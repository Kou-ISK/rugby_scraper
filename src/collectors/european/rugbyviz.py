import re
import requests
from datetime import datetime
from ..base import BaseScraper

class RugbyVizScraper(BaseScraper):
    def __init__(
        self,
        *,
        competition_id: int,
        competition_slug: str,
        competition_name: str,
        source_url: str,
        config_url: str,
        source_name: str,
    ):
        super().__init__()
        self.api_base = "https://rugby-union-feeds.incrowdsports.com"
        self.competition_id = competition_id
        self.competition_slug = competition_slug
        self.competition_name = competition_name
        self.source_url = source_url
        self.config_url = config_url
        self.source_name = source_name
        self._config_cache = None

    def _fetch_config(self):
        if self._config_cache:
            return self._config_cache
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        html = requests.get(self.config_url, headers=headers, timeout=30).text
        api_key = self._extract_config_value(html, "apiKey")
        app_id = self._extract_config_value(html, "appId")
        realm_id = self._extract_config_value(html, "realmId")
        client_id = self._extract_config_value(html, "clientId")
        season_raw = self._extract_config_value(html, "season", numeric=True)
        provider = self._extract_config_value(html, "dataProvider")

        # デバッグ: season_rawの値を確認
        print(f"🔍 DEBUG: season_raw = {season_raw} (type: {type(season_raw)})")

        # seasonが202501形式の場合、先頭4桁（年）のみを抽出
        season = season_raw[:4] if season_raw and len(season_raw) >= 4 else season_raw
        
        print(f"🔍 DEBUG: season = {season} (extracted from season_raw)")

        self._config_cache = {
            "api_key": api_key,
            "app_id": app_id,
            "realm_id": realm_id,
            "client_id": client_id,
            "season": season,
            "season_id": season_raw,  # API呼び出し用の元のseason
            "provider": provider or "rugbyviz",
        }
        return self._config_cache

    def _extract_config_value(self, html: str, key: str, numeric: bool = False):
        if numeric:
            match = re.search(rf"{key}:(\\d+)", html)
        else:
            match = re.search(rf'{key}:"([^"]+)"', html)
        return match.group(1) if match else None

    def scrape(self):
        try:
            config = self._fetch_config()
            if not config.get("api_key"):
                print("API設定の取得に失敗しました")
                return None

            headers = {
                "X-API-KEY": config["api_key"],
                "X-APP-ID": config["app_id"],
                "X-REALM": config["realm_id"],
            }
            params = {
                "clientId": config["client_id"],
                "provider": config["provider"],
                "seasonId": config.get("season_id") or config["season"],  # API呼び出しには元のseason_id使用
                "compId": str(self.competition_id),
                "pageSize": 200,
                "pageNumber": 0,
            }

            all_matches = []
            first_page = requests.get(
                f"{self.api_base}/v1/matches", headers=headers, params=params, timeout=30
            ).json()
            all_matches.extend(first_page.get("data", []))

            total_pages = first_page.get("metadata", {}).get("totalPages", 1)
            for page in range(1, total_pages):
                params["pageNumber"] = page
                page_data = requests.get(
                    f"{self.api_base}/v1/matches", headers=headers, params=params, timeout=30
                ).json()
                all_matches.extend(page_data.get("data", []))

            normalized = [self._normalize_match(m, config) for m in all_matches]
            
            # Assign match IDs and save
            if normalized:
                normalized = self.assign_match_ids(normalized)
                
                # season決定: configから取得、なければ試合データから判定
                season = config.get("season")
                if not season:
                    # 最初の試合のkickoffから年を抽出
                    first_kickoff = normalized[0].get("kickoff_utc", "")
                    if first_kickoff:
                        season = first_kickoff[:4]  # "2025-09-26..." -> "2025"
                        print(f"⚠️  WARNING: season not in config, using first match year: {season}")
                    else:
                        season = str(datetime.now().year)
                        print(f"⚠️  WARNING: no season data, using current year: {season}")
                
                print(f"📅 Season: {season}")
                filename = f"{self.competition_slug}/{season}"
                self.save_to_json(normalized, filename)
                print(f"✅ {len(normalized)}試合を保存: {filename}.json")
            
            return normalized

        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _normalize_match(self, match, config):
        home_team = match.get("homeTeam", {}) or {}
        away_team = match.get("awayTeam", {}) or {}
        venue = match.get("venue", {}) or {}
        broadcasters = match.get("broadcasters") or []
        if not broadcasters and match.get("icBroadcasters"):
            broadcasters = [b.get("name") for b in match.get("icBroadcasters") if b.get("name")]

        round_name = ""
        if match.get("round"):
            round_name = f"Round {match.get('round')}"
        elif match.get("title"):
            round_name = str(match.get("title"))

        # season決定: 試合データから年を抽出（kickoffから判定）
        season = None
        kickoff_date = match.get("date")
        if kickoff_date:
            # "2025-09-26T..." -> "2025"
            season = kickoff_date[:4]
        
        # フォールバック: configから取得
        if not season:
            season = config.get("season") or str(datetime.now().year)

        home_team_name = home_team.get("name", "")
        away_team_name = away_team.get("name", "")
        
        # team_idを自動解決（teams.jsonに自動登録）
        home_team_id = self._resolve_team_id(home_team_name, self.competition_slug) if home_team_name else None
        away_team_id = self._resolve_team_id(away_team_name, self.competition_slug) if away_team_name else None
        
        return self.build_match(
            competition_id=self.competition_slug,
            season=season,
            round_name=round_name,
            status=match.get("status", ""),
            kickoff=match.get("date"),
            timezone_name="UTC",
            venue=venue.get("name", ""),
            home_team=home_team_name,
            away_team=away_team_name,
            match_url="",
            broadcasters=broadcasters,
            match_id=match.get("id"),
            home_team_id=home_team_id,
            away_team_id=away_team_id,
        )

class GallagherPremiershipScraper(RugbyVizScraper):
    def __init__(self):
        super().__init__(
            competition_id=1011,
            competition_slug="gp",  # Gallagher Premiership の正式ID
            competition_name="Gallagher Premiership",
            source_url="https://www.premiershiprugby.com/fixtures-results/",
            config_url="https://www.premiershiprugby.com/fixtures-results/",
            source_name="Premiership Rugby (RugbyViz data feed)",
        )

class UnitedRugbyChampionshipScraper(RugbyVizScraper):
    def __init__(self):
        super().__init__(
            competition_id=1068,
            competition_slug="urc",
            competition_name="United Rugby Championship",
            source_url="https://www.unitedrugby.com",
            config_url="https://www.premiershiprugby.com/fixtures-results/",
            source_name="United Rugby Championship (RugbyViz data feed)",
        )
