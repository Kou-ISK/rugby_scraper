import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
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
        logos_url: str = None,
        fetch_official_logos: bool = True,
        update_team_master: bool = False,
    ):
        super().__init__(update_team_master=update_team_master)
        self.api_base = "https://rugby-union-feeds.incrowdsports.com"
        self.competition_id = competition_id
        self.competition_slug = competition_slug
        self.competition_name = competition_name
        self.source_url = source_url
        self.config_url = config_url
        self.logos_url = logos_url or config_url
        self.source_name = source_name
        self.fetch_official_logos = fetch_official_logos
        self._config_cache = None
        self._team_logos_cache = {}  # 公式サイトから取得したロゴURL

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
    
    def _fetch_team_logos_from_official_site(self):
        """公式サイトからチームロゴURLを取得
        
        RugbyViz公式サイト（Premiership Rugby/URC）のHTMLから
        チーム名とロゴURLの対応を抽出
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            response = requests.get(self.logos_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # チームロゴの抽出（img要素からalt属性とsrc属性を取得）
            # Premiership Rugby/URCサイトでは通常 <img alt="Team Name" src="..."> 形式
            team_imgs = soup.find_all('img', alt=True, src=True)
            
            for img in team_imgs:
                alt_text = img.get('alt', '').strip()
                src = img.get('src', '').strip()
                
                # チーム名らしい文字列とロゴURLらしいパス
                if alt_text and src and (
                    'media-cdn.incrowdsports.com' in src or
                    'media-cdn.cortextech.io' in src
                ):
                    # 相対URLを絶対URLに変換
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        from urllib.parse import urlparse, urljoin
                        base_url = f"{urlparse(self.logos_url).scheme}://{urlparse(self.logos_url).netloc}"
                        src = urljoin(base_url, src)
                    
                    # クエリパラメータを除去（安定化）
                    clean_src = src.split('?')[0]
                    
                    self._team_logos_cache[alt_text] = {
                        "logo_url": clean_src,
                        "badge_url": clean_src,
                    }
                    print(f"  🖼️  {alt_text}: {clean_src[:80]}...")
            
            if self._team_logos_cache:
                print(f"✅ 公式サイトから{len(self._team_logos_cache)}チームのロゴURLを取得")
            else:
                print("⚠️  公式サイトからロゴURLを取得できませんでした")
                
        except Exception as e:
            print(f"⚠️  公式サイトからのロゴURL取得エラー: {e}")
    
    def _get_team_logo_from_cache(self, team_name: str) -> dict:
        """キャッシュからチームロゴURLを取得
        
        Args:
            team_name: チーム名
            
        Returns:
            {"logo_url": "...", "badge_url": "..."} または空辞書
        """
        # 完全一致
        if team_name in self._team_logos_cache:
            return self._team_logos_cache[team_name]
        
        # 大文字小文字を無視して検索
        team_name_lower = team_name.lower()
        for cached_name, logo_info in self._team_logos_cache.items():
            if cached_name.lower() == team_name_lower:
                return logo_info
        
        # 部分一致（キャッシュ名がチーム名に含まれる）
        for cached_name, logo_info in self._team_logos_cache.items():
            if cached_name.lower() in team_name_lower or team_name_lower in cached_name.lower():
                return logo_info
        
        return {}

    def scrape(self):
        try:
            # 公式サイトからチームロゴURLを取得
            if self.fetch_official_logos:
                print("🔍 公式サイトからチームロゴを取得中...")
                self._fetch_team_logos_from_official_site()
            
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
            if normalized:
                team_names = {m.get("home_team", "") for m in normalized} | {m.get("away_team", "") for m in normalized}
                official_logos = {}
                for team_name in team_names:
                    if not team_name:
                        continue
                    logo_info = self._get_team_logo_from_cache(team_name)
                    if logo_info:
                        official_logos[team_name] = logo_info
                if official_logos:
                    self._apply_official_team_logos(official_logos, self.competition_slug)
            
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
        
        # team_idを自動解決（teams.jsonに自動登録、公式ロゴ使用）
        home_team_id = self._resolve_team_id_with_official_logo(home_team_name, self.competition_slug) if home_team_name else None
        away_team_id = self._resolve_team_id_with_official_logo(away_team_name, self.competition_slug) if away_team_name else None
        
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
    
    def _resolve_team_id_with_official_logo(self, team_name: str, competition_id: str = None) -> str:
        """チームIDを解決し、新規登録時は公式ロゴURLを使用
        
        Args:
            team_name: チーム名
            competition_id: 大会ID
            
        Returns:
            チームID
        """
        if not team_name:
            return ""
        
        # スポンサー名を除去
        base_team_name = self._normalize_team_name(team_name, competition_id)
        
        # 既存チーム検索
        if competition_id:
            for team_id, team_data in self._team_master.items():
                if team_data.get("competition_id") == competition_id:
                    if base_team_name.upper() == team_data.get("short_name", "").upper():
                        return team_id
                    if base_team_name.lower() == team_data.get("name", "").lower():
                        return team_id
            
            # 新規チーム登録（公式ロゴ使用）
            if not self._update_team_master:
                return ""
            club_team_id = self._generate_club_team_id(base_team_name, competition_id)
            logo_info = self._get_team_logo_from_cache(team_name)
            self._register_club_team(club_team_id, team_name, competition_id, logo_info)
            return club_team_id
        
        return ""

class GallagherPremiershipScraper(RugbyVizScraper):
    def __init__(self):
        super().__init__(
            competition_id=1011,
            competition_slug="premier",
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
            logos_url="https://www.unitedrugby.com",
            source_name="United Rugby Championship (RugbyViz data feed)",
            fetch_official_logos=True,
        )
