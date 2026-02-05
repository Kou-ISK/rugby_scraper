from abc import ABC, abstractmethod
import json
import hashlib
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
        self._team_master = self._load_team_master()
        self._competition_id = None  # サブクラスで設定
    
    def _load_team_master(self) -> Dict[str, Any]:
        """Load team master data from data/teams.json."""
        # Try relative to current working directory first
        teams_path = Path("data/teams.json")
        if not teams_path.exists():
            # Try relative to this file
            base_path = Path(__file__).resolve().parents[2]
            teams_path = base_path / "data" / "teams.json"
        
        if not teams_path.exists():
            print(f"Warning: teams.json not found at {teams_path}")
            return {}
        
        try:
            with open(teams_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load teams.json: {e}")
            return {}
    
    def _resolve_team_id(self, team_name: str, competition_id: Optional[str] = None) -> str:
        """Resolve team ID from team name using master data.
        
        新ID形式対応:
        - 大会IDが指定されている場合、その大会のチームのみを検索
        - 例: competition_id="w6n", team_name="ENG" → "w6n-1"
        
        Args:
            team_name: Team display name (e.g., 'FRA', 'France', 'England')
            competition_id: Competition ID to narrow search (optional)
            
        Returns:
            Team ID from master, or empty string if not found.
        """
        if not team_name:
            return ""
        
        # 大会IDが指定されている場合、その大会のチームのみを検索
        if competition_id:
            for team_id, team_data in self._team_master.items():
                # 新ID形式: {comp_id}-{num}
                if team_data.get("competition_id") == competition_id:
                    # short_name, name のいずれかが一致するかチェック
                    if team_name.upper() == team_data.get("short_name", "").upper():
                        return team_id
                    if team_name.lower() == team_data.get("name", "").lower():
                        return team_id
        
        # 大会ID指定なし、または見つからない場合は全体から検索（後方互換性）
        # Try exact lowercase match first
        key = team_name.lower()
        if key in self._team_master:
            return key
        
        # Try matching against short_name or name
        for team_id, team_data in self._team_master.items():
            if team_name.upper() == team_data.get("short_name", "").upper():
                return team_id
            if team_name.lower() == team_data.get("name", "").lower():
                return team_id
        
        return ""
    
    def _generate_match_id(self, competition_id: str, kickoff_utc: str, 
                          home_team: str, away_team: str) -> str:
        """Generate stable match ID.
        
        Args:
            competition_id: Competition identifier
            kickoff_utc: Kickoff time in UTC (ISO8601)
            home_team: Home team display name
            away_team: Away team display name
            
        Returns:
            Unique match ID based on competition, time and teams.
        """
        if not all([competition_id, kickoff_utc, home_team, away_team]):
            return ""
        
        base = f"{competition_id}|{kickoff_utc}|{home_team}|{away_team}"
        digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
        return f"{competition_id}-{kickoff_utc.lower()}-{home_team.lower()}-{away_team.lower()}-{digest}"
    
    @abstractmethod
    def scrape(self):
        pass
    
    def save_to_json(self, data: Union[List[Dict[str, Any]], Dict[str, Any]], filename: str):
        """Save data to JSON file.
        
        新ディレクトリ構造対応:
        - filename に大会ID/シーズン形式を使用 (例: "w6n/2026")
        - 旧形式 (例: "six-nations-women") もサポート
        """
        output_path = self.output_dir / f"{filename}.json"
        
        # 親ディレクトリを作成（新構造対応）
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
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
        
        # Auto-resolve team IDs from master if not provided
        # 大会IDを使ってチーム検索を絞り込み
        comp_id = str(competition_id) if competition_id is not None else (self._competition_id or "")
        if home_team_id is None:
            home_team_id = self._resolve_team_id(home_team, comp_id)
        if away_team_id is None:
            away_team_id = self._resolve_team_id(away_team, comp_id)
        
        # Auto-generate match_id if not provided
        if match_id is None and kickoff_utc and home_team and away_team and comp_id:
            match_id = self._generate_match_id(comp_id, kickoff_utc, home_team, away_team)

        return {
            "match_id": str(match_id) if match_id else "",
            "competition": competition,
            "competition_id": comp_id,
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
            "home_team_id": str(home_team_id) if home_team_id else "",
            "away_team_id": str(away_team_id) if away_team_id else "",
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
