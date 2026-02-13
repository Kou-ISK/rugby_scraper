import json
from pathlib import Path
from datetime import datetime
from dateutil import parser as date_parser

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


def build_competitions():
    competitions = []
    for base in load_base_competitions():
        teams = set()
        seasons = set()
        dates = []
        match_count = 0
        last_updated = None

        for rel_path in base.get("data_paths", []):
            base_path = Path(rel_path)
            if base_path.is_dir():
                match_paths = sorted(base_path.glob("*.json"))
            else:
                match_paths = [base_path]

            for path in match_paths:
                matches = load_matches(path)
                if not isinstance(matches, list):
                    continue

                match_count += len(matches)
                for match in matches:
                    if not isinstance(match, dict):
                        continue
                    home_team = match.get("home_team")
                    away_team = match.get("away_team")
                    if home_team and not is_placeholder_team(home_team):
                        teams.add(home_team)
                    if away_team and not is_placeholder_team(away_team):
                        teams.add(away_team)
                    if match.get("season"):
                        seasons.add(str(match.get("season")))

                    kickoff = match.get("kickoff") or match.get("kickoff_utc")
                    dt = parse_datetime(kickoff)
                    if dt:
                        dates.append(dt)

                if path.exists():
                    mtime = datetime.utcfromtimestamp(path.stat().st_mtime)
                    last_updated = max(last_updated, mtime) if last_updated else mtime

        date_range = None
        if dates:
            dates_sorted = sorted(dates)
            date_range = {
                "start": dates_sorted[0].isoformat(),
                "end": dates_sorted[-1].isoformat(),
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
            "coverage": coverage,
            "teams": sorted(teams),
            "data_summary": {
                "match_count": match_count,
                "seasons": sorted(seasons),
                "date_range": date_range or {"start": "", "end": ""},
                "last_updated": last_updated.isoformat() if last_updated else "",
            },
        }
        competitions.append(competition)

    return competitions


def main():
    output_path = Path("data/competitions_summary.json")
    competitions = build_competitions()
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(competitions, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
