"""
Backfill team_id in match data using teams.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from src.collectors.base import BaseScraper

ROOT = Path(__file__).resolve().parents[2]
MATCHES_DIR = ROOT / "data" / "matches"


class _Resolver(BaseScraper):
    def scrape(self):
        raise NotImplementedError


def _iter_match_files(only: List[str] | None):
    for comp_dir in sorted(MATCHES_DIR.iterdir()):
        if not comp_dir.is_dir():
            continue
        comp_id = comp_dir.name
        if only and comp_id not in only:
            continue
        for match_file in sorted(comp_dir.glob("*.json")):
            yield comp_id, match_file


def backfill_team_ids(only: List[str] | None = None, force: bool = False) -> None:
    resolver = _Resolver(update_team_master=False)
    updated_files = 0
    total_updates = 0

    for comp_id, match_file in _iter_match_files(only):
        try:
            with match_file.open("r", encoding="utf-8") as f:
                matches = json.load(f)
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ {match_file}: 読み込み失敗 ({exc})")
            continue

        if not isinstance(matches, list):
            continue

        changed = False
        for match in matches:
            if not isinstance(match, dict):
                continue

            home_team = match.get("home_team", "")
            away_team = match.get("away_team", "")

            if force or not match.get("home_team_id"):
                match["home_team_id"] = resolver._resolve_team_id(home_team, comp_id)
                if match["home_team_id"]:
                    changed = True
                    total_updates += 1

            if force or not match.get("away_team_id"):
                match["away_team_id"] = resolver._resolve_team_id(away_team, comp_id)
                if match["away_team_id"]:
                    changed = True
                    total_updates += 1

        if changed:
            with match_file.open("w", encoding="utf-8") as f:
                json.dump(matches, f, ensure_ascii=False, indent=2)
                f.write("\n")
            updated_files += 1

    print(f"✅ Backfill 完了: 更新ファイル {updated_files} / team_id更新 {total_updates}")


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Backfill team_id fields in match data using teams.json.")
    parser.add_argument(
        "--only",
        type=str,
        default="",
        help="Comma-separated competition IDs to update (e.g., premier,urc,m6n).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing team_id values.",
    )
    args = parser.parse_args(argv)

    only = [s.strip() for s in args.only.split(",") if s.strip()] if args.only else None
    backfill_team_ids(only, args.force)


if __name__ == "__main__":
    main()
