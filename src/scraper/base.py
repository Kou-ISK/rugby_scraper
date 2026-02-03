from abc import ABC, abstractmethod
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dateutil import parser as date_parser
try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    from backports.zoneinfo import ZoneInfo

class BaseScraper(ABC):
    def __init__(self):
        self.output_dir = Path("data/matches")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def scrape(self):
        pass
    
    def save_to_json(self, data: Union[List[Dict[str, Any]], Dict[str, Any]], filename: str):
        output_path = self.output_dir / f"{filename}.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, ensure_ascii=False, indent=2, fp=f)

    def _parse_timezone_offset(self, timezone_value: Optional[str]) -> Optional[timezone]:
        if not timezone_value:
            return None
        if timezone_value.upper() == "UTC":
            return timezone.utc
        if timezone_value.startswith("UTC"):
            timezone_value = timezone_value[3:]
        if timezone_value.startswith(("+", "-")) and len(timezone_value) >= 3:
            sign = 1 if timezone_value[0] == "+" else -1
            try:
                hours, minutes = timezone_value[1:].split(":")
            except ValueError:
                hours = timezone_value[1:3]
                minutes = "00"
            try:
                offset = timedelta(hours=int(hours), minutes=int(minutes)) * sign
                return timezone(offset)
            except ValueError:
                return None
        return None

    def _normalize_datetime(
        self,
        value: Optional[Union[str, datetime]],
        timezone_name: Optional[str],
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        if not value:
            return None, None, timezone_name

        if isinstance(value, datetime):
            dt = value
        else:
            try:
                # dayfirst=True: 日付の曖昧性を解決 (例: "05/02/2026" → 2月5日)
                dt = date_parser.parse(str(value), fuzzy=True, dayfirst=True)
            except (ValueError, TypeError):
                return None, None, timezone_name

        if dt.tzinfo is None:
            tzinfo = None
            if timezone_name:
                try:
                    tzinfo = ZoneInfo(timezone_name)
                except Exception:
                    tzinfo = self._parse_timezone_offset(timezone_name)
            if tzinfo is None:
                tzinfo = timezone.utc
                timezone_name = "UTC"
            dt = dt.replace(tzinfo=tzinfo)
        else:
            timezone_name = timezone_name or str(dt.tzinfo)

        kickoff_local = dt.isoformat()
        kickoff_utc = dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return kickoff_local, kickoff_utc, timezone_name

    def build_match(
        self,
        *,
        competition: str,
        source_name: str,
        source_url: str,
        source_type: str,
        kickoff: Optional[Union[str, datetime]],
        timezone_name: Optional[str],
        timezone_source: str,
        venue: str,
        home_team: str,
        away_team: str,
        match_url: str,
        broadcasters: Optional[List[str]] = None,
        competition_id: Optional[Union[str, int]] = None,
        season: Optional[Union[str, int]] = None,
        round_name: str = "",
        status: str = "",
        match_id: Optional[Union[str, int]] = None,
        home_team_id: Optional[Union[str, int]] = None,
        away_team_id: Optional[Union[str, int]] = None,
    ) -> Dict[str, Any]:
        kickoff_local, kickoff_utc, tz_name = self._normalize_datetime(kickoff, timezone_name)

        return {
            "match_id": str(match_id) if match_id is not None else "",
            "competition": competition,
            "competition_id": str(competition_id) if competition_id is not None else "",
            "season": str(season) if season is not None else "",
            "round": round_name or "",
            "status": status or "",
            "kickoff": kickoff_local or "",
            "kickoff_utc": kickoff_utc or "",
            "timezone": tz_name or "",
            "timezone_source": timezone_source,
            "venue": venue or "",
            "home_team": home_team or "",
            "away_team": away_team or "",
            "home_team_id": str(home_team_id) if home_team_id is not None else "",
            "away_team_id": str(away_team_id) if away_team_id is not None else "",
            "match_url": match_url or "",
            "broadcasters": broadcasters or [],
            "source_name": source_name,
            "source_url": source_url,
            "source_type": source_type,
        }

    def apply_timezone_override(self, driver, timezone_id: str):
        try:
            driver.execute_cdp_cmd(
                "Emulation.setTimezoneOverride", {"timezoneId": timezone_id}
            )
            try:
                resolved = driver.execute_script(
                    "return Intl.DateTimeFormat().resolvedOptions().timeZone"
                )
                if resolved and resolved != timezone_id:
                    print(f"Timezone override mismatch: {timezone_id} -> {resolved}")
            except Exception:
                pass
        except Exception:
            pass
