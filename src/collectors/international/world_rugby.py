import re
from datetime import datetime, timedelta, timezone
import requests
from ..base import BaseScraper


class WorldRugbyInternationalsScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.api_base = "https://api.wr-rims-prod.pulselive.com"
        self.source_url = "https://www.world.rugby/fixtures"
        self.match_url_template = "https://www.world.rugby/match/{match_id}"
        self.source_name = "World Rugby"
        self.page_size = 50
        self.lookback_days = 30
        self.lookahead_days = 450
        self.include_patterns = [
            r"Autumn Nations Series",
            r"Rugby Championship",
            r"Men's Internationals",
            r"Women's Internationals",
            r"Pacific Nations Cup",
            r"Nations Championship",
            r"Summer Nations Series",
        ]
        self.exclude_patterns = [
            r"Six Nations",
            r"U20",
            r"U18",
            r"U21",
            r"U19",
            r"Sevens",
        ]

    def scrape(self):
        try:
            start_date, end_date = self._date_range()
            matches = self._fetch_matches(start_date, end_date)
            
            # Assign match IDs and save
            if matches:
                matches = self.assign_match_ids(matches)
                
                season = str(datetime.utcnow().year)
                filename = f"wri/{season}"
                self.save_to_json(matches, filename)
                print(f"✅ {len(matches)}試合を保存: {filename}.json")
            
            return matches
        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            return None

    def _date_range(self):
        now = datetime.utcnow().date()
        start_date = now - timedelta(days=self.lookback_days)
        end_date = now + timedelta(days=self.lookahead_days)
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def _fetch_matches(self, start_date: str, end_date: str):
        params = {
            "pageSize": self.page_size,
            "page": 0,
            "startDate": start_date,
            "endDate": end_date,
        }
        first_page = requests.get(
            f"{self.api_base}/rugby/v3/match", params=params, timeout=30
        ).json()
        page_info = first_page.get("pageInfo", {})
        total_pages = page_info.get("numPages", 0)
        matches = self._normalize_matches(first_page.get("content", []))

        for page in range(1, total_pages):
            params["page"] = page
            data = requests.get(
                f"{self.api_base}/rugby/v3/match", params=params, timeout=30
            ).json()
            matches.extend(self._normalize_matches(data.get("content", [])))

        return matches

    def _normalize_matches(self, raw_matches):
        normalized = []
        for match in raw_matches:
            competition = match.get("competition")
            if not self._is_target_competition(competition):
                continue

            time_info = match.get("time", {}) or {}
            kickoff_utc, tz_name = self._build_kickoff(time_info)

            teams = match.get("teams") or []
            home_team, away_team = self._split_teams(teams)

            venue = match.get("venue", {}) or {}
            event = match.get("events") or []
            
            # team_idを自動解決（teams.jsonに自動登録）
            home_team_name = home_team.get("name", "") if home_team else ""
            away_team_name = away_team.get("name", "") if away_team else ""
            home_team_id = self._resolve_team_id(home_team_name, "wri") if home_team_name else None
            away_team_id = self._resolve_team_id(away_team_name, "wri") if away_team_name else None

            normalized.append(
                self.build_match(
                    competition_id="wri",
                    season=str(datetime.utcnow().year),
                    round_name=match.get("eventPhase") or "",
                    status=match.get("status") or "",
                    kickoff=kickoff_utc,
                    timezone_name=tz_name,
                    venue=venue.get("name", ""),
                    home_team=home_team_name,
                    away_team=away_team_name,
                    match_url=self.match_url_template.format(
                        match_id=match.get("matchId")
                    ),
                    broadcasters=[],
                    match_id=match.get("matchId"),
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                )
            )
        return normalized

    def _build_kickoff(self, time_info):
        millis = time_info.get("millis")
        gmt_offset = time_info.get("gmtOffset", 0.0) or 0.0
        if millis is None:
            return None, "UTC"

        utc_dt = datetime.fromtimestamp(millis / 1000, tz=timezone.utc)
        offset = timedelta(hours=gmt_offset)
        tz = timezone(offset)
        local_dt = utc_dt.astimezone(tz)
        offset_sign = "+" if offset.total_seconds() >= 0 else "-"
        offset_minutes = int(abs(offset.total_seconds()) // 60)
        offset_hours, offset_mins = divmod(offset_minutes, 60)
        tz_name = f"UTC{offset_sign}{offset_hours:02}:{offset_mins:02}"
        return local_dt, tz_name

    def _split_teams(self, teams):
        if len(teams) >= 2:
            return teams[0], teams[1]
        if len(teams) == 1:
            return teams[0], {}
        return {}, {}

    def _is_target_competition(self, competition):
        if not competition or not isinstance(competition, str):
            return False

        if any(re.search(pattern, competition, re.IGNORECASE) for pattern in self.exclude_patterns):
            return False

        return any(re.search(pattern, competition, re.IGNORECASE) for pattern in self.include_patterns)


class WorldRugbyCompetitionScraper(WorldRugbyInternationalsScraper):
    def __init__(self, include_patterns, source_url=None, source_name=None):
        super().__init__()
        self.include_patterns = include_patterns
        if source_url:
            self.source_url = source_url
        if source_name:
            self.source_name = source_name


class RugbyChampionshipScraper(WorldRugbyCompetitionScraper):
    def __init__(self):
        super().__init__(
            include_patterns=[r"Rugby Championship"],
            source_url="https://www.world.rugby/fixtures",
            source_name="World Rugby",
        )


class AutumnNationsSeriesScraper(WorldRugbyCompetitionScraper):
    def __init__(self):
        super().__init__(
            include_patterns=[r"Autumn Nations Series"],
            source_url="https://www.world.rugby/fixtures",
            source_name="World Rugby",
        )
