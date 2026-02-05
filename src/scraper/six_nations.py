from datetime import datetime
from dateutil import parser as date_parser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from .base import BaseScraper
try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    from backports.zoneinfo import ZoneInfo

class SixNationsBaseScraper(BaseScraper):
    def __init__(self, competition_path: str, competition_name: str, competition_id: str):
        super().__init__()
        self.base_url = "https://www.sixnationsrugby.com"
        self.calendar_url = f"{self.base_url}/en/{competition_path}/fixtures/"
        self.competition_name = competition_name
        self._competition_id = competition_id  # BaseScraperの_competition_idを設定
        self.display_timezone = "Europe/London"
        self.driver = None
    
    def _get_competition_id(self) -> str:
        """Return competition ID for this scraper."""
        return self._competition_id

    def scrape(self):
        try:
            self._initialize_driver_and_load_page()
            matches = self._extract_matches(BeautifulSoup(self.driver.page_source, 'html.parser'))
            return matches
        except Exception as e:
            import traceback
            print(f"スクレイピングエラー: {str(e)}")
            traceback.print_exc()
            return None
        finally:
            if self.driver:
                self.driver.quit()

    def _initialize_driver_and_load_page(self):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        self.driver = self._setup_driver()
        self.apply_timezone_override(self.driver, self.display_timezone)
        year = str(datetime.now().year)
        url = f"{self.calendar_url}{year}"

        self.driver.get(url)
        print(f"ページにアクセス: {url}")

        # より賢い待機戦略: レンダリング完了を検出
        def wait_for_complete_render(driver, timeout=60):
            """ページの完全なレンダリングを待つ"""
            start = time.time()
            last_height = 0
            stable_count = 0
            
            while time.time() - start < timeout:
                # ページの高さをチェック
                try:
                    current_height = driver.execute_script("return document.body.scrollHeight")
                    
                    if current_height == last_height:
                        stable_count += 1
                        if stable_count >= 3:  # 3回連続で変化なし = 安定
                            print(f"レンダリング安定を検出 (高さ: {current_height}px)")
                            return True
                    else:
                        stable_count = 0
                        print(f"レンダリング中... (高さ: {current_height}px)")
                    
                    last_height = current_height
                    time.sleep(2)
                except Exception as e:
                    print(f"高さチェック中のエラー: {e}")
                    time.sleep(2)
            
            print(f"タイムアウト (最終高さ: {last_height}px)")
            return False
        
        # ページ読み込み完了を待つ
        WebDriverWait(self.driver, 30).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        print("ページ読み込み完了")
        
        # 完全なレンダリングを待つ
        if wait_for_complete_render(self.driver, timeout=60):
            print("ページレンダリング完了")
        else:
            print("警告: レンダリングタイムアウト、処理を続行")
        
        # Next.jsのハイドレーション確認
        try:
            has_next = self.driver.execute_script("""
                return !!(window.next && window.next.router);
            """)
            if has_next:
                print("Next.js検出: ハイドレーション待機中...")
                time.sleep(5)
        except:
            pass
        
        # roundContainerの存在を確認
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='fixturesResultsListing_roundContainer']"))
                )
                print("✅ ラウンドコンテナの読み込み完了")
                break
            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"試行 {attempt + 1}/{max_attempts}: ラウンドコンテナ待機中...")
                    time.sleep(10)
                else:
                    print(f"⚠️ 警告: ラウンドコンテナが見つかりませんでした")
                    # デバッグ情報
                    try:
                        cards = self.driver.find_elements(By.CSS_SELECTOR, "[class*='fixturesResultsCard']")
                        print(f"試合カード数: {len(cards)}")
                        body_text = self.driver.find_element(By.TAG_NAME, "body").text[:300]
                        print(f"Body preview: {body_text}...")
                    except Exception as debug_e:
                        print(f"デバッグ情報取得失敗: {debug_e}")
        
        # デバッグ
        html_size = len(self.driver.page_source)
        print(f"HTMLサイズ: {html_size:,} bytes")
        if html_size > 500000:
            print("✅ HTMLサイズ正常（JavaScript実行済み）")
        else:
            print(f"⚠️ HTMLサイズが小さい（期待値: 700KB以上）")

    def _class_has_prefix(self, classes, prefix: str) -> bool:
        if not classes:
            return False
        if isinstance(classes, str):
            classes = classes.split()
        return any(cls.startswith(prefix) for cls in classes)

    def _find_all_by_prefix(self, soup, tag: str, prefix: str):
        return soup.find_all(tag, class_=lambda c: self._class_has_prefix(c, prefix))

    def _find_one_by_prefix(self, soup, tag: str, prefix: str):
        return soup.find(tag, class_=lambda c: self._class_has_prefix(c, prefix))

    def _extract_matches(self, soup):
        matches = []
        round_containers = self._find_all_by_prefix(
            soup, "div", "fixturesResultsListing_roundContainer"
        )

        if not round_containers:
            print("ラウンドコンテナが見つかりません")
            return matches

        for container in round_containers:
            matches.extend(self._process_round_container(container))

        return matches

    def _process_round_container(self, container):
        """
        roundContainerは複数の日付グループを含む親コンテナ。
        各日付グループ（子div）ごとに処理する。
        """
        matches = []
        try:
            # 日付グループ（直接の子div）を取得
            date_groups = [
                child for child in container.children
                if hasattr(child, 'name') and child.name == 'div'
            ]
            
            for date_group in date_groups:
                # この日付グループの日付ヘッダーを取得
                current_date = self._get_date_from_date_group(date_group)
                if not current_date:
                    continue
                    
                print(f"日付ヘッダー: {current_date}")
                
                # この日付グループの試合カードを取得
                match_cards = self._find_all_by_prefix(
                    date_group, "article", "fixturesResultsCard_fixturesResults"
                )

                for card in match_cards:
                    match_info = self._extract_match_info(card, current_date)
                    if match_info:
                        matches.append(match_info)

        except Exception as e:
            print(f"ラウンドの処理に失敗: {str(e)}")

        return matches

    def _get_date_from_date_group(self, date_group):
        """日付グループから日付ヘッダーを取得"""
        date_element = self._find_one_by_prefix(
            date_group, "h2", "fixturesResultsListing_dateTitle"
        )
        return date_element.text.strip() if date_element else None

    def _extract_match_info(self, card, current_date):
        try:
            time_element = self._find_one_by_prefix(card, "div", "fixturesResultsCard_status")
            venue_element = self._find_one_by_prefix(card, "div", "fixturesResultsCard_stadium")
            teams = self._find_all_by_prefix(card, "span", "fixturesResultsCard_teamName")
            match_url = self._get_match_url(card)

            if len(teams) < 2:
                return None

            home_team = teams[0].text.strip()
            away_team = teams[1].text.strip()
            timezone_name = self._infer_timezone(home_team)

            # 日付と時刻を抽出: URLを優先（HTMLの表示日付が不正確なため）
            kickoff_dt = None
            
            # Method 1 (優先): URLから抽出
            if match_url:
                kickoff_dt = self._extract_datetime_from_url(match_url, timezone_name)
                if kickoff_dt:
                    print(f"  URLから日付取得: {kickoff_dt.date()}")
            
            # Method 2 (フォールバック): HTML表示テキストから抽出
            if not kickoff_dt and current_date and time_element and time_element.text.strip():
                date_text = f"{current_date} {time_element.text.strip()}"
                print(f"  日付テキスト: '{date_text}'")
                kickoff_dt = self._parse_display_datetime(date_text)
                if kickoff_dt:
                    print(f"  パース結果: {kickoff_dt}")
                    kickoff_dt = kickoff_dt.replace(tzinfo=ZoneInfo(timezone_name))
            
            # どちらも取れない場合は警告
            if not kickoff_dt:
                print(f"⚠️ 警告: {home_team} vs {away_team} の日付を取得できませんでした")

            return self.build_match(
                competition=self.competition_name,
                competition_id=self._competition_id,
                competition_id=self._get_competition_id(),
                season=str(datetime.now().year),
                round_name="",
                status="",
                kickoff=kickoff_dt,
                timezone_name=timezone_name,
                timezone_source="home_team_default",
                venue=venue_element.text.strip() if venue_element else "",
                home_team=home_team,
                away_team=away_team,
                match_url=f"{self.base_url}{match_url}" if match_url else "",
                broadcasters=[],
                source_name="Six Nations Rugby",
                source_url=f"{self.calendar_url}{datetime.now().year}",
                source_type="official",
            )
        except Exception as e:
            print(f"試合情報の抽出に失敗: {str(e)}")
            return None

    def _get_match_url(self, card):
        raw_match_url = self._find_one_by_prefix(card, "a", "fixturesResultsCard_cardLink")
        return raw_match_url.get("href") if raw_match_url else None

    def _extract_datetime_from_url(self, url: str, timezone_name: str):
        """
        URLから正確な日付と時刻を抽出
        URL例: /en/m6n/fixtures/2026/italy-v-scotland-07022026-1510/build-up
        フォーマット: DDMMYYYY-HHMM
        """
        try:
            import re
            # URLから日付部分を抽出（DDMMYYYY-HHMM形式）
            pattern = r'(\d{2})(\d{2})(\d{4})-(\d{2})(\d{2})'
            match = re.search(pattern, url)
            
            if match:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))
                hour = int(match.group(4))
                minute = int(match.group(5))
                
                # 指定されたタイムゾーンで日時を構築
                dt = datetime(year, month, day, hour, minute, 0)
                dt = dt.replace(tzinfo=ZoneInfo(timezone_name))
                return dt
            
            return None
        except Exception as e:
            print(f"URLからの日付抽出エラー: {str(e)}")
            return None

    def _parse_display_datetime(self, date_string):
        if not date_string:
            return None
        try:
            default_dt = datetime(datetime.now().year, 1, 1, 0, 0, 0)
            # dayfirst=True を指定して、日付を正しく解釈する (例: "7 Feb" -> 2月7日)
            parsed = date_parser.parse(date_string, fuzzy=True, dayfirst=True, default=default_dt)
            return parsed.replace(tzinfo=ZoneInfo(self.display_timezone))
        except (ValueError, TypeError):
            return None

    def _infer_timezone(self, home_team: str) -> str:
        team_key = home_team.strip().upper()
        if team_key in {"FRA", "FRANCE"}:
            return "Europe/Paris"
        if team_key in {"ITA", "ITALY"}:
            return "Europe/Rome"
        return "Europe/London"

    def _setup_driver(self):
        from selenium_stealth import stealth
        
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

        try:
            driver_manager = ChromeDriverManager()
            service = Service(driver_manager.install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Selenium Stealthを適用（自動的にボット検出を回避）
            stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Linux",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            driver.set_page_load_timeout(60)
            driver.implicitly_wait(10)
            return driver
        except Exception as e:
            print(f"ドライバーの初期化エラー: {str(e)}")
            raise

class SixNationsScraper(SixNationsBaseScraper):
    def __init__(self):
        super().__init__("m6n", "Six Nations", "m6n")

class SixNationsWomensScraper(SixNationsBaseScraper):
    def __init__(self):
        super().__init__("w6n", "Women's Six Nations", "w6n")

class SixNationsU20Scraper(SixNationsBaseScraper):
    def __init__(self):
        super().__init__("u6n/u20-mens", "Six Nations U20", "u6n")
