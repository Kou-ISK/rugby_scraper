import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from .base import BaseScraper
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException

class Top14Scraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://top14.lnr.fr"
        self.calendar_url = f"{self.base_url}/calendrier-et-resultats"
        self.driver = None

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

    def _extract_matches(self, soup):
        matches = []
        
        # 日付を取得
        calendar_inner = soup.find('div', class_='calendar-results__inner')
        if not calendar_inner:
            return matches
        
        current_date = None
        
        # calendar_inner内のすべての要素を順番に処理
        for element in calendar_inner.children:
            if not hasattr(element, 'get'):  # NavigableStringをスキップ
                continue
            
            # 日付要素の場合
            if element.get('class') and 'calendar-results__fixture-date' in element.get('class'):
                current_date = element.text.strip()
            
            # 試合要素の場合
            elif element.get('class') and 'calendar-results__line' in element.get('class'):
                if not current_date:
                    continue
                    
                match_info = {}
                match_info['date'] = current_date
                
                # 時刻を取得
                time_element = element.select_one('.match-line__time')
                if time_element:
                    match_info['time'] = time_element.text.strip()
                
                # チーム名を取得
                home_team = element.select_one('.club-line--reversed .club-line__name')
                away_team = element.select_one('.club-line--table-format:not(.club-line--reversed) .club-line__name')
                
                if home_team and away_team:
                    match_info['home_team'] = home_team.text.strip()
                    match_info['away_team'] = away_team.text.strip()
                
                # 放送局を取得
                broadcasters = []
                broadcaster_elements = element.select('.match-line__broadcaster-link img')
                for broadcaster in broadcaster_elements:
                    broadcasters.append(broadcaster['alt'])
                
                if broadcasters:
                    match_info['broadcasters'] = broadcasters
                
                # URLを取得
                match_link = element.select_one('.match-links__link[href*="/feuille-de-match/"]')
                if match_link:
                    match_info['url'] = f"{self.base_url}{match_link['href']}"
                
                matches.append(match_info)
                print(match_info)
        
        return matches

    def scrape(self):
        try:
            self.driver = self._setup_driver()
            self.driver.get(self.calendar_url)
            print(f"ページにアクセス: {self.calendar_url}")
            
            # まずページの読み込みを待つ
            WebDriverWait(self.driver, 30).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # プルダウンの要素を探す
            round_select = Select(self.driver.find_element(By.ID, 'Journée'))
            round_options = [option.text for option in round_select.options]
            
            all_matches = []
            
            for round_option in round_options:
                try:
                    # 節を選択
                    round_select = Select(self.driver.find_element(By.ID, 'Journée'))
                    round_select.select_by_visible_text(round_option)
                    time.sleep(3)
                    
                    # ページソースを取得してBeautifulSoupで解析
                    html_content = self.driver.page_source
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 試合情報を直接取得
                    matches = self._extract_matches(soup)
                    all_matches.extend(matches)
                    
                except StaleElementReferenceException:
                    time.sleep(2)
                    continue
            
            print(f"処理した試合数: {len(all_matches)}")
            return all_matches
            
        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            return None
        finally:
            if self.driver:
                self.driver.quit()