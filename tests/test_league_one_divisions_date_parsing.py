import unittest
from datetime import datetime

from src.collectors.domestic.league_one_divisions import LeagueOneDivisionsScraper


class FixedNowLeagueOneDivisionsScraper(LeagueOneDivisionsScraper):
    def _now(self):
        return datetime(2026, 3, 1, 9, 0, tzinfo=self.jst)


class LeagueOneDivisionsDateParsingTests(unittest.TestCase):
    def setUp(self):
        self.scraper = FixedNowLeagueOneDivisionsScraper()

    def test_parse_march_first(self):
        kickoff = self.scraper.parse_kickoff_datetime(
            "03.01 日 12:10", "https://league-one.jp/match/29312"
        )
        self.assertEqual("2026-03-01T12:10:00+09:00", kickoff.isoformat())

    def test_parse_december_uses_previous_year(self):
        kickoff = self.scraper.parse_kickoff_datetime(
            "12.13 土 13:00", "https://league-one.jp/match/29260"
        )
        self.assertEqual("2025-12-13T13:00:00+09:00", kickoff.isoformat())

    def test_ambiguous_month_day_not_swapped(self):
        kickoff_a = self.scraper.parse_kickoff_datetime("04.06 日 14:30", "match-a")
        kickoff_b = self.scraper.parse_kickoff_datetime("06.04 日 14:30", "match-b")
        self.assertEqual((4, 6), (kickoff_a.month, kickoff_a.day))
        self.assertEqual((6, 4), (kickoff_b.month, kickoff_b.day))

    def test_invalid_format_returns_none(self):
        kickoff = self.scraper.parse_kickoff_datetime(
            "invalid", "https://league-one.jp/match/xxxx"
        )
        self.assertIsNone(kickoff)


if __name__ == "__main__":
    unittest.main()
