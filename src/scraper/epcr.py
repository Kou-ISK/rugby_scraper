import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from .base import BaseScraper
from bs4 import BeautifulSoup

class EPCRBaseScraper(BaseScraper):
    def __init__(self, competition_type):
        super().__init__()
        self.base_url = "https://www.epcrugby.com"
        self.competition_type = competition_type
        self.url = f"{self.base_url}/{competition_type}/matches"

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
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            match_links = []
            links = soup.find_all('a', href=lambda x: x and f'/{self.competition_type}/matches/' in x)
            
            for link in links:
                match_id = link['href'].split('/')[-2]
                if match_id.isdigit():
                    match_url = f"{self.base_url}/{self.competition_type}/matches/{match_id}/news"
                    match_links.append({
                        'id': match_id,
                        'url': match_url
                    })
            
            print(f"取得した試合リンク数: {len(match_links)}")
            return match_links
            
        except Exception as e:
            print(f"試合リンクの抽出に失敗: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []

    def _extract_match_details(self, url):
        try:
            self.driver.get(url)
            print(f"試合詳細ページにアクセス: {url}")
            
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            time.sleep(2)
            
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            match_info = {}
            
            date_element = soup.select_one('header .flex:has(svg:has(path[d*="M11.99 2C6.47"]))')
            if date_element:
                date_text = date_element.text.strip()
                match_info['date'] = date_text.split('\n')[0].strip()
            
            venue_text = soup.select_one('header .flex:has(svg:has(path[d*="M12 2C8.13"]))')
            if venue_text:
                venue_lines = [v.strip() for v in venue_text.text.split('\n') if v.strip()]
                venue = next((v for v in venue_lines if not any(x in v for x in [':', '-', 'Attendance'])), '')
                match_info['venue'] = venue
            
            teams = soup.select(f'header a[href*="/{self.competition_type}/clubs/"]')
            if len(teams) >= 2:
                match_info['home_team'] = teams[0].text.strip()
                match_info['away_team'] = teams[1].text.strip()
            
            broadcaster_text = soup.select_one('header .flex:has(svg):has(path[d*="21 6H13"])')
            if broadcaster_text:
                broadcasters = broadcaster_text.text.strip().split('/')
                match_info['broadcasters'] = [b.strip() for b in broadcasters]
                
            return match_info
            
        except Exception as e:
            print(f"試合詳細の抽出に失敗: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None

    def scrape(self):
        try:
            self.driver = self._setup_driver()
            self.driver.get(self.url)
            print(f"ページにアクセス: {self.url}")
            
            WebDriverWait(self.driver, 30).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(5)

            match_links = self._extract_match_links(self.driver)
            if not match_links:
                return None

            matches = []
            for match_link in match_links:
                match_info = self._extract_match_details(match_link['url'])
                if match_info:
                    match_info['id'] = match_link['id']
                    matches.append(match_info)

            print(f"処理した試合数: {len(matches)}")
            return matches

        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            return None
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

class EPCRChampionsCupScraper(EPCRBaseScraper):
    def __init__(self):
        super().__init__('champions-cup')

class EPCRChallengeCupScraper(EPCRBaseScraper):
    def __init__(self):
        super().__init__('challenge-cup')