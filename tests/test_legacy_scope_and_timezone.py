"""Invented clock/metadata fixtures. No collector or current official source is fetched."""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup

from src.collectors.european.top14 import Top14Scraper
from src.collectors.international.six_nations import SixNationsScraper
from src.repositories.competition_repository import build_competitions, effective_collection_coverage
from src.services.fixture_publication import VALIDATION_VERSION, file_sha256, write_json_atomic


class Fixed2027Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        value = datetime(2027, 10, 6, tzinfo=timezone.utc)
        return value.astimezone(tz) if tz else value.replace(tzinfo=None)


class Fixed2026Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        value = datetime(2026, 10, 6, tzinfo=timezone.utc)
        return value.astimezone(tz) if tz else value.replace(tzinfo=None)


class SixNationsFallbackTests(unittest.TestCase):
    @patch("src.collectors.international.six_nations.datetime", Fixed2027Clock)
    def test_display_fallback_retains_london_instant_for_france_italy_and_dst(self):
        scraper = SixNationsScraper()
        cases = [
            ("5 February", "20:10", "2027-02-05T20:10:00Z"),
            ("11 April", "20:10", "2027-04-11T19:10:00Z"),
            ("28 March", "00:30", "2027-03-28T00:30:00Z"),
            ("28 March", "02:30", "2027-03-28T01:30:00Z"),
            ("31 October", "00:30", "2027-10-30T23:30:00Z"),
            ("31 October", "02:30", "2027-10-31T02:30:00Z"),
        ]
        for home, zone in (("FRA", "Europe/Paris"), ("ITA", "Europe/Rome")):
            for current_date, clock, expected in cases:
                with self.subTest(home=home, date=current_date, clock=clock):
                    card = BeautifulSoup(f'''<article><div class="fixturesResultsCard_status">{clock}</div>
                      <span class="fixturesResultsCard_teamName">{home}</span><span class="fixturesResultsCard_teamName">IRE</span>
                      <a class="fixturesResultsCard_cardLink" href="/en/m6n/fixtures/202700/home-v-ireland/build-up"></a></article>''', "html.parser").article
                    match = scraper._extract_match_info(card, current_date)
                    self.assertEqual(expected, match["kickoff_utc"])
                    self.assertEqual(zone, match["timezone"])
                    self.assertEqual(datetime.fromisoformat(expected.replace("Z", "+00:00")), datetime.fromisoformat(match["kickoff"]).astimezone(timezone.utc))

    @patch("src.collectors.international.six_nations.datetime", Fixed2027Clock)
    def test_url_venue_clock_still_precedes_display_fallback(self):
        for home in ("FRA", "ITA"):
            with self.subTest(home=home):
                card = BeautifulSoup(f'''<article><div class="fixturesResultsCard_status">20:10</div>
                  <span class="fixturesResultsCard_teamName">{home}</span><span class="fixturesResultsCard_teamName">IRE</span>
                  <a class="fixturesResultsCard_cardLink" href="/en/m6n/fixtures/202700/home-v-ireland-05022027-2110/build-up"></a></article>''', "html.parser").article
                match = SixNationsScraper()._extract_match_info(card, "5 February")
                self.assertEqual("2027-02-05T20:10:00Z", match["kickoff_utc"])


@patch("src.repositories.competition_repository.datetime", Fixed2026Clock)
class LegacyScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = Path(self.tmp.name)
        scraper = Top14Scraper()
        self.path = self.data / "matches/t14/2026-2027.json"
        match = scraper.build_match(competition_id="t14", season="2026-2027", kickoff="2026-10-03T12:30:00Z", timezone_name="UTC", venue="Invented stadium", home_team="Home", away_team="Away", match_id="11848", match_url="https://top14.lnr.fr/feuille-de-match/2026-2027/j5/11848-home-away")
        write_json_atomic(self.path, scraper.assign_match_ids([match]))
        self.health = {"sources": {"t14": {"outcome": "success", "last_success_at": "2026-10-02T00:00:00Z", "last_attempt_at": "2026-10-02T00:00:00Z"}}, "files": {"data/matches/t14/2026-2027.json": {"sha256": file_sha256(self.path), "validation_version": VALIDATION_VERSION, "validated_at": "2026-10-02T00:00:00Z"}}}
        write_json_atomic(self.data / "source_health.json", self.health)
        write_json_atomic(self.data / "competitions_base.json", [{"id": "t14", "name": "TOP14"}])

    def test_metadata_annotates_retained_scope_without_recollection_or_byte_changes(self):
        before = self.path.read_bytes()
        health_before = (self.data / "source_health.json").read_bytes()
        _, manifest = build_competitions(self.data)
        entry = manifest["competitions"][0]
        self.assertEqual("partial", entry["status"])
        self.assertEqual("observed_rounds", entry["collection_coverage"]["scope"])
        self.assertFalse(entry["collection_coverage"]["complete"])
        self.assertEqual(1, entry["collection_coverage"]["included_match_count"])
        self.assertNotIn("observed_match_count", entry["collection_coverage"])
        self.assertEqual("2026-10-02T00:00:00Z", entry["last_success_at"])
        self.assertEqual("2026-10-02T00:00:00Z", entry["last_attempt_at"])
        self.assertEqual("2026-10-02T00:00:00Z", entry["files"][0]["validated_at"])
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(health_before, (self.data / "source_health.json").read_bytes())

    def test_stale_and_unavailable_take_priority_over_limited_scope(self):
        self.health["sources"]["t14"].update(outcome="failed", error="Source process exited with status 1")
        write_json_atomic(self.data / "source_health.json", self.health)
        _, manifest = build_competitions(self.data)
        self.assertEqual("stale", manifest["competitions"][0]["status"])
        self.assertEqual("Source process exited with status 1", manifest["competitions"][0]["error"])
        self.health["files"] = {}
        write_json_atomic(self.data / "source_health.json", self.health)
        _, manifest = build_competitions(self.data)
        self.assertEqual("unavailable", manifest["competitions"][0]["status"])
        self.assertEqual({}, manifest["competitions"][0]["collection_coverage"])

    def test_reviewed_paths_only_and_explicit_scope_declarations_are_preserved(self):
        result = effective_collection_coverage("srp", ["data/matches/srp/2026.json"], 77, {})
        self.assertEqual("regular_season", result["scope"])
        self.assertEqual(77, result["included_match_count"])
        self.assertFalse(result["complete"])
        for comp, path in (("srp", "data/matches/srp/2028.json"), ("t14", "data/matches/t14/2027-2028.json"), ("urc", "data/matches/urc/2026.json")):
            self.assertEqual({}, effective_collection_coverage(comp, [path], 77, {}))
        declared = {"scope": "full_season", "complete": True, "included_match_count": 84}
        self.assertEqual(declared, effective_collection_coverage("srp", ["data/matches/srp/2026.json"], 84, declared))


if __name__ == "__main__":
    unittest.main()
