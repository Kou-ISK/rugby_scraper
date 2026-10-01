import copy
import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup

from scripts.automation.scrape_all import collect_source
from src.collectors.domestic.league_one_divisions import LeagueOneDivisionsScraper
from src.collectors.european.rugbyviz import UnitedRugbyChampionshipScraper
from src.collectors.european.top14 import Top14Scraper
from src.collectors.european.epcr import EPCRChampionsCupScraper
from src.collectors.international.rugby_championship import RugbyChampionshipScraper
from src.collectors.international.nations_championship import NationsChampionshipScraper
from src.repositories.competition_repository import build_competitions
from src.services.fixture_publication import (
    VALIDATION_VERSION, file_sha256, utc_now, validate_match_file, write_json_atomic,
)


def fixture(comp="urc", season="2026", source_id="official-fixture-test-1", kickoff="2026-10-02T18:45:00Z"):
    scraper = UnitedRugbyChampionshipScraper()
    match = scraper.build_match(
        competition_id=comp, season=season, kickoff=kickoff, timezone_name="UTC",
        venue="Cardiff Arms Park", home_team="Cardiff Rugby", away_team="Zebre Parma",
        match_url="", match_id=source_id,
    )
    return scraper.assign_match_ids([match])[0]


class DatetimeReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.scraper = UnitedRugbyChampionshipScraper()

    def test_every_ambiguous_iso_month_day_stays_in_original_order(self):
        for month in range(1, 13):
            for day in range(1, 13):
                value = f"2026-{month:02}-{day:02}T18:45:00Z"
                with self.subTest(value=value):
                    self.assertEqual(value, self.scraper._normalize_datetime(value, "UTC")[1])

    def test_cardiff_official_fixture_golden(self):
        # Independent club fixture reference, checked 2026-10-01:
        # https://www.cardiffrugby.wales/fixtures/
        # https://www.cardiffrugby.wales/news/cardiff-make-four-changes-for-zebre-with-mcnally-captain/
        # Fri 2 October 2026, 19:45 BST = 18:45 UTC. This is a normalization
        # golden, not an assertion that this synthetic record was fetched live.
        local, utc, _ = self.scraper._normalize_datetime("2026-10-02 19:45:00", "Europe/London")
        self.assertEqual("2026-10-02T19:45:00+01:00", local)
        self.assertEqual("2026-10-02T18:45:00Z", utc)

    def test_dst_and_year_boundary_offsets(self):
        cases = [
            ("2026-03-28T19:45:00", "Europe/London", "2026-03-28T19:45:00Z"),
            ("2026-03-29T19:45:00", "Europe/London", "2026-03-29T18:45:00Z"),
            ("2026-10-25T19:45:00", "Europe/London", "2026-10-25T19:45:00Z"),
            ("2026-12-31T23:30:00-03:00", "UTC-03:00", "2027-01-01T02:30:00Z"),
            ("2026-01-01T01:00:00+09:00", "Asia/Tokyo", "2025-12-31T16:00:00Z"),
            ("2028-02-29T12:00:00Z", "UTC", "2028-02-29T12:00:00Z"),
        ]
        for value, zone, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(expected, self.scraper._normalize_datetime(value, zone)[1])

    def test_missing_unknown_and_ambiguous_clocks_are_not_fabricated(self):
        cases = [
            ("2026-10-02", "Europe/London"), ("TBC", "UTC"),
            ("2026-02-30T18:45:00", "UTC"),
            ("2026-10-02T19:45:00", "Unknown/Zone"),
            ("2026-10-02T19:45:00", None),
            ("2026-03-29T01:30:00", "Europe/London"),
            ("2026-10-25T01:30:00", "Europe/London"),
            ("05/02/2026 14:00", "UTC"),
        ]
        for value, zone in cases:
            with self.subTest(value=value, zone=zone):
                self.assertIsNone(self.scraper._normalize_datetime(value, zone)[1])
        self.assertEqual("2026-02-05T14:00:00Z", self.scraper._normalize_datetime("05/02/2026 14:00", "UTC", dayfirst=True)[1])
        self.assertEqual("2026-05-02T14:00:00Z", self.scraper._normalize_datetime("05/02/2026 14:00", "UTC", dayfirst=False)[1])
        for value in ("12:00", "October 2 19:45", "2026", "05/02/2026"):
            with self.subTest(incomplete=value):
                self.assertIsNone(self.scraper._normalize_datetime(value, "UTC", dayfirst=True)[1])

    def test_unknown_time_preserves_known_calendar_date(self):
        match = fixture(kickoff="2026-10-02")
        self.assertEqual("2026-10-02", match["kickoff_date"])
        self.assertEqual("", match["kickoff_utc"])

    def test_aware_datetime_converts_to_declared_timezone_without_changing_instant(self):
        local, utc, zone = self.scraper._normalize_datetime("2026-10-02T18:45:00Z", "Europe/Paris")
        self.assertEqual("2026-10-02T20:45:00+02:00", local)
        self.assertEqual("2026-10-02T18:45:00Z", utc)
        self.assertEqual("Europe/Paris", zone)


class SourceAndIdentityTests(unittest.TestCase):
    def test_official_identity_survives_insertion_and_rescheduling(self):
        scraper = UnitedRugbyChampionshipScraper()
        one = fixture()
        rescheduled = fixture(kickoff="2026-10-03T18:45:00Z")
        inserted = fixture(source_id="earlier-official-id", kickoff="2026-10-01T18:45:00Z")
        before = copy.deepcopy(one)
        after = scraper.assign_match_ids([one, inserted])
        same_match = next(m for m in after if m["source_match_id"] == before["source_match_id"])
        self.assertEqual(before["stable_id"], same_match["stable_id"])
        self.assertNotEqual(before["match_id"], same_match["match_id"])
        self.assertEqual(before["stable_id"], rescheduled["stable_id"])
        self.assertEqual("official", rescheduled["identity_strength"])

    def test_official_id_reused_across_seasons_or_providers_stays_distinct(self):
        current = fixture(source_id="1", season="2026")
        following = fixture(source_id="1", season="2027", kickoff="2027-10-02T18:45:00Z")
        self.assertNotEqual(current["stable_id"], following["stable_id"])
        self.assertEqual("rugbyviz", current["source_provider"])
        self.assertEqual(2, current["identity_version"])
        other = copy.deepcopy(current)
        other.pop("stable_id"); other["source_provider"] = "another-official-provider"
        UnitedRugbyChampionshipScraper._add_stable_identity(other)
        self.assertNotEqual(current["stable_id"], other["stable_id"])
        self.assertEqual(current["stable_id"], fixture(source_id="1", season="2026", kickoff="2026-10-04T18:45:00Z")["stable_id"])

    def test_legacy_stable_upgrade_keeps_explicit_reviewable_migration_alias(self):
        match = fixture()
        expected = match["stable_id"]
        match["stable_id"] = "urc:legacy-id"
        match.pop("identity_version")
        UnitedRugbyChampionshipScraper._add_stable_identity(match)
        self.assertEqual(expected, match["stable_id"])
        self.assertEqual(["urc:legacy-id"], match["previous_stable_ids"])
        self.assertEqual(2, match["identity_version"])

    def test_generic_urls_are_weak_and_never_collapse_different_matches(self):
        scraper = UnitedRugbyChampionshipScraper()
        for url in ("https://www.world.rugby/fixtures", "https://league-one.jp/schedule/",
                    "https://www.epcrugby.com/champions-cup/matches", "https://www.world.rugby/matches/2026",
                    "https://www.sixnationsrugby.com/en/m6n/fixtures/2026"):
            matches = []
            for away in ("Zebre Parma", "Glasgow Warriors"):
                match = fixture()
                match.pop("stable_id"); match.pop("source_match_id"); match["match_id"] = ""
                match["match_url"] = url; match["away_team"] = away
                scraper._add_stable_identity(match)
                self.assertEqual("weak", match["identity_strength"])
                matches.append(match)
            self.assertNotEqual(matches[0]["stable_id"], matches[1]["stable_id"])

    def test_six_nations_match_slug_is_specific_but_landing_page_is_not(self):
        url = "https://www.sixnationsrugby.com/en/m6n/fixtures/2026/italy-v-scotland-07022026-1510/build-up"
        canonical, source_id = UnitedRugbyChampionshipScraper._canonical_match_identity_url(url)
        self.assertTrue(canonical.endswith("italy-v-scotland-07022026-1510"))
        self.assertEqual("", source_id)

    def test_canonical_official_url_ignores_status_and_query(self):
        scraper = UnitedRugbyChampionshipScraper()
        one = fixture()
        one.pop("stable_id"); one.pop("source_match_id"); one["match_id"] = ""
        one["match_url"] = "https://league-one.jp/match/29312/print?campaign=1"
        two = copy.deepcopy(one); two["match_url"] = "https://league-one.jp/match/29312"
        scraper._add_stable_identity(one); scraper._add_stable_identity(two)
        self.assertEqual(one["stable_id"], two["stable_id"])

    def test_numeric_rugbyviz_season_and_partition(self):
        scraper = UnitedRugbyChampionshipScraper()
        self.assertEqual("202601", scraper._extract_config_value('season:202601', "season", numeric=True))
        self.assertEqual("202601", scraper._extract_config_value('"season": "202601"', "season", numeric=True))
        match = scraper._normalize_match({"id": 123, "date": "2027-01-02T17:30:00Z",
            "homeTeam": {"name": "Cardiff Rugby"}, "awayTeam": {"name": "Glasgow Warriors"}}, {"season": "2026"})
        self.assertEqual("2026", match["season"])
        self.assertEqual("2027-01-02T17:30:00Z", match["kickoff_utc"])
        self.assertEqual("123", match["source_match_id"])

    def test_trc_filter_excludes_other_rugby_championships(self):
        scraper = RugbyChampionshipScraper()
        for title in ("Rugby Championship", "The Rugby Championship", "Rugby Championship 2027"):
            self.assertTrue(scraper._is_target_competition(title))
        for title in ("Asian Rugby Championship", "Pacific Rugby Championship", "U20 Rugby Championship", "Nations Championship 2026"):
            self.assertFalse(scraper._is_target_competition(title))

    def test_nc_retains_existing_branch_filter(self):
        scraper = NationsChampionshipScraper()
        self.assertTrue(scraper._is_target_competition("Nations Championship 2026"))
        self.assertFalse(scraper._is_target_competition("World Rugby Nations Cup 2026"))

    def test_top14_french_dates_and_real_season(self):
        scraper = Top14Scraper()
        self.assertEqual("2026-10-02 21:05:00", scraper._format_date_time("Vendredi 2 octobre", "21h05", season="2026-2027"))
        self.assertEqual("2027-01-02 15:00:00", scraper._format_date_time("Samedi 2 janvier", "15h", season="2026-2027"))
        self.assertEqual("2026-02-07 15:00:00", scraper._format_date_time("Samedi 7 février 2026", "15", season="2025-2026"))
        self.assertIsNone(scraper._format_date_time("2 octobre", "À déterminer", season="2026-2027"))
        self.assertIsNone(scraper._format_date_time("31 février", "15h", season="2026-2027"))

    def test_epcr_display_date_is_padded_and_uses_browser_timezone(self):
        scraper = EPCRChampionsCupScraper()
        value = scraper.format_date_string("Sat, 7 Feb 2026 - 15:00")
        self.assertEqual("2026-02-07 15:00:00", value)
        self.assertEqual("2026-02-07T14:00:00Z", scraper._normalize_datetime(value, "Europe/Paris")[1])

    def test_jrlo_essential_schedule_never_requests_print_pages(self):
        scraper = LeagueOneDivisionsScraper()
        html = '<div class="c-schedule"><h3 class="ttl">ディビジョン1 第18節 (M123)</h3><a class="btn-match-detail">試合終了</a><li class="home"><p class="score">30</p></li><li class="away"><p class="score">20</p></li></div>'
        card = BeautifulSoup(html, "html.parser").select_one(".c-schedule")
        scraper._existing_match_details = {"https://league-one.jp/match/1": {"home_tries": 4}}
        with patch.object(scraper, "_fetch_print_match_details", side_effect=AssertionError("secondary HTTP requested")):
            details = scraper._extract_schedule_details(card, datetime.now(scraper.jst), "https://league-one.jp/match/1")
        self.assertEqual(4, details["home_tries"])
        self.assertEqual(30, details["home_score"])

    def test_jrlo_uses_official_season_cross_year(self):
        scraper = LeagueOneDivisionsScraper()
        soup = BeautifulSoup('<select name="year"><option value="2025">2025-26</option><option value="2026" selected>2026-27</option></select>', "html.parser")
        scraper._schedule_start_year = scraper._extract_schedule_start_year(soup)
        self.assertEqual(2026, scraper.parse_kickoff_datetime("12.19 土 13:00").year)
        self.assertEqual(2027, scraper.parse_kickoff_datetime("01.09 土 13:00").year)


class PublicationReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data_dir = Path(self.temp.name) / "data"
        self.path = self.data_dir / "matches/urc/2026.json"
        write_json_atomic(self.path, [fixture()])
        write_json_atomic(self.data_dir / "competitions_base.json", [{"id": "urc", "name": "URC", "data_paths": ["data/matches/urc/fictional.json"]}])
        write_json_atomic(self.data_dir / "competitions.json", [{"id": "urc", "name": "URC", "logo_url": "existing-logo", "data_summary": {"match_count": 0}}])
        self.health = {"files": {}, "sources": {}}

    def fake_run(self, candidate=None, returncode=0, timeout=False):
        def run(command, *, env, **kwargs):
            if timeout:
                raise subprocess.TimeoutExpired(command, 300)
            if candidate is not None:
                write_json_atomic(Path(env["RUGBY_DATA_DIR"]) / "matches/urc/2026.json", candidate)
            return subprocess.CompletedProcess(command, returncode, "", "")
        return run

    def test_failed_and_timed_out_sources_preserve_exact_last_good_bytes(self):
        before = self.path.read_bytes()
        for run in (self.fake_run([], returncode=1), self.fake_run(timeout=True), self.fake_run([])):
            with self.subTest(run=run):
                result = collect_source("urc", self.data_dir, self.health, run=run)
                self.assertEqual("failed", result["outcome"])
                self.assertEqual(before, self.path.read_bytes())

    def test_empty_source_does_not_clear_old_data_or_claim_success(self):
        before = self.path.read_bytes()
        result = collect_source("urc", self.data_dir, self.health, run=self.fake_run())
        self.assertEqual("no_fixtures", result["outcome"])
        self.assertEqual(before, self.path.read_bytes())
        self.assertNotIn("last_success_at", self.health["sources"]["urc"])

    def test_healthy_source_promotes_and_failed_retry_keeps_verified_hash(self):
        result = collect_source("urc", self.data_dir, self.health, run=self.fake_run([fixture(kickoff="2026-10-03T18:45:00Z")]))
        self.assertEqual("success", result["outcome"])
        before = self.path.read_bytes()
        last_success = self.health["sources"]["urc"]["last_success_at"]
        collect_source("urc", self.data_dir, self.health, run=self.fake_run([], returncode=1))
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(last_success, self.health["sources"]["urc"]["last_success_at"])
        write_json_atomic(self.data_dir / "source_health.json", self.health)
        _, manifest = build_competitions(self.data_dir)
        self.assertEqual("stale", manifest["competitions"][0]["status"])
        self.assertEqual(["data/matches/urc/2026.json"], manifest["competitions"][0]["data_paths"])

    def test_manifest_only_lists_verified_actual_paths_and_preserves_master(self):
        future = fixture(kickoff="2027-01-02T17:30:00Z")
        collect_source("urc", self.data_dir, self.health, run=self.fake_run([future]))
        write_json_atomic(self.data_dir / "source_health.json", self.health)
        masters, manifest = build_competitions(self.data_dir)
        comp = manifest["competitions"][0]
        self.assertEqual(["data/matches/urc/2026.json"], comp["data_paths"])
        self.assertEqual(["2026"], comp["seasons"])
        self.assertEqual("existing-logo", masters[0]["logo_url"])
        self.assertEqual(1, masters[0]["data_summary"]["match_count"])
        self.assertEqual(file_sha256(self.path), comp["files"][0]["sha256"])
        self.assertEqual(1, comp["coverage"]["known_kickoffs"])

    def test_mtime_does_not_promote_old_data_and_hash_tampering_revokes_trust(self):
        _, manifest = build_competitions(self.data_dir)
        self.assertEqual([], manifest["competitions"][0]["data_paths"])
        self.assertEqual("unverified", manifest["competitions"][0]["files"][0]["trust"])
        collect_source("urc", self.data_dir, self.health, run=self.fake_run([fixture()]))
        write_json_atomic(self.data_dir / "source_health.json", self.health)
        write_json_atomic(self.path, [fixture(kickoff="2026-10-04T18:45:00Z")])
        _, manifest = build_competitions(self.data_dir)
        self.assertEqual([], manifest["competitions"][0]["data_paths"])

    def test_validation_rejects_path_mismatch_inconsistent_times_and_duplicates(self):
        bads = []
        wrong = fixture(); wrong["season"] = "2027"; bads.append([wrong])
        wrong = fixture(); wrong["kickoff"] = "2026-10-02T19:45:00+00:00"; bads.append([wrong])
        wrong = fixture(); wrong["timezone"] = "Europe/Paris"; bads.append([wrong])
        bads.append([fixture(), fixture()])
        for candidate in bads:
            with self.subTest(candidate=candidate):
                write_json_atomic(self.path, candidate)
                with self.assertRaises(ValueError):
                    validate_match_file(self.path)

    def test_shared_consumer_datetime_contract(self):
        cases = json.loads((Path(__file__).parent / "fixtures/datetime-contract.json").read_text())
        for case in cases:
            with self.subTest(case=case["name"]):
                candidate = fixture(source_id=case["name"], kickoff="2026-10-02T19:45:00+01:00")
                candidate["match_id"] = "contract-" + case["name"]
                candidate.update(kickoff="2026-10-02T19:45:00+01:00", kickoff_utc="2026-10-02T18:45:00Z", timezone="Europe/London")
                if case.get("unknown"):
                    candidate.update(kickoff="", kickoff_utc="")
                candidate.update(case["change"])
                write_json_atomic(self.path, [fixture(source_id="known-control"), candidate])
                if case["valid"]:
                    self.assertEqual(2, validate_match_file(self.path)["match_count"])
                else:
                    with self.assertRaises(ValueError):
                        validate_match_file(self.path)

    def test_invalid_contract_records_never_replace_verified_last_good(self):
        collect_source("urc", self.data_dir, self.health, run=self.fake_run([fixture()]))
        before = self.path.read_bytes()
        verified = copy.deepcopy(self.health["files"])
        for change in [{"timezone": "UTC+99:99"}, {"timezone": "UTC+09:00"},
                       {"kickoff": "", "kickoff_utc": "", "kickoff_date": "not-a-date"}]:
            with self.subTest(change=change):
                bad = fixture(source_id="invalid-record")
                bad["match_id"] = "invalid-record"
                bad.update(change)
                result = collect_source("urc", self.data_dir, self.health, run=self.fake_run([fixture(), bad]))
                self.assertEqual("failed", result["outcome"])
                self.assertEqual(before, self.path.read_bytes())
                self.assertEqual(verified, self.health["files"])

    def test_previous_validation_version_retains_only_currently_valid_last_good(self):
        collect_source("urc", self.data_dir, self.health, run=self.fake_run([fixture()]))
        relative = "data/matches/urc/2026.json"
        self.health["files"][relative]["validation_version"] = 2
        before = self.path.read_bytes()
        collect_source("urc", self.data_dir, self.health, run=self.fake_run([], returncode=1))
        write_json_atomic(self.data_dir / "source_health.json", self.health)
        _, manifest = build_competitions(self.data_dir)
        self.assertEqual([relative], manifest["competitions"][0]["data_paths"])
        self.assertEqual("stale", manifest["competitions"][0]["status"])
        self.assertEqual(before, self.path.read_bytes())
        invalid = fixture()
        invalid["timezone"] = "UTC+99:99"
        write_json_atomic(self.path, [invalid])
        self.health["files"][relative]["sha256"] = file_sha256(self.path)
        write_json_atomic(self.data_dir / "source_health.json", self.health)
        _, manifest = build_competitions(self.data_dir)
        self.assertEqual([], manifest["competitions"][0]["data_paths"])
        self.assertEqual("invalid", manifest["competitions"][0]["files"][0]["trust"])

    def test_official_all_unknown_dates_publish_without_midnight_and_fail_closed(self):
        write_json_atomic(self.data_dir / "competitions_base.json", [{"id": "urc", "name": "URC", "official_sites": ["https://official.example"]}])
        candidate = fixture(source_id="official-date-only", kickoff="2026-12-12")
        candidate.update(source_url="https://official.example/schedule", source_type="official")
        result = collect_source("urc", self.data_dir, self.health, run=self.fake_run([candidate]))
        self.assertEqual("success", result["outcome"])
        write_json_atomic(self.data_dir / "source_health.json", self.health)
        _, manifest = build_competitions(self.data_dir)
        c = manifest["competitions"][0]
        self.assertEqual(["data/matches/urc/2026.json"], c["data_paths"])
        self.assertEqual({"start": "", "end": ""}, c["coverage"]["date_range"])
        self.assertEqual(0, c["coverage"]["known_kickoffs"])
        self.assertEqual(1, c["coverage"]["unknown_kickoffs"])
        before = self.path.read_bytes()
        for change in [{"kickoff_unknown_reason": "parse_failure"}, {"source_url": "https://unrelated.example"},
                       {"kickoff_date": "2026-02-30"}, {"venue": ""}, {"source_type": "curated"}]:
            with self.subTest(change=change):
                bad = {**candidate, **change}
                outcome = collect_source("urc", self.data_dir, self.health, run=self.fake_run([bad]))
                self.assertEqual("failed", outcome["outcome"])
                self.assertEqual(before, self.path.read_bytes())

    def test_second_invalid_file_rejects_the_whole_source_without_promoting_first(self):
        before = self.path.read_bytes()
        def run(command, *, env, **kwargs):
            staging = Path(env["RUGBY_DATA_DIR"])
            write_json_atomic(staging / "matches/urc/2026.json", [fixture(kickoff="2026-10-03T18:45:00Z")])
            write_json_atomic(staging / "matches/urc/2027.json", [fixture()])
            return subprocess.CompletedProcess(command, 0, "", "")
        result = collect_source("urc", self.data_dir, self.health, run=run)
        self.assertEqual("failed", result["outcome"])
        self.assertEqual(before, self.path.read_bytes())
        self.assertFalse((self.data_dir / "matches/urc/2027.json").exists())

    def test_rename_failure_restores_all_divisions_and_does_not_record_success(self):
        paths = [self.data_dir / f"matches/jrlo-div{i}/2026.json" for i in (1, 2)]
        for i, path in enumerate(paths, 1):
            write_json_atomic(path, [fixture(comp=f"jrlo-div{i}")])
        before = [p.read_bytes() for p in paths]
        def run(command, *, env, **kwargs):
            staging = Path(env["RUGBY_DATA_DIR"])
            for i in (1, 2):
                write_json_atomic(staging / f"matches/jrlo-div{i}/2026.json", [fixture(comp=f"jrlo-div{i}", kickoff="2026-10-03T18:45:00Z")])
            return subprocess.CompletedProcess(command, 0, "", "")
        original_replace = Path.replace
        def replace(path, target):
            if path.suffix == ".tmp" and Path(target) == paths[1]:
                raise OSError("simulated second promotion failure")
            return original_replace(path, target)
        with patch.object(Path, "replace", replace):
            result = collect_source("jrlo", self.data_dir, self.health, run=run)
        self.assertEqual("failed", result["outcome"])
        self.assertEqual(before, [p.read_bytes() for p in paths])
        self.assertEqual({}, self.health["files"])


if __name__ == "__main__":
    unittest.main()
