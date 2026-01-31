import io
import re
from datetime import datetime, timezone, timedelta
import requests
import pdfplumber
from .base import BaseScraper

class SuperRugbyPacificScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.source_url = "https://www.super.rugby/superrugby/fixtures/"
        self.pdf_url = "https://super.rugby/superrugby/documents/media-files/2026-super-rugby-pacific-match-schedule/"

    def scrape(self):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(self.pdf_url, headers=headers, timeout=30)
            if response.status_code != 200:
                print(f"PDFの取得に失敗: {self.pdf_url}")
                return None

            matches = self._parse_pdf(response.content)
            print(f"取得した試合数: {len(matches)}")
            return matches
        except Exception as e:
            print(f"スクレイピングエラー: {str(e)}")
            return None

    def _parse_pdf(self, pdf_bytes: bytes):
        matches = []
        year = None
        current_round = ""
        pending_round_indices = []

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    if year is None:
                        year_match = re.match(r"^(\d{4})\s+DRAW$", line)
                        if year_match:
                            year = int(year_match.group(1))
                            continue

                    if "DATE TEAM VS TEAM" in line.upper():
                        continue

                    if line.startswith("BYE:"):
                        continue

                    if re.fullmatch(r"\d{1,2}", line):
                        current_round = line.zfill(2)
                        if pending_round_indices:
                            for idx in pending_round_indices:
                                matches[idx]["round"] = f"Round {current_round}"
                            pending_round_indices = []
                        continue

                    round_pending = False
                    if line.startswith("ROUND "):
                        line = line.replace("ROUND ", "", 1)
                        round_pending = True

                    parsed = self._parse_match_line(line, year)
                    if not parsed:
                        continue

                    match_data = self.build_match(
                        competition="Super Rugby Pacific",
                        competition_id="205",
                        season=str(year) if year else "",
                        round_name=f"Round {current_round}" if current_round else "",
                        status="",
                        kickoff=parsed["kickoff_dt"],
                        timezone_name=parsed["timezone_name"],
                        timezone_source="pdf_local_vs_gmt",
                        venue=parsed["venue"],
                        home_team=parsed["home_team"],
                        away_team=parsed["away_team"],
                        match_url="",
                        broadcasters=[],
                        source_name="Super Rugby",
                        source_url=self.pdf_url,
                        source_type="official",
                    )

                    matches.append(match_data)
                    if round_pending and not current_round:
                        pending_round_indices.append(len(matches) - 1)

        return matches

    def _parse_match_line(self, line: str, year: int):
        if not year:
            return None

        tokens = line.split()
        if not tokens:
            return None

        if tokens[0] == "ROUND":
            tokens = tokens[1:]

        time_indices = [i for i, token in enumerate(tokens) if re.match(r"^\d{1,2}:\d{2}$", token)]
        if len(time_indices) < 2:
            return None

        first_time_idx = time_indices[0]
        last_time_idx = time_indices[-1]
        prefix_tokens = tokens[:first_time_idx]
        venue_tokens = tokens[last_time_idx + 1 :]

        if not venue_tokens and first_time_idx >= 1 and tokens[first_time_idx - 1].upper() == "TBC":
            venue_tokens = ["TBC"]
            prefix_tokens = tokens[: first_time_idx - 1]

        if len(prefix_tokens) < 4:
            return None

        date_tokens = prefix_tokens[:3]
        if not re.match(r"^(MON|TUE|WED|THU|FRI|SAT|SUN)$", date_tokens[0]):
            return None

        day = date_tokens[1]
        month = date_tokens[2]
        teams_text = " ".join(prefix_tokens[3:])
        team_parts = re.split(r"\s+VS\s+|\s+vs\s+", teams_text)
        if len(team_parts) != 2:
            return None

        home_team = team_parts[0].strip()
        away_and_venue = team_parts[1].strip()

        away_tokens = away_and_venue.split()
        venue_tokens = list(venue_tokens)
        venue_start = None
        venue_keywords = {"stadium", "park", "oval", "arena", "ground", "field", "tbc"}
        for idx, token in enumerate(away_tokens):
            cleaned = token.strip(",").lower()
            if cleaned in venue_keywords:
                venue_start = idx
                break

        venue_start_lower = None
        for idx, token in enumerate(away_tokens):
            if any(ch.isalpha() for ch in token) and token != token.upper():
                venue_start_lower = idx
                break

        if venue_start_lower is not None and (venue_start is None or venue_start_lower < venue_start):
            venue_start = venue_start_lower

        if venue_start is not None:
            venue_tokens = away_tokens[venue_start:] + venue_tokens
            away_tokens = away_tokens[:venue_start]

        away_team = " ".join(away_tokens).strip()
        venue = " ".join(venue_tokens).strip()

        date_str = f"{day} {month} {year}"
        try:
            match_date = datetime.strptime(date_str, "%d %b %Y")
        except ValueError:
            return None

        local_time = tokens[first_time_idx]
        gmt_time = tokens[first_time_idx + 1]
        local_dt = datetime.strptime(local_time, "%H:%M")
        gmt_dt = datetime.strptime(gmt_time, "%H:%M")

        offset_minutes = int((local_dt - gmt_dt).total_seconds() / 60)
        if offset_minutes < -12 * 60:
            offset_minutes += 24 * 60
        if offset_minutes > 14 * 60:
            offset_minutes -= 24 * 60

        offset = timedelta(minutes=offset_minutes)
        offset_sign = "+" if offset_minutes >= 0 else "-"
        offset_minutes_abs = abs(offset_minutes)
        offset_hours, offset_mins = divmod(offset_minutes_abs, 60)
        timezone_name = f"UTC{offset_sign}{offset_hours:02}:{offset_mins:02}"

        kickoff_dt = datetime(
            match_date.year,
            match_date.month,
            match_date.day,
            int(local_time.split(":")[0]),
            int(local_time.split(":")[1]),
            tzinfo=timezone(offset),
        )

        return {
            "home_team": home_team,
            "away_team": away_team,
            "venue": venue,
            "kickoff_dt": kickoff_dt,
            "timezone_name": timezone_name,
        }
