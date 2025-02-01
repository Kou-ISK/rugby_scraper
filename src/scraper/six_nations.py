import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from .base import BaseScraper

class SixNationsScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.sixnationsrugby.com"
        self.calendar_url = self.base_url + "/en/m6n/fixtures/"
        
    def scrape(self):
        try:
            all_matches = []
            # 現在の日付を取得
            current_date = datetime.now()
            year = str(current_date.year)

            url = f"{self.calendar_url}{year}"
            
            response = requests.get(url)
            if response.status_code != 200:
                print(f"ページの取得に失敗: {url}")
            
            soup = BeautifulSoup(response.content, 'html.parser')

            matches = self._extract_matches(soup)
            all_matches.extend(matches)
            
            return all_matches
            
        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None

    def _extract_matches(self, soup):
        matches = []
        current_date = None
        
        # 試合カードを直接取得
        match_cards = soup.find_all("article", class_="fixturesResultsCard_fixturesResults__qdiE7")
        
        for card in match_cards:
            try:
                # 日付を取得（前の要素から）
                date_element = card.find_previous("h2", class_="fixturesResultsListing_dateTitle__P0IBW")

                # 時間
                time_element = card.find("div", class_="fixturesResultsCard_status__yNPfa")

                # 会場
                venue_element = card.find("div", class_="fixturesResultsCard_stadium__eRJIL")

                # チーム情報
                teams = card.find_all('span', class_="fixturesResultsCard_teamName__M7vfR")

                # 試合詳細URL
                match_url = card.find("a", class_="fixturesResultsCard_cardLink__c6BTy")['href']
                
                # 日時を解析してdatetimeオブジェクトに変換
                try:
                    match_datetime = date_element.text.strip() + " " + time_element.text.strip()
                except ValueError as e:
                    print(f"日時の解析に失敗: {str(e)}")
                    continue
                
                match_info = {
                    'date': match_datetime,
                    'venue': venue_element.text.strip(),
                    'home_team': teams[0].text.strip(),
                    'away_team': teams[1].text.strip(),
                    'broadcasters': "",
                    'url': self.base_url + match_url
                }

                print(match_info)
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