#!/usr/bin/env python3
"""Collect in isolation, retain failures, and report CI failures after publishing.

Normal partial runs return zero so metadata/data publication can proceed.
--check-report is the separate post-publication CI signal for source failures.
"""
import argparse
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.services.fixture_publication import (
    VALIDATION_VERSION, file_sha256, load_json, utc_now,
    validate_match_file, write_json_atomic,
)

COMPETITIONS = [
    ("wr", "World Rugby Internationals"),
    ("premier", "Gallagher Premiership"),
    ("urc", "United Rugby Championship"),
    ("trc", "The Rugby Championship"),
    ("ans", "Autumn Nations Series"),
    ("nc", "Nations Championship"),
    ("srp", "Super Rugby Pacific"),
    ("epcr-champions", "EPCR Champions Cup"),
    ("epcr-challenge", "EPCR Challenge Cup"),
    ("t14", "Top 14"),
    ("jrlo", "Japan Rugby League One"),
    ("m6n", "Six Nations"),
    ("w6n", "Women's Six Nations"),
    ("u6n", "U20 Six Nations"),
]


def competition_ids(source):
    return ["jrlo-div1", "jrlo-div2", "jrlo-div3"] if source == "jrlo" else [source]


def source_files(data_dir, source):
    return sorted(path for comp in competition_ids(source)
                  for path in (data_dir / "matches" / comp).glob("*.json"))


def run_subprocess(command, *, cwd, env, timeout):
    # Kill the source's browser children too when the source budget expires.
    process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def collect_source(source, data_dir, health, *, timeout=300, run=run_subprocess):
    attempted = utc_now()
    ids = competition_ids(source)
    error = ""
    outcome = "failed"
    promoted = []
    try:
        with tempfile.TemporaryDirectory(prefix="rugby-source-") as temporary:
            staging = Path(temporary) / "data"
            shutil.copytree(data_dir, staging)
            before = {p.relative_to(staging): p.stat().st_mtime_ns for p in source_files(staging, source)}
            env = {**os.environ, "RUGBY_DATA_DIR": str(staging)}
            result = run([sys.executable, "-m", "src.main", source], cwd=ROOT, env=env, timeout=timeout)
            if result.stdout:
                print(result.stdout)
            if result.returncode:
                if result.stderr:
                    print(result.stderr)
                raise ValueError(f"Source process exited with status {result.returncode}")
            touched = [p for p in source_files(staging, source)
                       if before.get(p.relative_to(staging)) != p.stat().st_mtime_ns]
            if not touched:
                outcome = "no_fixtures"
                error = "Source returned no fixture files; retained previous data"
            else:
                # Validate every candidate before changing any live source file.
                for path in touched:
                    summary = validate_match_file(path)
                    previous = data_dir / path.relative_to(staging)
                    if previous.exists():
                        old = load_json(previous, [])
                        old_known = sum(bool(m.get("kickoff_utc")) for m in old if isinstance(m, dict))
                        if old_known >= 10 and summary["known_kickoffs"] < old_known * 0.5:
                            raise ValueError(f"{path.name}: known kickoffs fell by more than 50%; manual source review required")
                    promoted.append((path, summary))
                replacements = []
                backups = {}
                for path, summary in promoted:
                    destination = data_dir / path.relative_to(staging)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    backups[destination] = destination.read_bytes() if destination.exists() else None
                    temporary_file = destination.with_suffix(".json.tmp")
                    shutil.copyfile(path, temporary_file)
                    replacements.append((temporary_file, destination, summary))
                changed = []
                try:
                    for temporary_file, destination, _ in replacements:
                        temporary_file.replace(destination)
                        changed.append(destination)
                except OSError:
                    # JRLO's three divisions are promoted as one source. Restore
                    # any earlier rename if a later destination cannot commit.
                    for destination in reversed(changed):
                        original = backups[destination]
                        if original is None:
                            destination.unlink()
                        else:
                            rollback = destination.with_suffix(".json.rollback")
                            rollback.write_bytes(original)
                            rollback.replace(destination)
                    raise
                for _, destination, summary in replacements:
                    relative = "data/" + destination.relative_to(data_dir).as_posix()
                    health.setdefault("files", {})[relative] = {
                        "sha256": file_sha256(destination), "validated_at": attempted,
                        "validation_version": VALIDATION_VERSION, "source": source,
                        "coverage": summary,
                    }
                outcome = "success"
    except subprocess.TimeoutExpired:
        error = f"Source exceeded its {timeout}-second fixture budget; retained previous data"
    except (OSError, ValueError, TypeError, KeyError) as exception:
        error = str(exception)
    previous_sources = health.setdefault("sources", {})
    for comp in ids:
        previous = previous_sources.get(comp, {})
        successful_file = any(p.parent.name == comp for p, _ in promoted) if outcome == "success" else False
        record = {**previous, "last_attempt_at": attempted,
                  "outcome": outcome if successful_file or outcome != "success" else "no_fixtures",
                  "error": error if outcome != "success" else ""}
        if successful_file:
            record["last_success_at"] = attempted
        elif outcome == "success":
            record["error"] = "No fixtures collected for this division; retained previous data"
        previous_sources[comp] = record
    print(f"{source}: {outcome}" + (f" — {error}" if error else ""))
    return {"source": source, "outcome": outcome, "error": error,
            "promoted_files": len(promoted) if outcome == "success" else 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--competition", choices=[c[0] for c in COMPETITIONS])
    parser.add_argument("--check-report", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args(argv)
    data_dir = ROOT / "data"
    report_path = data_dir / "scrape_report.json"
    if args.check_report:
        report = load_json(report_path, {})
        return 1 if not report or report.get("failed_sources", 0) else 0
    health = load_json(data_dir / "source_health.json", {"schema_version": 1, "sources": {}, "files": {}})
    selected = [c for c in COMPETITIONS if not args.competition or c[0] == args.competition]
    results = []
    for source, name in selected:
        print(f"Collecting {name} ({source})")
        results.append(collect_source(source, data_dir, health, timeout=args.timeout))
        write_json_atomic(data_dir / "source_health.json", health)
    report = {"generated_at": utc_now(), "sources": results,
              "successful_sources": sum(r["outcome"] == "success" for r in results),
              "failed_sources": sum(r["outcome"] == "failed" for r in results),
              "empty_sources": sum(r["outcome"] == "no_fixtures" for r in results)}
    write_json_atomic(report_path, report)
    print(f"Validated sources: {report['successful_sources']}/{len(results)}; failed: {report['failed_sources']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
