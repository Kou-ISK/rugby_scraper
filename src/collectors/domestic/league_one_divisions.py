import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time
from typing import List, Dict, Any
from urllib.parse import urljoin
from zoneinfo import ZoneInfo
from ..base import BaseScraper

class LeagueOneDivisionsScraper(BaseScraper):
    """Japan Rugby League One scraper with Division support.
    
    Division 1, 2, 3を別ファイルとして出力:
    - jrlo-div1/2026.json
    - jrlo-div2/2026.json
    - jrlo-div3/2026.json
    """
    
    # Division 1のチーム（2025-2026シーズン）
    DIVISION_1_TEAMS = {
        "埼玉ワイルドナイツ", "東京サンゴリアス", "クボタスピアーズ船橋・東京ベイ",
        "東芝ブレイブルーパス東京", "トヨタヴェルブリッツ", "ブラックラムズ東京",
        "コベルコ神戸スティーラーズ", "横浜キヤノンイーグルス", "静岡ブルーレヴズ",
        "花園近鉄ライナーズ", "三重ホンダヒート", "レッドハリケーンズ大阪",
        "三菱重工相模原ダイナボアーズ", "浦安D-Rocks",
    }
    
    # Division 2のチーム
    DIVISION_2_TEAMS = {
        "グリーンロケッツ東葛", "ルリーロ福岡", "クリタウォーターガッシュ昭島",
        "ヤクルトレビンズ戸田",
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
        self._team_logos_cache_by_comp = {}
        self.jst = ZoneInfo("Asia/Tokyo")
        self._last_print_request_at = 0.0
        self._print_request_interval_seconds = 1.0
        
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

    def _infer_division_from_text(self, text: str) -> str:
        if not text:
            return ""
        if "ディビジョン1" in text or "D1" in text:
            return "div1"
        if "ディビジョン2" in text or "D2" in text:
            return "div2"
        if "ディビジョン3" in text or "D3" in text:
            return "div3"
        return ""

    def _find_division_near_container(self, container) -> str:
        if not container:
            return ""
        # 祖先コンテナ内の「ディビジョン」表記を優先
        ancestor = container
        for _ in range(6):
            if not ancestor:
                break
            text = ancestor.get_text(" ", strip=True)
            div = self._infer_division_from_text(text)
            if div:
                return div
            ancestor = ancestor.parent

        # 直近の「ディビジョン」表記を持つ要素を探索
        node = container
        for _ in range(12):
            node = node.find_previous(["div", "p", "h2", "h3", "h4", "span"])
            if not node:
                break
            text = node.get_text(strip=True)
            div = self._infer_division_from_text(text)
            if div:
                return div
        return ""

    def _is_placeholder_team(self, team_name: str) -> bool:
        if not team_name:
            return False
        placeholders = [
            "リーグ戦",
            "準々決勝",
            "準決勝",
            "決勝",
        ]
        if any(p in team_name for p in placeholders):
            return True
        return False
        
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

            # 公式ロゴの反映
            for comp_id, team_logos in self._team_logos_cache_by_comp.items():
                self._apply_official_team_logos(team_logos, comp_id)
            
            # Divisionごとに分類（両チームが同じDivisionの試合のみ）
            div1_matches = []
            div2_matches = []
            div3_matches = []
            unknown_matches = []
            cross_division_matches = []  # Division間の試合（期待しないがログ用）
            
            for match in all_matches:
                home_team = match.get("home_team", "")
                away_team = match.get("away_team", "")
                
                # matchレベルで判定済みのdivisionがあれば優先
                match_div = match.get("division", "")
                home_div = self._get_division(home_team)
                away_div = self._get_division(away_team)
                # プレースホルダー名はDivision1扱い（ヘッダー不明時のフォールバック）
                if not home_div and self._is_placeholder_team(home_team):
                    home_div = "div1"
                if not away_div and self._is_placeholder_team(away_team):
                    away_div = "div1"

                if match_div:
                    home_div = match_div
                    away_div = match_div
                else:
                    # 片方だけ判定できた場合はそのdivisionで統一（交流戦は無い前提）
                    if home_div and not away_div:
                        away_div = home_div
                    if away_div and not home_div:
                        home_div = away_div
                
                # 両チームが同じDivisionの試合のみを抽出
                if home_div and away_div and home_div == away_div:
                    if home_div == "div1":
                        match["competition_id"] = "jrlo-div1"
                        div1_matches.append(match)
                    elif home_div == "div2":
                        match["competition_id"] = "jrlo-div2"
                        div2_matches.append(match)
                    elif home_div == "div3":
                        match["competition_id"] = "jrlo-div3"
                        div3_matches.append(match)
                elif home_div and away_div and home_div != away_div:
                    # Division間の交流戦（想定外）→ home_divで扱う
                    cross_division_matches.append(match)
                    match["competition_id"] = f"jrlo-{home_div}"
                    if home_div == "div1":
                        div1_matches.append(match)
                    elif home_div == "div2":
                        div2_matches.append(match)
                    elif home_div == "div3":
                        div3_matches.append(match)
                else:
                    # どちらかのチームが未定義
                    unknown_matches.append(match)
            
            # team_idを設定（BaseScraperの_resolve_team_idを使用）
            for match in div1_matches + div2_matches + div3_matches:
                comp_id = match.get("competition_id", "jrlo")
                home_team = match.get("home_team", "")
                away_team = match.get("away_team", "")

                # プレースホルダー名はteam_idを空にする
                if self._is_placeholder_team(home_team):
                    match["home_team_id"] = ""
                else:
                    match["home_team_id"] = self._resolve_team_id(home_team, comp_id)
                if self._is_placeholder_team(away_team):
                    match["away_team_id"] = ""
                else:
                    match["away_team_id"] = self._resolve_team_id(away_team, comp_id)
                
                # placeholderを含む場合は名寄せしない

            # ログ出力
            print(f"\n=== JRLO Division分類結果 ===")
            print(f"Division 1: {len(div1_matches)}試合")
            print(f"Division 2: {len(div2_matches)}試合")
            print(f"Division 3: {len(div3_matches)}試合")
            if cross_division_matches:
                print(f"⚠️  Division間交流戦: {len(cross_division_matches)}試合（確認要）")
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
                self.save_to_json(div1_matches, f"jrlo-div1/{season}")
            if div2_matches:
                self.save_to_json(div2_matches, f"jrlo-div2/{season}")
            if div3_matches:
                self.save_to_json(div3_matches, f"jrlo-div3/{season}")
            
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

                # 公式ロゴURL取得（チーム要素内のimg）
                home_logo = self._get_team_logo_url(teams[0])
                away_logo = self._get_team_logo_url(teams[1])
                home_div = self._get_division(home_team)
                away_div = self._get_division(away_team)
                if home_logo and home_div:
                    comp_id = f"jrlo-{home_div}"
                    self._team_logos_cache_by_comp.setdefault(comp_id, {})[home_team] = {"logo_url": home_logo}
                if away_logo and away_div:
                    comp_id = f"jrlo-{away_div}"
                    self._team_logos_cache_by_comp.setdefault(comp_id, {})[away_team] = {"logo_url": away_logo}
                
                raw_date = self._format_date(date_element)
                match_url = self._get_match_url(container) or ""
                kickoff = self.parse_kickoff_datetime(raw_date, match_url)
                schedule_details = self._extract_schedule_details(container)
                
                # divisionを事前に推定
                inferred_div = self._find_division_near_container(container)
                comp_id = f"jrlo-{inferred_div}" if inferred_div else "jrlo"

                # competition_idは後でdivisionに応じて変更
                # team_idは後で設定（Division分類後に登録）
                match_info = self.build_match(
                    competition_id=comp_id,  # 仮ID
                    season=str(datetime.now().year),
                    round_name=schedule_details.get("round", ""),
                    status=schedule_details.get("status", "scheduled"),
                    kickoff=kickoff,
                    timezone_name="Asia/Tokyo",
                    venue=venue_text,
                    home_team=home_team,
                    away_team=away_team,
                    match_url=match_url,
                    broadcasters=self._get_broadcasters(broadcasters),
                    home_team_id="",  # 後で設定
                    away_team_id="",  # 後で設定
                )
                match_info["division"] = inferred_div
                self._apply_optional_match_details(match_info, schedule_details)
                matches.append(match_info)
                
            except Exception as e:
                print(f"試合情報の抽出に失敗: {str(e)}")
                continue
        
        return matches

    def _extract_schedule_details(self, container) -> Dict[str, Any]:
        details: Dict[str, Any] = {"status": "scheduled"}

        title_element = container.find("h3", class_="ttl")
        title_text = title_element.get_text(" ", strip=True) if title_element else ""
        details.update(self._parse_title_metadata(title_text))

        detail_link = container.find("a", class_="btn-match-detail")
        detail_text = detail_link.get_text(" ", strip=True) if detail_link else ""
        details["status"] = self._parse_status(detail_text)

        scores = self._get_scores(container)
        if scores:
            details["home_score"], details["away_score"] = scores

        if (
            details.get("status") == "finished"
            and details.get("round_number") is not None
            and self._is_regular_season_match(title_text)
        ):
            print_details = self._fetch_print_match_details(self._get_match_url(container) or "")
            details.update(print_details)

        return details

    def _apply_optional_match_details(self, match_info: Dict[str, Any], details: Dict[str, Any]) -> None:
        optional_fields = [
            "home_score",
            "away_score",
            "home_tries",
            "away_tries",
            "round_number",
            "conference",
            "official_match_code",
        ]
        for field in optional_fields:
            value = details.get(field)
            if value is not None and value != "":
                match_info[field] = value

    def _parse_title_metadata(self, title_text: str) -> Dict[str, Any]:
        details: Dict[str, Any] = {}
        if not title_text:
            return details

        round_match = re.search(r"第\s*(\d+)\s*節", title_text)
        if round_match:
            round_number = int(round_match.group(1))
            details["round"] = str(round_number)
            details["round_number"] = round_number

        conference_match = re.search(r"カンファレンス\s*([A-ZＡ-Ｚ])", title_text)
        if conference_match:
            details["conference"] = self._normalize_fullwidth_ascii(conference_match.group(1))

        code_matches = re.findall(r"\(([^()]+)\)", title_text)
        if code_matches:
            details["official_match_code"] = code_matches[-1].strip()

        return details

    def _normalize_fullwidth_ascii(self, value: str) -> str:
        return value.translate(str.maketrans("ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"))

    def _parse_status(self, detail_text: str) -> str:
        if "試合終了" in detail_text:
            return "finished"
        return "scheduled"

    def _get_scores(self, container):
        score_elements = container.select("li.home p.score, li.away p.score")
        if len(score_elements) < 2:
            return None

        scores = []
        for element in score_elements[:2]:
            score_text = element.get_text(strip=True)
            if not score_text or not score_text.isdigit():
                return None
            scores.append(int(score_text))
        return tuple(scores)

    def _is_regular_season_match(self, title_text: str) -> bool:
        return "ディビジョン" in title_text and re.search(r"第\s*\d+\s*節", title_text) is not None

    def _fetch_print_match_details(self, match_url: str) -> Dict[str, Any]:
        if not match_url:
            return {}

        print_url = urljoin(match_url.rstrip("/") + "/", "print")
        try:
            response = None
            for attempt in range(3):
                self._throttle_print_request()
                response = requests.get(
                    print_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    },
                    timeout=30,
                )
                self._last_print_request_at = time.monotonic()
                if response.status_code == 200:
                    break
                if response.status_code != 429 or attempt == 2:
                    return {}
                time.sleep(10 * (attempt + 1))

            if not response or response.status_code != 200:
                return {}
            soup = BeautifulSoup(response.content, "html.parser")
            return self._parse_print_score_table(soup)
        except Exception as e:
            print(f"公式記録プリントページの取得に失敗: url='{print_url}' error='{e}'")
            return {}

    def _throttle_print_request(self) -> None:
        elapsed = time.monotonic() - self._last_print_request_at
        if elapsed < self._print_request_interval_seconds:
            time.sleep(self._print_request_interval_seconds - elapsed)

    def _parse_print_score_table(self, soup) -> Dict[str, Any]:
        score_table = soup.find("table", class_="score")
        if not score_table:
            return {}

        details: Dict[str, Any] = {}
        for row in score_table.find_all("tr"):
            label = row.find("th", class_="tp")
            if not label:
                continue

            label_text = label.get_text(strip=True)
            values = [self._parse_int(cell.get_text(strip=True)) for cell in row.find_all("td")]
            if label_text == "T" and len(values) >= 4:
                home_parts = values[:2]
                away_parts = values[2:4]
                if all(value is not None for value in home_parts):
                    details["home_tries"] = sum(home_parts)
                if all(value is not None for value in away_parts):
                    details["away_tries"] = sum(away_parts)
            elif label_text == "合計" and len(values) >= 2:
                if values[0] is not None:
                    details["home_score"] = values[0]
                if values[1] is not None:
                    details["away_score"] = values[1]

        return details

    def _parse_int(self, value: str):
        return int(value) if value and value.isdigit() else None

    def _get_team_logo_url(self, team_element) -> str:
        if not team_element:
            return ""
        img = team_element.find("img")
        if not img:
            return ""
        src = img.get("src") or img.get("data-src") or ""
        if not src:
            return ""
        if src.startswith("//"):
            return f"https:{src}"
        if src.startswith("/"):
            return f"{self.base_url}{src}"
        return src

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
        
    def _now(self):
        return datetime.now(self.jst)

    def _season_year_for_month(self, month: int) -> int:
        current_date = self._now()
        current_year = current_date.year
        season_start_month = 12
        return current_year - 1 if month >= season_start_month else current_year

    def parse_kickoff_datetime(self, date_string: str, match_url: str = ""):
        try:
            if not date_string:
                raise ValueError("empty date string")

            parts = date_string.split()
            if len(parts) < 3:
                raise ValueError(f"unexpected date format: {date_string}")

            date_part = parts[0].split(".")
            if len(date_part) != 2:
                raise ValueError(f"unexpected date token: {parts[0]}")

            month = int(date_part[0])
            day = int(date_part[1])
            hour, minute = [int(v) for v in parts[2].split(":")]

            year = self._season_year_for_month(month)
            kickoff = datetime(year, month, day, hour, minute, tzinfo=self.jst)

            # MM.DD と最終値の月日が一致しない場合は異常として扱う
            if kickoff.month != month or kickoff.day != day:
                raise ValueError(
                    f"parsed date mismatch: src={month:02}.{day:02} parsed={kickoff.month:02}.{kickoff.day:02}"
                )

            return kickoff
        except (ValueError, IndexError) as e:
            print(
                f"キックオフ日時の解析に失敗: date='{date_string}' url='{match_url}' error='{e}'"
            )
            return None
