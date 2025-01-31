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

class EPCRChallengeCupScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.url = "https://www.epcrugby.com/challenge-cup/matches"

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

    def _extract_nuxt_data(self, driver):
        try:
            # __NUXT_DATA__スクリプトを探す
            nuxt_data_element = driver.find_element(By.ID, "__NUXT_DATA__")
            nuxt_data_json = nuxt_data_element.get_attribute('textContent')
            
            # JSONデータをパース
            data = json.loads(nuxt_data_json)
            
            # データ構造をデバッグ出力
            print("Nuxtデータ構造:")
            for i, item in enumerate(data):
                print(f"Index {i}:", type(item))
                if isinstance(item, dict):
                    print("Keys:", list(item.keys()))
            
            # 'fixtures-and-results'を探す
            matches_data = []
            for item in data:
                if isinstance(item, dict):
                    if 'fixtures-and-results' in item:
                        matches = item['fixtures-and-results']
                        if isinstance(matches, dict) and 'matches' in matches:
                            matches_data = matches['matches']
                            break
            
            if not matches_data:
                print("試合データが見つかりませんでした")
            else:
                print(f"取得した試合数: {len(matches_data)}")
            
            return matches_data
            
        except Exception as e:
            print(f"Nuxtデータの抽出に失敗: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None

    def _parse_match_data(self, match):
        try:
            return {
                'date': match.get('date'),
                'home_team': match.get('homeTeam', {}).get('name'),
                'away_team': match.get('awayTeam', {}).get('name'),
                'venue': match.get('venue'),
                'broadcasters': [
                    {
                        'name': broadcaster.get('name'),
                        'region': broadcaster.get('region')
                    }
                    for broadcaster in match.get('broadcasters', [])
                ]
            }
        except Exception as e:
            print(f"試合データの解析に失敗: {str(e)}")
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
            
            # JavaScriptの実行完了を待機
            time.sleep(5)  # 追加：データ読み込みのための待機
            
            # Nuxtデータを抽出
            matches_data = self._extract_nuxt_data(driver)
            
            if matches_data:
                matches = []
                for match in matches_data:
                    match_info = self._parse_match_data(match)
                    if match_info:
                        matches.append(match_info)
                print(f"処理した試合数: {len(matches)}")
                return matches
            
            return None
            
        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None
        finally:
            if driver:
                driver.quit()

    def save_to_json(self, data: list, filename: str = "epcr-challenge"):
        super().save_to_json(data, filename)

class EPCRChampionsCupScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.url = "https://www.epcrugby.com/champions-cup/matches"
    
    def scrape(self):
        # 同様の実装
        pass 