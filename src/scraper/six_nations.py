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
    def __init__(self, competition_path: str, competition_name: str):
        super().__init__()
        self.base_url = "https://www.sixnationsrugby.com"
        self.calendar_url = f"{self.base_url}/en/{competition_path}/fixtures/"
        self.competition_name = competition_name
        self.display_timezone = "Europe/London"
        self.driver = None

    def scrape(self):
        try:
            self._initialize_driver_and_load_page()
            matches = self._extract_matches(BeautifulSoup(self.driver.page_source, 'html.parser'))
            return matches
        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            return None
        finally:
            if self.driver:
                self.driver.quit()

    def _initialize_driver_and_load_page(self):
        self.driver = self._setup_driver()
        self.apply_timezone_override(self.driver, self.display_timezone)
        year = str(datetime.now().year)
        url = f"{self.calendar_url}{year}"

        self.driver.get(url)
        print(f"ページにアクセス: {url}")

        WebDriverWait(self.driver, 30).until(
            lambda d: d.find_element(By.TAG_NAME, "body").text.strip() != ""
        )

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
        matches = []
        try:
            current_date = self._get_date_from_container(container)
            match_cards = self._find_all_by_prefix(
                container, "div", "fixturesResultsCard_padding"
            )

            for card in match_cards:
                match_info = self._extract_match_info(card, current_date)
                if match_info:
                    matches.append(match_info)

        except Exception as e:
            print(f"ラウンドの処理に失敗: {str(e)}")

        return matches

    def _get_date_from_container(self, container):
        date_element = self._find_one_by_prefix(
            container, "h2", "fixturesResultsListing_dateTitle"
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

            # URLから正確な日付と時刻を抽出（URLが最も信頼できる情報源）
            kickoff_dt = None
            if match_url:
                kickoff_dt = self._extract_datetime_from_url(match_url, timezone_name)
            
            # URLから日付が取れない場合のフォールバック
            if not kickoff_dt:
                date_text = current_date
                if time_element and time_element.text.strip():
                    date_text = f"{current_date} {time_element.text.strip()}"
                kickoff_dt = self._parse_display_datetime(date_text)
                if kickoff_dt and timezone_name:
                    try:
                        kickoff_dt = kickoff_dt.astimezone(ZoneInfo(timezone_name))
                    except Exception:
                        pass

            return self.build_match(
                competition=self.competition_name,
                competition_id="",
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
            parsed = date_parser.parse(date_string, fuzzy=True, default=default_dt)
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
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        try:
            driver_manager = ChromeDriverManager()
            service = Service(driver_manager.install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            return driver
        except Exception as e:
            print(f"ドライバーの初期化エラー: {str(e)}")
            raise

class SixNationsScraper(SixNationsBaseScraper):
    def __init__(self):
        super().__init__("m6n", "Six Nations")

class SixNationsWomensScraper(SixNationsBaseScraper):
    def __init__(self):
        super().__init__("w6n", "Women's Six Nations")

class SixNationsU20Scraper(SixNationsBaseScraper):
    def __init__(self):
        super().__init__("u6n/u20-mens", "Six Nations U20")
