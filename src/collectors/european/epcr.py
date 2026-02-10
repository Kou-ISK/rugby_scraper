import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from ..base import BaseScraper
from bs4 import BeautifulSoup
from datetime import datetime

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
            self._prefer_selenium_manager()
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            self.apply_timezone_override(driver, "Europe/Paris")
            return driver
        except Exception as e:
            print(f"ドライバーの初期化エラー: {str(e)}")
            raise    

    def _extract_matches(self):
        matches = []
        team_logos = {}

        # Nuxtデータ（公式ページのJSON）を優先利用
        nuxt_data = None
        try:
            nuxt_data = self.driver.execute_script(
                "return (window.__NUXT__ && window.__NUXT__.data) ? window.__NUXT__.data : null;"
            )
        except Exception:
            nuxt_data = None

        fixtures_key = f"fixtures-and-results-{self.competition_type}"
        fixtures = None
        if isinstance(nuxt_data, dict):
            fixtures = nuxt_data.get(fixtures_key)

        if isinstance(fixtures, list) and fixtures:
            for fixture in fixtures:
                home_team = (fixture.get("homeTeam") or {}).get("name", "")
                away_team = (fixture.get("awayTeam") or {}).get("name", "")
                home_logo = (fixture.get("homeTeam") or {}).get("imageUrl", "")
                away_logo = (fixture.get("awayTeam") or {}).get("imageUrl", "")
                if home_team and home_logo:
                    team_logos[home_team] = {"logo_url": home_logo}
                if away_team and away_logo:
                    team_logos[away_team] = {"logo_url": away_logo}

                match_id = fixture.get("id")
                match_info = {
                    "url": f"{self.base_url}/{self.competition_type}/matches/{match_id}" if match_id else "",
                    "home_team": home_team,
                    "away_team": away_team,
                    "date": fixture.get("date"),
                    "venue": (fixture.get("venue") or {}).get("name", ""),
                    "broadcasters": fixture.get("broadcasters") or [],
                }
                matches.append(match_info)

            if team_logos:
                self._apply_official_team_logos(team_logos, self._get_competition_id())

            return matches

        # フォールバック: 既存HTML解析
        html_content = self.driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        def normalize_name(value: str) -> str:
            return re.sub(r'\\s+', ' ', (value or '').strip().lower())

        def find_logo_for_team(container, team_name: str) -> str:
            if not team_name:
                return ""
            target = normalize_name(team_name)
            for img in container.find_all('img'):
                alt = normalize_name(img.get('alt', ''))
                if not alt:
                    continue
                if alt == target or alt in target or target in alt:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy') or ""
                    if src:
                        return src
            return ""

        container = soup.find('div', class_='container max-w-7xl')
        if not container:
            return matches

        game_containers = container.find_all('div', class_='relative flex w-full card-shadow group')

        for game_container in game_containers:
            match_info = {}

            url_element = game_container.find('a', class_='absolute z-30 w-full h-full group')
            if url_element:
                match_info['url'] = f"{self.base_url}{url_element['href']}"

            inner_container = game_container.find('div', class_='w-full flex flex-col bg-white lg:pr-12 pr-8 pb-2')
            if inner_container:
                info_containers = inner_container.find_all('div', class_='flex flex-col lg:flex-row items-start lg:items-center lg:ml-10 ml-4 border-solid border-b py-1 lg:py-0')

                home_team_element = inner_container.find('div', class_='font-primary font-average lg:text-4xl text:sm uppercase flex items-center lg:ml-10 ml-4 py-4')
                away_team_element = inner_container.find('div', class_='font-primary font-average lg:text-4xl text:sm uppercase flex items-center lg:ml-10 ml-4 pb-4')

                if home_team_element and away_team_element:
                    home_team = home_team_element.text.strip()
                    away_team = away_team_element.text.strip()

                    home_team = ' '.join(home_team.split()[:-1])
                    away_team = ' '.join(away_team.split()[:-1])

                    match_info['home_team'] = home_team
                    match_info['away_team'] = away_team

                    home_logo = find_logo_for_team(game_container, home_team)
                    away_logo = find_logo_for_team(game_container, away_team)
                    if home_logo:
                        team_logos[home_team] = {"logo_url": home_logo}
                    if away_logo:
                        team_logos[away_team] = {"logo_url": away_logo}

                for info_container in info_containers:
                    date_element = info_container.select_one('.flex.items-center.uppercase')
                    if date_element:
                        date_text = date_element.text.strip()
                        match_info['date'] = self.format_date_string(date_text)

                    venue_element = info_container.select_one('.flex.items-center.lg\\:ml-4')
                    if venue_element:
                        venue_text = venue_element.text.strip()
                        match_info['venue'] = venue_text

                    broadcaster_element = info_container.select_one('.flex.items-center.lg\\:ml-4:has(svg:has(path[d*=\"21 6H13\"]))')
                    if broadcaster_element:
                        broadcaster_text = broadcaster_element.text.strip()
                        broadcasters = [b.strip() for b in broadcaster_text.split('/')]
                        match_info['broadcasters'] = broadcasters

            if match_info:
                matches.append(match_info)

        if team_logos:
            self._apply_official_team_logos(team_logos, self._get_competition_id())

        return matches
    
    def format_date_string(self, date_string):
        try:
            parts = date_string.split(", ")
            date_time = parts[1].split(" - ")
            date_part = date_time[0].split()
            time_part = date_time[1]

            day = date_part[0]
            month = date_part[1]
            year = date_part[2]

            # 月の省略形を数字に変換
            month_number = datetime.strptime(month, "%b").month

            formatted_string = f"{year}-{month_number:02}-{day} {time_part}:00"
            return formatted_string
        except (ValueError, IndexError):
            return None  # 変換できない場合

    def scrape(self):
        try:
            self.driver = self._setup_driver()
            self.driver.get(self.url)
            print(f"ページにアクセス: {self.url}")
            
            WebDriverWait(self.driver, 30).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(5)

            matches = self._extract_matches()

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
        self._competition_id = "epcr-champions"
    
    def _get_competition_id(self) -> str:
        return self._competition_id

    def scrape(self):
        raw_matches = super().scrape()
        if not raw_matches:
            return raw_matches
        
        matches = [
            self.build_match(
                competition_id="epcr-champions",
                season=str(datetime.now().year),
                round_name="",
                status="",
                kickoff=match.get("date"),
                timezone_name="UTC",
                venue=match.get("venue", ""),
                home_team=match.get("home_team", ""),
                away_team=match.get("away_team", ""),
                match_url=match.get("url", ""),
                broadcasters=match.get("broadcasters") or [],
            )
            for match in raw_matches
        ]
        
        # Assign match IDs and save
        if matches:
            matches = self.assign_match_ids(matches)
            season = str(datetime.now().year)
            filename = f"epcr-champions/{season}"
            self.save_to_json(matches, filename)
            print(f"✅ {len(matches)}試合を保存: {filename}.json")
        
        return matches

class EPCRChallengeCupScraper(EPCRBaseScraper):
    def __init__(self):
        super().__init__('challenge-cup')
        self._competition_id = "epcr-challenge"
    
    def _get_competition_id(self) -> str:
        return self._competition_id

    def scrape(self):
        raw_matches = super().scrape()
        if not raw_matches:
            return raw_matches
        
        matches = [
            self.build_match(
                competition_id="epcr-challenge",
                season=str(datetime.now().year),
                round_name="",
                status="",
                kickoff=match.get("date"),
                timezone_name="UTC",
                venue=match.get("venue", ""),
                home_team=match.get("home_team", ""),
                away_team=match.get("away_team", ""),
                match_url=match.get("url", ""),
                broadcasters=match.get("broadcasters") or [],
            )
            for match in raw_matches
        ]
        
        # Assign match IDs and save
        if matches:
            matches = self.assign_match_ids(matches)
            season = str(datetime.now().year)
            filename = f"epcr-challenge/{season}"
            self.save_to_json(matches, filename)
            print(f"✅ {len(matches)}試合を保存: {filename}.json")
        
        return matches
