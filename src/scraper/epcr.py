import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import pytz
from .base import BaseScraper
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.select import Select
import json
from bs4 import BeautifulSoup

class EPCRChallengeCupScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.epcrugby.com"
        self.url = f"{self.base_url}/challenge-cup/matches"

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

    def _extract_match_links(self, driver):
        try:
            # JavaScriptの実行完了を待機
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            match_links = []
            links = soup.find_all('a', href=lambda x: x and '/challenge-cup/matches/' in x)
            
            for link in links:
                match_id = link['href'].split('/')[-2]  # URLから最後から2番目の要素を取得
                # 数字のIDのみを処理
                if match_id.isdigit():
                    match_url = f"{self.base_url}/challenge-cup/matches/{match_id}/news"
                    match_links.append({
                        'id': match_id,
                        'url': match_url
                    })
            
            print(f"取得した試合リンク数: {len(match_links)}")
            print(match_links)
            return match_links
            
        except Exception as e:
            print(f"試合リンクの抽出に失敗: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []

    def _extract_match_details(self, driver, match_id):
        try:
            # __NUXT_DATA__からマッチデータを抽出
            nuxt_data_element = driver.find_element(By.ID, "__NUXT_DATA__")
            nuxt_data_json = nuxt_data_element.get_attribute('textContent')
            data = json.loads(nuxt_data_json)

            # マッチデータを探索
            match_data = None
            for item in data:
                if isinstance(item, dict):
                    if 'match' in item:
                        match_info = item['match']
                        if str(match_info.get('id')) == str(match_id):
                            match_data = match_info
                            break
                    elif 'data' in item and isinstance(item['data'], dict) and 'match' in item['data']:
                        match_info = item['data']['match']
                        if str(match_info.get('id')) == str(match_id):
                            match_data = match_info
                            break

            if match_data:
                print({
                    'id': match_id,
                    'date': match_data.get('date'),
                    'home_team': match_data.get('homeTeam', {}).get('name'),
                    'away_team': match_data.get('awayTeam', {}).get('name'),
                    'venue': match_data.get('venue'),
                    'broadcasters': [
                        {
                            'name': broadcaster.get('name'),
                            'region': broadcaster.get('region')
                        }
                        for broadcaster in match_data.get('broadcasters', [])
                    ]
                })
                return {
                    'id': match_id,
                    'date': match_data.get('date'),
                    'home_team': match_data.get('homeTeam', {}).get('name'),
                    'away_team': match_data.get('awayTeam', {}).get('name'),
                    'venue': match_data.get('venue'),
                    'broadcasters': [
                        {
                            'name': broadcaster.get('name'),
                            'region': broadcaster.get('region')
                        }
                        for broadcaster in match_data.get('broadcasters', [])
                    ]
                }
            return None
        except Exception as e:
            print(f"試合詳細の抽出に失敗 (ID: {match_id}): {str(e)}")
            return None

    def scrape(self):
        driver = None
        try:
            driver = self._setup_driver()
            driver.get(self.url)
            print(f"ページにアクセス: {self.url}")
            
            # ページの完全な読み込みを待機
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(5)

            # 試合リンクを取得
            match_links = self._extract_match_links(driver)
            if not match_links:
                return None

            # 各試合の詳細を取得
            matches = []
            for match_link in match_links:
                print(f"試合詳細ページにアクセス: {match_link['url']}")
                driver.get(match_link['url'])
                time.sleep(3)  # ページ読み込み待機
                
                match_info = self._extract_match_details(driver, match_link['id'])
                if match_info:
                    matches.append(match_info)

            print(f"処理した試合数: {len(matches)}")
            return matches

        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            return None
        finally:
            if driver:
                driver.quit()

    def save_to_json(self, data: list, filename: str = "epcr-challenge"):
        super().save_to_json(data, filename)

    def get_match_links(self, data):
        """HTMLから試合リンクを抽出する"""
        matches = []
        
        # Beautiful Soupを使ってHTMLをパース
        soup = BeautifulSoup(data, 'html.parser')
        
        # 試合カードのリンクを探す
        match_links = soup.find_all('a', href=lambda x: x and '/challenge-cup/matches/' in x)
        
        for link in match_links:
            # 相対パスを完全なURLに変換
            match_url = f"{self.base_url}{link['href']}"
            matches.append(match_url)
        
        return matches

    def _scrape_match_details(self, driver, match_url):
        try:
            driver.get(match_url)
            # ページの読み込み完了を待機
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # APIレスポンスを待機
            time.sleep(2)
            
            # ページのHTMLを取得
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 必要なデータを抽出
            match_data = {
                'home_team': getattr(soup.select_one('.home-team-name'), 'text', '').strip(),
                'away_team': getattr(soup.select_one('.away-team-name'), 'text', '').strip(),
                'score': getattr(soup.select_one('.match-score'), 'text', '').strip(),
                'date': getattr(soup.select_one('.match-date'), 'text', '').strip()
            }
            
            return match_data
            
        except Exception as e:
            print(f"試合詳細の取得に失敗: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None

class EPCRChampionsCupScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.url = "https://www.epcrugby.com/champions-cup/matches"
    
    def scrape(self):
        # 同様の実装
        pass 