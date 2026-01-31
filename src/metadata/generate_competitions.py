import json
from pathlib import Path
from datetime import datetime
from dateutil import parser as date_parser

BASE_COMPETITIONS = [
    {
        "id": "six-nations",
        "name": "Six Nations",
        "short_name": "6N",
        "sport": "rugby union",
        "category": "international",
        "gender": "men",
        "age_grade": "senior",
        "tier": "tier-1",
        "region": "Europe",
        "governing_body": "Six Nations Rugby",
        "organizer": "Six Nations Rugby",
        "official_sites": ["https://www.sixnationsrugby.com"],
        "official_feeds": [],
        "timezone_default": "Europe/London",
        "season_pattern": "annual",
        "match_url_template": "https://www.sixnationsrugby.com/en/m6n/fixtures/{season}/{slug}",
        "data_paths": ["data/matches/six-nations.json"],
    },
    {
        "id": "six-nations-women",
        "name": "Women's Six Nations",
        "short_name": "W6N",
        "sport": "rugby union",
        "category": "international",
        "gender": "women",
        "age_grade": "senior",
        "tier": "tier-1",
        "region": "Europe",
        "governing_body": "Six Nations Rugby",
        "organizer": "Six Nations Rugby",
        "official_sites": ["https://www.sixnationsrugby.com"],
        "official_feeds": [],
        "timezone_default": "Europe/London",
        "season_pattern": "annual",
        "match_url_template": "https://www.sixnationsrugby.com/en/w6n/fixtures/{season}/{slug}",
        "data_paths": ["data/matches/six-nations-women.json"],
    },
    {
        "id": "six-nations-u20",
        "name": "Six Nations U20",
        "short_name": "U20 6N",
        "sport": "rugby union",
        "category": "international",
        "gender": "men",
        "age_grade": "u20",
        "tier": "tier-1",
        "region": "Europe",
        "governing_body": "Six Nations Rugby",
        "organizer": "Six Nations Rugby",
        "official_sites": ["https://www.sixnationsrugby.com"],
        "official_feeds": [],
        "timezone_default": "Europe/London",
        "season_pattern": "annual",
        "match_url_template": "https://www.sixnationsrugby.com/en/u6n/u20-mens/fixtures/{season}/{slug}",
        "data_paths": ["data/matches/six-nations-u20.json"],
    },
    {
        "id": "epcr-champions",
        "name": "EPCR Champions Cup",
        "short_name": "Champions Cup",
        "sport": "rugby union",
        "category": "club",
        "gender": "men",
        "age_grade": "senior",
        "tier": "tier-1",
        "region": "Europe",
        "governing_body": "EPCR",
        "organizer": "EPCR",
        "official_sites": ["https://www.epcrugby.com"],
        "official_feeds": [],
        "timezone_default": "Europe/Paris",
        "season_pattern": "annual",
        "match_url_template": "https://www.epcrugby.com/champions-cup/matches/{matchId}",
        "data_paths": ["data/matches/epcr-champions.json"],
    },
    {
        "id": "epcr-challenge",
        "name": "EPCR Challenge Cup",
        "short_name": "Challenge Cup",
        "sport": "rugby union",
        "category": "club",
        "gender": "men",
        "age_grade": "senior",
        "tier": "tier-1",
        "region": "Europe",
        "governing_body": "EPCR",
        "organizer": "EPCR",
        "official_sites": ["https://www.epcrugby.com"],
        "official_feeds": [],
        "timezone_default": "Europe/Paris",
        "season_pattern": "annual",
        "match_url_template": "https://www.epcrugby.com/challenge-cup/matches/{matchId}",
        "data_paths": ["data/matches/epcr-challenge.json"],
    },
    {
        "id": "top14",
        "name": "Top 14",
        "short_name": "Top 14",
        "sport": "rugby union",
        "category": "club",
        "gender": "men",
        "age_grade": "senior",
        "tier": "tier-1",
        "region": "Europe",
        "governing_body": "LNR",
        "organizer": "LNR",
        "official_sites": ["https://top14.lnr.fr"],
        "official_feeds": [],
        "timezone_default": "Europe/Paris",
        "season_pattern": "annual",
        "match_url_template": "https://top14.lnr.fr/feuille-de-match/{matchId}",
        "data_paths": ["data/matches/top14.json"],
    },
    {
        "id": "league-one",
        "name": "Japan Rugby League One",
        "short_name": "League One",
        "sport": "rugby union",
        "category": "club",
        "gender": "men",
        "age_grade": "senior",
        "tier": "tier-1",
        "region": "Japan",
        "governing_body": "Japan Rugby League One",
        "organizer": "Japan Rugby League One",
        "official_sites": ["https://league-one.jp"],
        "official_feeds": [],
        "timezone_default": "Asia/Tokyo",
        "season_pattern": "annual",
        "match_url_template": "https://league-one.jp/match/{matchId}",
        "data_paths": ["data/matches/league-one.json"],
    },
    {
        "id": "gallagher-premiership",
        "name": "Gallagher Premiership",
        "short_name": "Premiership",
        "sport": "rugby union",
        "category": "club",
        "gender": "men",
        "age_grade": "senior",
        "tier": "tier-1",
        "region": "Europe",
        "governing_body": "Premiership Rugby",
        "organizer": "Premiership Rugby",
        "official_sites": ["https://www.premiershiprugby.com"],
        "official_feeds": ["https://rugby-union-feeds.incrowdsports.com"],
        "timezone_default": "Europe/London",
        "season_pattern": "annual",
        "match_url_template": "https://www.premiershiprugby.com/fixture/{matchId}",
        "data_paths": ["data/matches/gallagher-premiership.json"],
    },
    {
        "id": "urc",
        "name": "United Rugby Championship",
        "short_name": "URC",
        "sport": "rugby union",
        "category": "club",
        "gender": "men",
        "age_grade": "senior",
        "tier": "tier-1",
        "region": "Europe/Africa",
        "governing_body": "United Rugby Championship",
        "organizer": "URC",
        "official_sites": ["https://www.unitedrugby.com"],
        "official_feeds": ["https://rugby-union-feeds.incrowdsports.com"],
        "timezone_default": "Europe/London",
        "season_pattern": "annual",
        "match_url_template": "https://www.unitedrugby.com/match/{matchId}",
        "data_paths": ["data/matches/urc.json"],
    },
    {
        "id": "super-rugby-pacific",
        "name": "Super Rugby Pacific",
        "short_name": "SRP",
        "sport": "rugby union",
        "category": "club",
        "gender": "men",
        "age_grade": "senior",
        "tier": "tier-1",
        "region": "Oceania",
        "governing_body": "SANZAAR",
        "organizer": "Super Rugby",
        "official_sites": ["https://www.super.rugby"],
        "official_feeds": ["https://super.rugby/superrugby/documents/media-files/"],
        "timezone_default": "Pacific/Auckland",
        "season_pattern": "annual",
        "match_url_template": "https://www.super.rugby/superrugby/match-centre/{matchId}",
        "data_paths": ["data/matches/super-rugby-pacific.json"],
    },
    {
        "id": "world-rugby-internationals",
        "name": "World Rugby Internationals",
        "short_name": "WR Internationals",
        "sport": "rugby union",
        "category": "international",
        "gender": "mixed",
        "age_grade": "senior",
        "tier": "tier-1",
        "region": "global",
        "governing_body": "World Rugby",
        "organizer": "World Rugby",
        "official_sites": ["https://www.world.rugby"],
        "official_feeds": ["https://api.wr-rims-prod.pulselive.com"],
        "timezone_default": "UTC",
        "season_pattern": "annual",
        "match_url_template": "https://www.world.rugby/match/{matchId}",
        "data_paths": ["data/matches/world-rugby-internationals.json"],
    },
]


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


def build_competitions():
    competitions = []
    for base in BASE_COMPETITIONS:
        teams = set()
        seasons = set()
        dates = []
        match_count = 0
        last_updated = None

        for rel_path in base.get("data_paths", []):
            path = Path(rel_path)
            matches = load_matches(path)
            if not isinstance(matches, list):
                continue

            match_count += len(matches)
            for match in matches:
                if not isinstance(match, dict):
                    continue
                if match.get("home_team"):
                    teams.add(match.get("home_team"))
                if match.get("away_team"):
                    teams.add(match.get("away_team"))
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

        competition = {
            **base,
            "coverage": {
                "broadcast_regions": [],
                "analysis_providers": [],
            },
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
    output_path = Path("data/competitions.json")
    competitions = build_competitions()
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(competitions, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
