"""Enrich match JSON files with IDs from masters.

- Fills competition_id using filename (slug) if empty
- Fills team IDs from data/teams.json (keyed by id)
- Generates stable match_id if missing

Usage:
  python scripts/enrich_matches.py --matches data/matches --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
MATCHES_DIR = ROOT / "data" / "matches"
COMPETITIONS_JSON = ROOT / "data" / "competitions.json"
TEAMS_JSON = ROOT / "data" / "teams.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def compute_match_id(competition_id: str, kickoff_utc: str, home: str, away: str) -> str:
    base = f"{competition_id}|{kickoff_utc}|{home}|{away}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
    return f"{competition_id}-{kickoff_utc.lower()}-{home.lower()}-{away.lower()}-{digest}"


def enrich_file(path: Path, teams: Dict[str, Any], dry_run: bool) -> None:
    competition_id = path.stem
    matches: List[Dict[str, Any]] = load_json(path, default=[])
    changed = False

    for m in matches:
        # competition_id
        if not m.get("competition_id"):
            m["competition_id"] = competition_id
            changed = True

        # team IDs
        home = m.get("home_team") or ""
        away = m.get("away_team") or ""
        if home and not m.get("home_team_id"):
            key = home.lower()
            if key in teams:
                m["home_team_id"] = key
                changed = True
        if away and not m.get("away_team_id"):
            key = away.lower()
            if key in teams:
                m["away_team_id"] = key
                changed = True

        # match_id
        if not m.get("match_id") and m.get("kickoff_utc") and home and away:
            m["match_id"] = compute_match_id(competition_id, m["kickoff_utc"], home, away)
            changed = True

    if changed and not dry_run:
        write_json(path, matches)
    if changed:
        print(f"[updated] {path.relative_to(ROOT)}")
    else:
        print(f"[skip] {path.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich matches with IDs from masters.")
    parser.add_argument("--matches", default=str(MATCHES_DIR), help="Matches directory")
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes")
    args = parser.parse_args()

    matches_dir = Path(args.matches)
    teams = load_json(TEAMS_JSON, default={})
    if not teams:
        raise SystemExit("teams.json is missing or empty; please define team IDs first.")

    for path in sorted(matches_dir.glob("*.json")):
        enrich_file(path, teams, args.dry_run)


if __name__ == "__main__":
    main()
