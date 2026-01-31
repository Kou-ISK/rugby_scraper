import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from .base import BaseScraper

class LeagueOneScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://league-one.jp"
        self.calendar_url = self.base_url + "/schedule/"
        
    def scrape(self):
        try:
            all_matches = []
            # 現在の日付を取得
            current_date = datetime.now()
            # 12月以降は次のシーズン、1月は現在のシーズン
            year = str(current_date.year - 1) if current_date.month < 12 else str(current_date.year)
            
            url = f"{self.calendar_url}?year={year}"
                
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            self.current_url = url
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                print(f"ページの取得に失敗: {url}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            matches = self._extract_matches(soup)
            all_matches.extend(matches)
            
            print(f"取得した試合数: {len(all_matches)}")
            return all_matches
            
        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None

    def _extract_matches(self, soup):
        matches = []
        
        # 試合カードのコンテナを取得
        match_containers = soup.find_all('div', class_='c-schedule')
        
        for container in match_containers:
            try:
                # 試合情報の取得
                date_element = container.find('div', class_='datetime')
                venue_element = container.find('p', class_='place')
                teams = container.find_all('li', class_=['home', 'away'])
                broadcasters = container.find("dl", class_="broadcast")
                
                if not all([date_element, venue_element, teams]):
                    continue
                
                kickoff = self.format_date_string(self._format_date(date_element))
                match_info = self.build_match(
                    competition="Japan Rugby League One",
                    competition_id="",
                    season=str(datetime.now().year),
                    round_name="",
                    status="",
                    kickoff=kickoff,
                    timezone_name="Asia/Tokyo",
                    timezone_source="competition_default",
                    venue=venue_element.text.strip(),
                    home_team=self._get_team_name(teams[0]) or "",
                    away_team=self._get_team_name(teams[1]) or "",
                    match_url=self._get_match_url(container) or "",
                    broadcasters=self._get_broadcasters(broadcasters),
                    source_name="Japan Rugby League One",
                    source_url=self.current_url if hasattr(self, "current_url") else self.calendar_url,
                    source_type="official",
                )
                matches.append(match_info)
                
            except Exception as e:
                print(f"試合情報の抽出に失敗: {str(e)}")
                continue
        
        return matches

    def _format_date(self, date_element):
        try:
            date = date_element.find('p', class_='date').text.strip()
            time = date_element.find('p', class_='time').text.strip()
            return f"{date} {time}"
        except:
            return None

    def _get_team_name(self, team_element):
        try:
            name_element = team_element.find('p', class_='name only-pc')
            return name_element.text.strip() if name_element else None
        except:
            return None

    def _get_match_url(self, container):
        try:
            detail_link = container.find('a', class_='btn-match-detail')
            if detail_link and 'href' in detail_link.attrs:
                return f"{self.base_url}{detail_link['href']}"
            return None
        except Exception as e:
            print(f"URLの取得に失敗: {str(e)}")
            return None

    def _get_venue(self, container):
        try:
            venue_element = container.find('p', href='place').find('a')
            return venue_element.text.strip() if venue_element else None
        except Exception as e:
            print(f"会場の取得に失敗: {str(e)}")
            return None

    def _get_broadcasters(self, broadcasters):
        try:
            if not broadcasters:
                return []
            
            # 放送局のリストを取得
            broadcaster_list = broadcasters.find('dd').find_all('a')
            result = []
            
            for element in broadcaster_list:
                text = element.text.strip()
                if text and text not in result and text != "／":
                    result.append(text)
                
            return result
        
        except Exception as e:
            print(f"放送局の取得に失敗: {str(e)}")
            return []
        
    def format_date_string(self, date_string):
        try:
            parts = date_string.split()
            date_part = parts[0].split(".")
            time_part = parts[2]

            month = int(date_part[0])
            day = int(date_part[1])

            # 現在の日付を取得
            current_date = datetime.now()
            current_year = current_date.year

            # シーズン開始月
            season_start_month = 12

            # シーズン開始月より前の場合は今年、それ以降は去年
            year = current_year -1 if month >= season_start_month else current_year

            formatted_string = f"{year}-{month:02}-{day} {time_part}:00"
            return formatted_string
        except (ValueError, IndexError):
            return None  # 変換できない場合
