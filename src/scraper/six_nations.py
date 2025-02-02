from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper

class SixNationsScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.sixnationsrugby.com"
        self.calendar_url = f"{self.base_url}/en/m6n/fixtures/"
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
        year = str(datetime.now().year)
        url = f"{self.calendar_url}{year}"
        
        self.driver.get(url)
        print(f"ページにアクセス: {url}")
        
        WebDriverWait(self.driver, 30).until(
            lambda d: d.find_element(By.CLASS_NAME, "fixturesResultsListing_dateTitle__P0IBW").text != ""
        )        

    def _extract_matches(self, soup):
        matches = []
        round_containers = soup.find_all("div", class_="fixturesResultsListing_roundContainer__eF0xS")
        
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
            match_cards = container.find_all("div", class_="fixturesResultsCard_padding__vH5CX")
            
            for card in match_cards:
                match_info = self._extract_match_info(card, current_date)
                if match_info:
                    matches.append(match_info)
                    
        except Exception as e:
            print(f"ラウンドの処理に失敗: {str(e)}")
        
        return matches

    def _get_date_from_container(self, container):
        date_element = container.find("h2", class_="fixturesResultsListing_dateTitle__P0IBW")
        return date_element.text.strip() if date_element else None

    def _extract_match_info(self, card, current_date):
        try:
            time_element = card.find("div", class_="fixturesResultsCard_status__yNPfa")
            venue_element = card.find("div", class_="fixturesResultsCard_stadium__eRJIL")
            teams = card.find_all("span", class_="fixturesResultsCard_teamName__M7vfR")
            match_url = self._get_match_url(card)

            return {
                'date': f"{current_date} {time_element.text.strip()}" if time_element else current_date,
                'venue': venue_element.text.strip(),
                'home_team': teams[0].text.strip(),
                'away_team': teams[1].text.strip(),
                'url': self.base_url + match_url,
                'broadcasters': "",
            }
        except Exception as e:
            print(f"試合情報の抽出に失敗: {str(e)}")
            return None

    def _get_match_url(self, card):
        raw_match_url = card.find("a", class_="fixturesResultsCard_cardLink__c6BTy")
        return raw_match_url.get('href') if raw_match_url else None

    def _setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
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