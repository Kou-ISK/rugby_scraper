import json
from pathlib import Path
from datetime import datetime
from dateutil import parser as date_parser


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

BASE_COMPETITIONS = [
    {
        "id": "m6n",
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
        "data_paths": ["data/matches/m6n"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "JP",
                    "providers": ["WOWOW"],
                    "official_source": "https://www.sixnationsrugby.com/en/m6n/where-to-watch-guinness-six-nations",
                },
                {
                    "region": "UK",
                    "providers": ["ITV", "BBC", "Premier Sports"],
                    "official_source": "https://www.sixnationsrugby.com/en/m6n/where-to-watch-guinness-six-nations",
                },
                {
                    "region": "IE",
                    "providers": ["RTÉ", "Virgin Media", "Premier Sports"],
                    "official_source": "https://www.sixnationsrugby.com/en/m6n/where-to-watch-guinness-six-nations",
                },
                {
                    "region": "AU",
                    "providers": ["Stan Sport"],
                    "official_source": "https://www.sixnationsrugby.com/en/m6n/where-to-watch-guinness-six-nations",
                },
                {
                    "region": "NZ",
                    "providers": ["Sky"],
                    "official_source": "https://www.sixnationsrugby.com/en/m6n/where-to-watch-guinness-six-nations",
                },
            ],
            "analysis_providers": [],
            "notes": "Regional availability varies. Some streaming services require geo-location within their service area or VPN for international access.",
        },
    },
    {
        "id": "w6n",
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
        "data_paths": ["data/matches/w6n"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "UK",
                    "providers": ["BBC"],
                    "official_source": "https://www.sixnationsrugby.com/en/w6n/where-to-watch",
                },
            ],
            "analysis_providers": [],
            "notes": "Coverage may be available via Six Nations official channels and regional broadcasters.",
        },
    },
    {
        "id": "u6n",
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
        "data_paths": ["data/matches/u6n"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "UK/IE",
                    "providers": ["Six Nations YouTube"],
                    "official_source": "https://www.sixnationsrugby.com",
                },
            ],
            "analysis_providers": [],
            "notes": "Many matches available via Six Nations official streaming channels.",
        },
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
        "data_paths": ["data/matches/epcr-champions"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "UK/IE",
                    "providers": ["Premier Sports", "TNT Sports"],
                    "official_source": "https://www.epcrugby.com",
                },
                {
                    "region": "FR",
                    "providers": ["beIN Sports"],
                    "official_source": "https://www.epcrugby.com",
                },
            ],
            "analysis_providers": [],
            "notes": "Broadcasting rights vary by region. Check EPCR official site for regional availability.",
        },
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
        "data_paths": ["data/matches/epcr-challenge"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "UK/IE",
                    "providers": ["Premier Sports"],
                    "official_source": "https://www.epcrugby.com",
                },
                {
                    "region": "FR",
                    "providers": ["beIN Sports"],
                    "official_source": "https://www.epcrugby.com",
                },
            ],
            "analysis_providers": [],
            "notes": "Broadcasting rights vary by region. Check EPCR official site for regional availability.",
        },
    },
    {
        "id": "t14",
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
        "data_paths": ["data/matches/t14"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "FR",
                    "providers": ["Canal+"],
                    "official_source": "https://top14.lnr.fr",
                },
                {
                    "region": "International",
                    "providers": ["RugbyPass TV"],
                    "official_source": "https://info.rugbypass.tv",
                },
            ],
            "analysis_providers": [],
            "notes": "Canal+ holds exclusive French broadcasting rights. International viewers may require RugbyPass TV subscription.",
        },
    },
    {
        "id": "jrlo-div1",
        "name": "Japan Rugby League One Division 1",
        "short_name": "JRLO D1",
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
        "data_paths": ["data/matches/jrlo-div1"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "JP",
                    "providers": ["J SPORTS", "J SPORTSオンデマンド", "Lemino (selected matches)"],
                    "official_source": "https://league-one.jp/news/3842",
                }
            ],
            "analysis_providers": [],
            "notes": "J SPORTS provides comprehensive coverage in Japan. International access is limited.",
        },
    },
    {
        "id": "jrlo-div2",
        "name": "Japan Rugby League One Division 2",
        "short_name": "JRLO D2",
        "sport": "rugby union",
        "category": "club",
        "gender": "men",
        "age_grade": "senior",
        "tier": "tier-2",
        "region": "Japan",
        "governing_body": "Japan Rugby League One",
        "organizer": "Japan Rugby League One",
        "official_sites": ["https://league-one.jp"],
        "official_feeds": [],
        "timezone_default": "Asia/Tokyo",
        "season_pattern": "annual",
        "match_url_template": "https://league-one.jp/match/{matchId}",
        "data_paths": ["data/matches/jrlo-div2"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "JP",
                    "providers": ["J SPORTS", "J SPORTSオンデマンド", "Lemino (selected matches)"],
                    "official_source": "https://league-one.jp/news/3842",
                }
            ],
            "analysis_providers": [],
            "notes": "J SPORTS provides comprehensive coverage in Japan. International access is limited.",
        },
    },
    {
        "id": "jrlo-div3",
        "name": "Japan Rugby League One Division 3",
        "short_name": "JRLO D3",
        "sport": "rugby union",
        "category": "club",
        "gender": "men",
        "age_grade": "senior",
        "tier": "tier-3",
        "region": "Japan",
        "governing_body": "Japan Rugby League One",
        "organizer": "Japan Rugby League One",
        "official_sites": ["https://league-one.jp"],
        "official_feeds": [],
        "timezone_default": "Asia/Tokyo",
        "season_pattern": "annual",
        "match_url_template": "https://league-one.jp/match/{matchId}",
        "data_paths": ["data/matches/jrlo-div3"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "JP",
                    "providers": ["J SPORTS", "J SPORTSオンデマンド", "Lemino (selected matches)"],
                    "official_source": "https://league-one.jp/news/3842",
                }
            ],
            "analysis_providers": [],
            "notes": "J SPORTS provides comprehensive coverage in Japan. International access is limited.",
        },
    },
    {
        "id": "premier",
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
        "data_paths": ["data/matches/premier"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "UK/IE",
                    "providers": ["TNT Sports", "discovery+"],
                    "official_source": "https://www.tntsports.co.uk/rugby/premiership/2023-2024/tnt-sports-and-discovery-renew-deal-with-gallagher-premiership-rugby-to-remain-home-of-english-club_sto10068404/story.shtml",
                }
            ],
            "analysis_providers": [],
            "notes": "TNT Sports and discovery+ hold exclusive UK/IE broadcasting rights. International access may require VPN.",
        },
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
        "data_paths": ["data/matches/urc"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "UK/IE",
                    "providers": ["Premier Sports", "BBC (selected matches)"],
                    "official_source": "https://www.unitedrugby.com",
                },
                {
                    "region": "ZA",
                    "providers": ["SuperSport"],
                    "official_source": "https://www.unitedrugby.com",
                },
                {
                    "region": "International",
                    "providers": ["URC TV"],
                    "official_source": "https://www.unitedrugby.com/urc-tv",
                },
            ],
            "analysis_providers": [],
            "notes": "URC TV offers global streaming (geo-restrictions apply). Regional broadcasters vary by team location.",
        },
    },
    {
        "id": "srp",
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
        "data_paths": ["data/matches/srp"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "NZ",
                    "providers": ["Sky Sport NZ"],
                    "official_source": "https://www.super.rugby",
                },
                {
                    "region": "AU",
                    "providers": ["Stan Sport"],
                    "official_source": "https://www.super.rugby",
                },
                {
                    "region": "JP",
                    "providers": ["J SPORTS"],
                    "official_source": "https://www.super.rugby",
                },
            ],
            "analysis_providers": [],
            "notes": "Broadcasting rights are region-specific. International access may require regional subscriptions or VPN.",
        },
    },
    {
        "id": "trc",
        "name": "The Rugby Championship",
        "short_name": "TRC",
        "sport": "rugby union",
        "category": "international",
        "gender": "men",
        "age_grade": "senior",
        "tier": "tier-1",
        "region": "Oceania/Americas/Africa",
        "governing_body": "SANZAAR",
        "organizer": "SANZAAR",
        "official_sites": ["https://www.therugbychampionship.com"],
        "official_feeds": [],
        "timezone_default": "UTC",
        "season_pattern": "variable",
        "match_url_template": "",
        "data_paths": ["data/matches/trc"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "JP",
                    "providers": ["WOWOW"],
                    "official_source": "https://news.wowow.co.jp/2344.html",
                },
                {
                    "region": "Select countries (no local broadcaster)",
                    "providers": ["NZR+"],
                    "official_source": "https://www.allblacks.com/all-blacks-live-rugby-championship",
                },
            ],
            "analysis_providers": [],
            "notes": "NZR+ available in select markets without local broadcasters. Check regional broadcaster availability before subscribing to OTT services.",
        },
    },
    {
        "id": "ans",
        "name": "Autumn Nations Series",
        "short_name": "ANS",
        "sport": "rugby union",
        "category": "international",
        "gender": "men",
        "age_grade": "senior",
        "tier": "tier-1",
        "region": "Europe",
        "governing_body": "Six Nations Rugby",
        "organizer": "Six Nations Rugby",
        "official_sites": ["https://autumnnationsseries.com"],
        "official_feeds": [],
        "timezone_default": "Europe/London",
        "season_pattern": "annual",
        "match_url_template": "",
        "data_paths": ["data/matches/ans"],
        "coverage": {
            "broadcast_regions": [
                {
                    "region": "JP",
                    "providers": ["WOWOW"],
                    "official_source": "https://news.wowow.co.jp/2425.html",
                },
                {
                    "region": "UK/IE",
                    "providers": ["TNT Sports", "discovery+"],
                    "official_source": "https://www.tntsports.co.uk/rugby/tnt-sports-discovery-exclusively-broadcast-2025-quilter-nations-series-all-22-fixtures-announced_sto20080891/story.shtml",
                },
                {
                    "region": "AU",
                    "providers": ["Stan Sport"],
                    "official_source": "https://www.stan.com.au/watch/sport/rugby/autumn-nations-series",
                },
            ],
            "analysis_providers": [],
            "notes": "Regional geo-restrictions apply to streaming services. VPN may be required for international access outside official broadcast regions.",
        },
    },
    {
        "id": "wr",
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
        "data_paths": ["data/matches/wr"],
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
