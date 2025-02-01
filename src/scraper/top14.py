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

    def _extract_match_links(self):
        try:
            WebDriverWait(self.driver, 30).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(5)
            
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            match_links = []
            links = soup.select('a.match-links__link[href*="/feuille-de-match/"]')
            
            for link in links:
                # hrefの値から正しいURLを作成
                href = link['href']
                if href.startswith('http'):
                    match_url = href
                else:
                    # 重複するドメイン部分を削除
                    href = href.replace(self.base_url, '').lstrip('/')
                    match_url = f"{self.base_url}/{href}"
                
                match_links.append({
                    'url': match_url
                })
            # デバッグ用のプリント
            print(f"取得した試合リンク数: {len(match_links)}")
            print(f"リンク: {match_url}")
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
            
            # ページの完全な読み込みを待つ
            WebDriverWait(self.driver, 30).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(5)
            
            # ページソースを取得してBeautifulSoupで解析
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')

            # 試合情報を取得
            match_info = {
                'date': self._get_match_date(soup),
                'venue': self._get_venue(soup),
                'home_team': self._get_team_name(soup, 'home'),
                'away_team': self._get_team_name(soup, 'away'),
                'broadcasters': self._get_broadcasters(soup),
                'id': self._get_match_id(url)
            }
            print(match_info)
            return match_info

        except Exception as e:
            print(f"試合詳細の抽出に失敗: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None

    def _extract_all_season_match_links(self):
        try:
            # まずページの読み込みを待つ
            WebDriverWait(self.driver, 30).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(5)
            
            # プルダウンの要素を探す
            round_select = Select(self.driver.find_element(By.ID, 'Journée'))
            round_options = [option.text for option in round_select.options]
            
            all_match_links = []
            
            for round_option in round_options:
                try:
                    # 節を選択
                    round_select = Select(self.driver.find_element(By.ID, 'Journée'))
                    round_select.select_by_visible_text(round_option)
                    time.sleep(3)
                    
                    # 試合リンクを取得
                    match_links = self._extract_match_links()
                    all_match_links.extend(match_links)
                    
                except StaleElementReferenceException:
                    time.sleep(2)
                    continue
            
            print(f"全節の試合リンク数: {len(all_match_links)}")
            return all_match_links
            
        except Exception as e:
            print(f"試合リンクの抽出に失敗: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []

    def scrape(self):
        try:
            self.driver = self._setup_driver()
            self.driver.get(self.calendar_url)
            print(f"ページにアクセス: {self.calendar_url}")

            # デバッグ
            self._extract_match_details("https://top14.lnr.fr/feuille-de-match/2024-2025/j16/10978-bayonne-bordeaux-begles")
            
            match_links = self._extract_all_season_match_links()
            if not match_links:
                return None

            matches = []
            for match_link in match_links:
                match_info = self._extract_match_details(match_link['url'])
                if match_info:
                    matches.append(match_info)

            print(f"処理した試合数: {len(matches)}")
            return matches
            
        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            return None
        finally:
            if self.driver:
                self.driver.quit()

    def _get_match_date(self, soup):
        try:
            date_element = soup.find('div', class_='title--large')
            time_element = soup.find('span', class_='match-header-broadcast__hour')
            
            if date_element and time_element:
                return f"{date_element.text.strip()} - {time_element.text.strip()}"
            return None
        except Exception as e:
            print(f"日付の取得に失敗: {str(e)}")
            return None

    def _get_venue(self, soup):
        try:
            venue_elements = soup.find_all('div', class_='match-header__info')
            if len(venue_elements) >= 2:
                return venue_elements[1].text.strip()
            return None
        except Exception as e:
            print(f"会場の取得に失敗: {str(e)}")
            return None

    def _get_team_name(self, soup, team_type):
        try:
            index = 0 if team_type == 'home' else 1

            team_elements = soup.find_all('a', class_='match-header-club__title')
            if len(team_elements) > index:
                return team_elements[index].text.strip()
            return None
        except Exception as e:
            print(f"{team_type}チーム名の取得に失敗: {str(e)}")
            return None

    def _get_broadcasters(self, soup):
        try:
            broadcaster_elements = soup.find_all('img', class_='match-header-broadcast__channel')
            broadcasters = []
            for element in broadcaster_elements:
                alt_text = element.get('alt')
                if alt_text and alt_text not in broadcasters:
                    broadcasters.append(alt_text)
            return broadcasters
        except Exception as e:
            print(f"放送局の取得に失敗: {str(e)}")
            return []

    def _get_match_id(self, url):
        try:
            # URLから試合IDを抽出 (例: /feuille-de-match/2024-2025/j16/10977-clermont-toulouse から10977を取得)
            match_id = url.split('/')[-1].split('-')[0]
            return match_id
        except Exception as e:
            print(f"試合IDの取得に失敗: {str(e)}")
            return None 