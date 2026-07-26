from datetime import datetime, timezone

from src.collectors.international.nations_championship import (
    NationsChampionshipScraper,
)


def _raw_match(competition: str):
    return {
        "matchId": "world-rugby-match-id",
        "competition": competition,
        "eventPhase": "",
        "status": "U",
        "time": {
            "millis": int(
                datetime(2026, 11, 7, 15, 0, tzinfo=timezone.utc).timestamp()
                * 1000
            ),
            "gmtOffset": 0,
        },
        "teams": [{"name": "England"}, {"name": "Australia"}],
        "venue": {"name": "Allianz Stadium"},
    }


def test_normalizes_nations_championship_in_standard_match_format():
    scraper = NationsChampionshipScraper()

    matches = scraper.assign_match_ids(
        scraper._normalize_matches([_raw_match("Nations Championship 2026")])
    )

    assert len(matches) == 1
    assert matches[0] == {
        "match_id": "nc-2026-1",
        "competition_id": "nc",
        "season": "2026",
        "round": "",
        "status": "U",
        "kickoff": "2026-11-07T15:00:00+00:00",
        "kickoff_utc": "2026-11-07T15:00:00Z",
        "timezone": "UTC+00:00",
        "venue": "Allianz Stadium",
        "home_team": "England",
        "away_team": "Australia",
        "home_team_id": "",
        "away_team_id": "",
        "match_url": "https://www.world.rugby/match/world-rugby-match-id",
        "broadcasters": [],
    }


def test_does_not_include_world_rugby_nations_cup():
    scraper = NationsChampionshipScraper()

    matches = scraper._normalize_matches(
        [
            _raw_match("Nations Championship 2026"),
            _raw_match("World Rugby Nations Cup 2026"),
        ]
    )

    assert len(matches) == 1
    assert matches[0]["competition_id"] == "nc"
