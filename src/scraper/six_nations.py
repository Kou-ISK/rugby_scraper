from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import time
from .base import BaseScraper
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class SixNationsScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.sixnationsrugby.com"
        self.calendar_url = self.base_url + "/en/m6n/fixtures/"
        self.driver = None
        
    def scrape(self):
        try:
            self.driver = self._setup_driver()
            current_date = datetime.now()
            year = str(current_date.year)
            url = f"{self.calendar_url}{year}"
            
            self.driver.get(url)
            print(f"ページにアクセス: {url}")
            
            # ページの完全な読み込みを待つ
            WebDriverWait(self.driver, 30).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # テキストが読み込まれるまで待つ
            WebDriverWait(self.driver, 30).until(
                lambda d: d.find_element(By.CLASS_NAME, "fixturesResultsListing_dateTitle__P0IBW").text != ""
            )
            
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            matches = self._extract_matches(soup)
            return matches
            
        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            return None
        finally:
            if self.driver:
                self.driver.quit()

    def _extract_matches(self, soup):
        matches = []
        
        # ラウンドコンテナを取得
        round_containers = soup.find_all("div", class_="fixturesResultsListing_roundContainer__eF0xS")
        if not round_containers:
            print("ラウンドコンテナが見つかりません")
            return matches

        for round_container in round_containers:
            try:
                # 日付を取得
                date_element = round_container.find("h2", class_="fixturesResultsListing_dateTitle__P0IBW")
                if date_element:
                    current_date = date_element.text.strip()

                # 試合カードを取得
                match_cards = round_container.find_all("div", class_="fixturesResultsCard_padding__vH5CX")
                
                for card in match_cards:
                    try:
                        # 時間を取得
                        time_element = card.find("div", class_="fixturesResultsCard_status__yNPfa")
                        # 会場
                        venue_element = card.find("div", class_="fixturesResultsCard_stadium__eRJIL")
                        # チーム情報
                        teams = card.find_all("span", class_="fixturesResultsCard_teamName__M7vfR")
                        # 試合詳細URL
                        raw_match_url = card.find("a", class_="fixturesResultsCard_cardLink__c6BTy")
                        if raw_match_url:
                            match_url = raw_match_url.get('href')
                        
                        match_info = {
                            'date': f"{current_date} {time_element.text.strip()}" if time_element else current_date,
                            'venue': venue_element.text.strip(),
                            'home_team': teams[0].text.strip(),
                            'away_team': teams[1].text.strip(),
                            'url': self.base_url + match_url,
                            'broadcasters': "",
                        }
                        matches.append(match_info)
                        
                    except Exception as e:
                        print(f"試合情報の抽出に失敗: {str(e)}")
                        continue
                
            except Exception as e:
                print(f"ラウンドの処理に失敗: {str(e)}")
                continue
        
        return matches

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