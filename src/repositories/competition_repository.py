import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from src.services.fixture_publication import (
    load_json, write_json_atomic, file_sha256, is_verified_file,
    validate_match_file, utc_now,
)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
BASE_JSON = DATA_DIR / "competitions_base.json"


GLOBAL_ANALYSIS_PROVIDERS = [
    {
        "name": "ESPN Rugby",
        "official_source": "https://www.espn.com/rugby/",
    },
    {
        "name": "RugbyPass",
        "official_source": "https://www.rugbypass.com/",
    },
    {
        "name": "RugbyPass TV",
        "official_source": "https://info.rugbypass.tv/",
    },
]

PLACEHOLDER_TEAM_TOKENS = [
    "リーグ戦",
    "準々決勝",
    "準決勝",
    "決勝",
]
PLACEHOLDER_TEAM_EXACT = {"TBC", "TBD", "TBA", "-"}


def load_base_competitions():
    if not BASE_JSON.exists():
        raise FileNotFoundError(f"competitions_base.json not found: {BASE_JSON}")
    with BASE_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)



def load_matches(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def parse_datetime(value):
    if not value:
        return None
    try:
        return date_parser.parse(value)
    except (ValueError, TypeError):
        return None


def is_placeholder_team(team_name: str) -> bool:
    if not team_name:
        return False
    value = team_name.strip()
    if not value:
        return False
    if value.upper() in PLACEHOLDER_TEAM_EXACT:
        return True
    return any(token in value for token in PLACEHOLDER_TEAM_TOKENS)


def build_competitions(data_dir=DATA_DIR):
    """Build the manifest and both backwards-compatible metadata arrays.

    Paths come from actual files. Only hashes validated by the transactional
    runner are exposed in data_paths; filesystem mtimes never imply freshness.
    """
    data_dir = Path(data_dir)
    bases = load_json(data_dir / "competitions_base.json", [])
    masters = {c["id"]: c for c in load_json(data_dir / "competitions.json", [])}
    health = load_json(data_dir / "source_health.json", {"sources": {}, "files": {}})
    competitions = []
    manifest_competitions = []
    for template in bases:
        base = {**template, **masters.get(template["id"], {})}
        comp_id = base["id"]
        teams = set()
        seasons = set()
        dates = []
        match_count = 0
        unknown = 0
        files = []
        data_paths = []
        for path in sorted((data_dir / "matches" / comp_id).glob("*.json")):
            relative = "data/" + path.relative_to(data_dir).as_posix()
            file_info = {"path": relative, "season": path.stem, "sha256": file_sha256(path),
                         "match_count": 0, "known_kickoffs": 0, "unknown_kickoffs": 0,
                         "trust": "unverified", "validated_at": "", "error": "Awaiting collection with the corrected date parser"}
            try:
                summary = validate_match_file(path, comp_id)
                file_info.update({k: summary[k] for k in ("match_count", "known_kickoffs", "unknown_kickoffs")})
                if is_verified_file(path, health, data_dir):
                    record = health["files"][relative]
                    file_info.update(trust="verified", validated_at=record["validated_at"], error="")
                    data_paths.append(relative)
                    seasons.add(path.stem)
                    match_count += summary["match_count"]
                    unknown += summary["unknown_kickoffs"]
                    dates += [date for date in (summary["date_range"]["start"], summary["date_range"]["end"]) if date]
                    for match in load_json(path, []):
                        for field in ("home_team", "away_team"):
                            if match.get(field) and not is_placeholder_team(match[field]):
                                teams.add(match[field])
            except (OSError, ValueError, TypeError, KeyError) as error:
                file_info.update(trust="invalid", error=str(error))
            files.append(file_info)

        date_range = None
        if dates:
            dates_sorted = sorted(dates)
            date_range = {
                "start": dates_sorted[0],
                "end": dates_sorted[-1],
            }

        coverage = base.get("coverage") or {
            "broadcast_regions": [],
            "analysis_providers": [],
        }
        if not coverage.get("analysis_providers"):
            coverage = {
                **coverage,
                "analysis_providers": [
                    dict(provider) for provider in GLOBAL_ANALYSIS_PROVIDERS
                ],
            }

        competition = {
            **base,
            "data_paths": data_paths,
            "coverage": coverage,
            "teams": sorted(teams),
            "data_summary": {
                "match_count": match_count,
                "seasons": sorted(seasons),
                "date_range": date_range or {"start": "", "end": ""},
                "last_updated": health.get("sources", {}).get(comp_id, {}).get("last_success_at", ""),
            },
        }
        competitions.append(competition)
        source_health = health.get("sources", {}).get(comp_id, {})
        last_success = source_health.get("last_success_at", "")
        status = "healthy"
        if not data_paths:
            status = "unavailable"
        elif source_health.get("outcome") in ("failed", "no_fixtures") or not last_success:
            status = "stale"
        elif datetime.now(timezone.utc) - date_parser.isoparse(last_success) > timedelta(days=14):
            status = "stale"
        elif unknown or source_health.get("collection_coverage", {}).get("date_unannounced_count", 0) or any(f["trust"] != "verified" for f in files):
            status = "partial"
        manifest_competitions.append({
            "id": comp_id, "name": base.get("name", comp_id),
            "data_paths": data_paths, "seasons": sorted(seasons), "status": status,
            "last_success_at": last_success,
            "last_attempt_at": source_health.get("last_attempt_at", ""),
            "error": source_health.get("error", "") or ("No verified fixture files available" if not data_paths else ""),
            "coverage": {"match_count": match_count, "known_kickoffs": match_count - unknown,
                         "unknown_kickoffs": unknown, "date_range": date_range or {"start": "", "end": ""}},
            "collection_coverage": source_health.get("collection_coverage", {}),
            "files": files,
        })
    return competitions, {"schema_version": 1, "generated_at": utc_now(), "competitions": manifest_competitions}


def main(data_dir=DATA_DIR):
    data_dir = Path(data_dir)
    competitions, manifest = build_competitions(data_dir)
    write_json_atomic(data_dir / "competitions_summary.json", competitions)
    write_json_atomic(data_dir / "competitions.json", competitions)
    write_json_atomic(data_dir / "manifest.json", manifest)


if __name__ == "__main__":
    main()
