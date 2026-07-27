import unittest
from datetime import datetime
from unittest.mock import Mock, patch

import requests

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

    def test_fetches_print_details_only_within_lookback_window(self):
        recent = datetime(2026, 2, 20, 9, 0, tzinfo=self.scraper.jst)
        old = datetime(2026, 2, 14, 8, 59, tzinfo=self.scraper.jst)
        future = datetime(2026, 3, 2, 9, 0, tzinfo=self.scraper.jst)

        self.assertTrue(self.scraper._should_fetch_print_match_details(recent))
        self.assertFalse(self.scraper._should_fetch_print_match_details(old))
        self.assertFalse(self.scraper._should_fetch_print_match_details(future))

    @patch("src.collectors.domestic.league_one_divisions.time.sleep")
    @patch("src.collectors.domestic.league_one_divisions.requests.get")
    def test_schedule_page_retries_transient_connection_failure(
        self, get_mock, sleep_mock
    ):
        successful_response = Mock(status_code=200)
        get_mock.side_effect = [
            requests.ConnectTimeout("temporary timeout"),
            successful_response,
        ]

        response = self.scraper._fetch_schedule_page(
            "https://league-one.jp/schedule/", {"User-Agent": "test"}
        )

        self.assertIs(successful_response, response)
        self.assertEqual(2, get_mock.call_count)
        sleep_mock.assert_called_once_with(1)
        self.assertEqual((10, 30), get_mock.call_args.kwargs["timeout"])


if __name__ == "__main__":
    unittest.main()
