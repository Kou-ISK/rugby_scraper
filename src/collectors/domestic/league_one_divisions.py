import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from typing import List, Dict, Any
from ..base import BaseScraper

class LeagueOneDivisionsScraper(BaseScraper):
    """Japan Rugby League One scraper with Division support.
    
    Division 1, 2, 3を別ファイルとして出力:
    - jrlo_div1/2026.json
    - jrlo_div2/2026.json
    - jrlo_div3/2026.json
    """
    
    # Division 1のチーム（2025-2026シーズン）
    DIVISION_1_TEAMS = {
        "埼玉ワイルドナイツ", "東京サンゴリアス", "クボタスピアーズ船橋・東京ベイ",
        "東芝ブレイブルーパス東京", "トヨタヴェルブリッツ", "ブラックラムズ東京",
        "コベルコ神戸スティーラーズ", "横浜キヤノンイーグルス", "静岡ブルーレヴズ",
        "花園近鉄ライナーズ", "三重ホンダヒート", "レッドハリケーンズ大阪",
    }
    
    # Division 2のチーム
    DIVISION_2_TEAMS = {
        "グリーンロケッツ東葛", "ルリーロ福岡", "クリタウォーターガッシュ昭島",
        "浦安D-Rocks", "三菱重工相模原ダイナボアーズ", "ヤクルトレビンズ戸田",
        "スカイアクティブズ広島", "九州電力キューデンヴォルテクス",
        # 2025-2026シーズン追加チーム
        "日本製鉄釜石シーウェイブス", "日野レッドドルフィンズ",
        "豊田自動織機シャトルズ愛知", "清水建設江東ブルーシャークス",
    }
    
    # Division 3のチーム
    DIVISION_3_TEAMS = {
        "NTTドコモレッドハリケーンズ大阪", "NTT-Com SHINING ARCS",
        "中国電力レッドレグリオンズ", "ながと BLUE ANGELS",
        "狭山セコムラガッツ",  # 2025-2026シーズン追加
    }
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://league-one.jp"
        self.calendar_url = self.base_url + "/schedule/"
        
    def _get_division(self, team_name: str) -> str:
        """チーム名からDivisionを判定
        
        Args:
            team_name: チーム名
            
        Returns:
            "div1", "div2", "div3", or "" (不明)
        """
        if team_name in self.DIVISION_1_TEAMS:
            return "div1"
        elif team_name in self.DIVISION_2_TEAMS:
            return "div2"
        elif team_name in self.DIVISION_3_TEAMS:
            return "div3"
        else:
            return ""
        
    def scrape(self):
        try:
            # 全試合を取得
            all_matches = []
            current_date = datetime.now()
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
            
            # Divisionごとに分類（両チームが同じDivisionの試合のみ）
            div1_matches = []
            div2_matches = []
            div3_matches = []
            unknown_matches = []
            cross_division_matches = []  # Division間の試合
            
            for match in all_matches:
                home_team = match.get("home_team", "")
                away_team = match.get("away_team", "")
                
                home_div = self._get_division(home_team)
                away_div = self._get_division(away_team)
                
                # 両チームが同じDivisionの試合のみを抽出
                if home_div and away_div and home_div == away_div:
                    if home_div == "div1":
                        match["competition_id"] = "jrlo_div1"
                        div1_matches.append(match)
                    elif home_div == "div2":
                        match["competition_id"] = "jrlo_div2"
                        div2_matches.append(match)
                    elif home_div == "div3":
                        match["competition_id"] = "jrlo_div3"
                        div3_matches.append(match)
                elif home_div and away_div and home_div != away_div:
                    # Division間の交流戦
                    cross_division_matches.append(match)
                else:
                    # どちらかのチームが未定義
                    unknown_matches.append(match)
            
            # team_idを設定（BaseScraperの_resolve_team_idを使用）
            for match in div1_matches + div2_matches + div3_matches:
                comp_id = match.get("competition_id", "jrlo")
                home_team = match.get("home_team", "")
                away_team = match.get("away_team", "")
                
                # BaseScraperの_resolve_team_id（自動連番採番）
                match["home_team_id"] = self._resolve_team_id(home_team, comp_id)
                match["away_team_id"] = self._resolve_team_id(away_team, comp_id)
            
            # ログ出力
            print(f"\n=== JRLO Division分類結果 ===")
            print(f"Division 1: {len(div1_matches)}試合")
            print(f"Division 2: {len(div2_matches)}試合")
            print(f"Division 3: {len(div3_matches)}試合")
            if cross_division_matches:
                print(f"⚠️  Division間交流戦: {len(cross_division_matches)}試合（スキップ）")
                for m in cross_division_matches[:5]:  # 最初の5試合のみ表示
                    home_div = self._get_division(m.get("home_team", ""))
                    away_div = self._get_division(m.get("away_team", ""))
                    print(f"   - {m.get('home_team', '')} ({home_div}) vs {m.get('away_team', '')} ({away_div})")
            if unknown_matches:
                print(f"❌ Division不明（未定義チーム含む）: {len(unknown_matches)}試合")
                unknown_teams = set()
                for m in unknown_matches[:5]:
                    home = m.get("home_team", "")
                    away = m.get("away_team", "")
                    home_div = self._get_division(home)
                    away_div = self._get_division(away)
                    if not home_div:
                        unknown_teams.add(home)
                    if not away_div:
                        unknown_teams.add(away)
                    print(f"   - {home} ({home_div or 'UNKNOWN'}) vs {away} ({away_div or 'UNKNOWN'})")
                if unknown_teams:
                    print(f"   未定義チーム: {', '.join(sorted(unknown_teams))}")
                unknown_teams = set()
                for m in unknown_matches[:5]:  # 最初の5試合のみ
                    unknown_teams.add(m.get("home_team", ""))
                    unknown_teams.add(m.get("away_team", ""))
                if unknown_teams:
                    print(f"   未定義チーム例: {', '.join(sorted(unknown_teams)[:3])}")
            
            # match_idを割り当て
            div1_matches = self.assign_match_ids(div1_matches)
            div2_matches = self.assign_match_ids(div2_matches)
            div3_matches = self.assign_match_ids(div3_matches)
            
            # ファイル保存
            season = str(int(year) + 1)  # 2025年開始 → 2026シーズン
            if div1_matches:
                self.save_to_json(div1_matches, f"jrlo_div1/{season}")
            if div2_matches:
                self.save_to_json(div2_matches, f"jrlo_div2/{season}")
            if div3_matches:
                self.save_to_json(div3_matches, f"jrlo_div3/{season}")
            
            return {
                "div1": div1_matches,
                "div2": div2_matches,
                "div3": div3_matches,
                "unknown": unknown_matches,
            }
            
        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None

    def _extract_matches(self, soup) -> List[Dict[str, Any]]:
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
                
                if not all([date_element, teams]) or len(teams) < 2:
                    continue
                
                # venue情報を安全に取得
                venue_text = ""
                if venue_element:
                    venue_text = venue_element.text.strip()
                else:
                    venue_text = self._get_venue(container) or ""
                
                home_team = self._get_team_name(teams[0]) or ""
                away_team = self._get_team_name(teams[1]) or ""
                
                kickoff = self.format_date_string(self._format_date(date_element))
                
                # competition_idは後でdivisionに応じて変更
                # team_idは後で設定（Division分類後に登録）
                match_info = self.build_match(
                    competition_id="jrlo",  # 仮ID
                    season=str(datetime.now().year),
                    round_name="",
                    status="scheduled",
                    kickoff=kickoff,
                    timezone_name="Asia/Tokyo",
                    venue=venue_text,
                    home_team=home_team,
                    away_team=away_team,
                    match_url=self._get_match_url(container) or "",
                    broadcasters=self._get_broadcasters(broadcasters),
                    home_team_id="",  # 後で設定
                    away_team_id="",  # 後で設定
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
            venue_element = container.find('p', class_='place')
            if venue_element:
                link = venue_element.find('a')
                return link.text.strip() if link else venue_element.text.strip()
            return None
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
            year = current_year - 1 if month >= season_start_month else current_year

            formatted_string = f"{year}-{month:02}-{day} {time_part}:00"
            return formatted_string
        except (ValueError, IndexError):
            return None
