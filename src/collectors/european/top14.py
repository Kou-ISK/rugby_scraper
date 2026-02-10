import re
import unicodedata
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from ..base import BaseScraper

class Top14Scraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://top14.lnr.fr"
        self.calendar_url = f"{self.base_url}/calendrier-et-resultats"

    def _extract_matches(self, soup):
        matches = []
        # 公式ロゴを先に取得
        team_logos = {}
        for img in soup.select('img[src*="cdn.lnr.fr/club"]'):
            team_name = (img.get('alt') or '').strip()
            logo_url = (img.get('src') or '').strip()
            if team_name and logo_url:
                team_logos[team_name] = {"logo_url": logo_url}
        if team_logos:
            self._apply_official_team_logos(team_logos, "t14")
        
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
                    
                # 時刻を取得
                time_element = element.select_one('.match-line__time')
                time_text = time_element.text.strip() if time_element else None
                kickoff = self._format_date_time(current_date, time_text)
                
                # チーム名を取得
                home_team = element.select_one('.club-line--reversed .club-line__name')
                away_team = element.select_one('.club-line--table-format:not(.club-line--reversed) .club-line__name')
                
                if home_team and away_team:
                    home_team_name = home_team.text.strip()
                    away_team_name = away_team.text.strip()
                else:
                    continue  # チーム名が取得できない場合はスキップ
                
                # match_idとvenueを取得
                match_id = ""
                venue = ""
                match_link = element.select_one('.match-links__link[href*="/feuille-de-match/"]')
                if match_link:
                    href = match_link['href']
                    # URLからmatch_idを抽出 (例: /feuille-de-match/2025-2026/j1/11307-clermont-toulouse)
                    match_parts = href.split('/')[-1].split('-')
                    if len(match_parts) > 0 and match_parts[0].isdigit():
                        match_id = match_parts[0]
                
                # 会場情報を取得
                venue_element = element.select_one('.match-line__venue')
                if venue_element:
                    venue = venue_element.text.strip()
                
                # ラウンド情報を取得（現在の日付から推測）
                round_name = ""
                try:
                    if current_date and time_text:
                        # 日付から年を取得してシーズンを判定
                        current_year = datetime.now().year
                        round_name = f"Journée {current_year}"
                except:
                    pass
                
                # 放送局を取得
                broadcasters = []
                broadcaster_elements = element.select('.match-line__broadcaster-link img')
                for broadcaster in broadcaster_elements:
                    broadcasters.append(broadcaster['alt'])
                
                if broadcasters:
                    match_broadcasters = broadcasters
                else:
                    match_broadcasters = []
                
                # URLを取得
                match_link = element.select_one('.match-links__link[href*="/feuille-de-match/"]')
                if match_link:
                    href = match_link['href']
                    # 既にフルURLの場合はそのまま使用、相対パスの場合はbase_urlを結合
                    if href.startswith('http'):
                        match_url = href
                    else:
                        match_url = f"{self.base_url}{href}"
                else:
                    match_url = ""

                match_info = self.build_match(
                    competition_id="t14",
                    season=f"{datetime.now().year}-{datetime.now().year + 1}",
                    round_name=round_name,
                    status="scheduled",
                    kickoff=kickoff,
                    timezone_name="Europe/Paris",
                    venue=venue,
                    home_team=home_team_name,
                    away_team=away_team_name,
                    match_url=match_url,
                    broadcasters=match_broadcasters,
                    match_id=match_id,
                )

                matches.append(match_info)
        
        return matches

    def scrape(self):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(self.calendar_url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            matches = self._extract_matches(soup)
            print(f"処理した試合数: {len(matches)}")
            return matches

        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            return None

    def _format_date_time(self, date_text, time_text):
        if not date_text:
            return None
        normalized = unicodedata.normalize("NFKD", date_text).encode("ascii", "ignore").decode("ascii")
        day_match = re.search(r"\\b(\\d{1,2})\\b", normalized)
        month_match = re.search(r"\\b(janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)\\b", normalized)
        if not day_match or not month_match:
            return None

        day = int(day_match.group(1))
        month_name = month_match.group(1)
        month_map = {
            "janvier": 1,
            "fevrier": 2,
            "mars": 3,
            "avril": 4,
            "mai": 5,
            "juin": 6,
            "juillet": 7,
            "aout": 8,
            "septembre": 9,
            "octobre": 10,
            "novembre": 11,
            "decembre": 12,
        }
        month = month_map.get(month_name)
        if not month:
            return None

        year = self._infer_season_year(month)
        time_value = self._normalize_time(time_text) or "00:00"
        return f"{year}-{month:02}-{day:02} {time_value}:00"

    def _normalize_time(self, time_text):
        if not time_text:
            return None
        normalized = time_text.strip().lower().replace("h", ":")
        if re.match(r"^\\d{1,2}:\\d{2}$", normalized):
            return normalized
        if re.match(r"^\\d{1,2}:$", normalized):
            return normalized + "00"
        if re.match(r"^\\d{1,2}$", normalized):
            return normalized + ":00"
        return None

    def _infer_season_year(self, month):
        now = datetime.now()
        season_start_month = 8
        if month >= season_start_month and now.month < season_start_month:
            return now.year - 1
        if month < season_start_month and now.month >= season_start_month:
            return now.year + 1
        return now.year
