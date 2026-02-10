from abc import ABC, abstractmethod
import json
import hashlib
import re
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import quote_plus
from dateutil import parser as date_parser
try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    from backports.zoneinfo import ZoneInfo

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class BaseScraper(ABC):
    # 国際試合の大会ID（同名チームを同一視）
    INTERNATIONAL_COMPETITIONS = {
        "m6n": "M",      # Six Nations (Men) → M
        "w6n": "W",      # Six Nations (Women) → W
        "u6n": "U20",    # Six Nations U20 → U20
        "trc": "M",      # The Rugby Championship → M
        "ans": "M",      # Autumn Nations Series → M
        "wr": "M",       # World Rugby Internationals → M (混合の場合は個別判定)
    }
    
    # 国略称マッピング（チーム名 → 3文字コード）
    COUNTRY_CODES = {
        # Six Nations
        "ENGLAND": "ENG", "England": "ENG", "ENG": "ENG",
        "FRANCE": "FRA", "France": "FRA", "FRA": "FRA",
        "IRELAND": "IRE", "Ireland": "IRE", "IRE": "IRE",
        "ITALY": "ITA", "Italy": "ITA", "ITA": "ITA",
        "SCOTLAND": "SCO", "Scotland": "SCO", "SCO": "SCO",
        "WALES": "WAL", "Wales": "WAL", "WAL": "WAL",
        
        # Rugby Championship
        "ARGENTINA": "ARG", "Argentina": "ARG",
        "AUSTRALIA": "AUS", "Australia": "AUS",
        "NEW ZEALAND": "NZL", "New Zealand": "NZL",
        "SOUTH AFRICA": "RSA", "South Africa": "RSA",
        
        # その他主要国
        "JAPAN": "JPN", "Japan": "JPN",
        "FIJI": "FIJ", "Fiji": "FIJ",
        "USA": "USA",
        "CHILE": "CHI", "Chile": "CHI",
    }
    
    # 静的スポンサー名パターン（フォールバック用）
    SPONSOR_PATTERNS = [
        # 先頭のスポンサー名
        r'^DHL\s+',
        r'^ISUZU\s+',
        r'^GALLAGHER\s+',
        r'^Hollywoodbets\s+',
        r'^Vodacom\s+',
        # 末尾のスポンサー名
        r'\s+GIO$',
        r'\s+HBF$',
        r'\s+FMG$',
        r'\s+SKY$',
        r'\s+DHL$',
        r'\s+ISUZU$',
        r'\s+GALLAGHER$',
        r'\s+4R$',
        r'\s+FOUR\s+R$',
        r'\s+CHURCHILL$',
        r'\s+MCLEAN$',
        r'\s+HIF$',
        r'\s+HFC\s+BANK$',
    ]

    # Competition-specific alias mappings (short/alt names -> official names)
    # Keys are normalized via _normalize_alias_key.
    COMPETITION_TEAM_ALIASES = {
        "epcr-champions": {
            "Bayonne": "Aviron Bayonnais",
            "Bordeaux-Begles": "Union Bordeaux Bègles",
            "Clermont Auvergne": "ASM Clermont Auvergne",
            "La Rochelle": "Stade Rochelais",
            "Pau": "Section Paloise",
            "Toulon": "RC Toulon",
            "Toulouse": "Stade Toulousain",
            "Stade Francais Paris": "Stade Français Paris",
        },
        "epcr-challenge": {
            "Lyon O.U.": "Lyon Olympique Universitaire",
            "Montauban": "US Montauban",
            "Montpellier": "Montpellier Hérault Rugby",
            "Perpignan": "USAP",
            "Stade Francais Paris": "Stade Français Paris",
        },
        "jrlo-div1": {
            "埼玉ワイルドナイツ": "埼玉パナソニックワイルドナイツ",
            "東京サンゴリアス": "東京サントリーサンゴリアス",
        },
        "jrlo-div3": {
            "スカイアクティブズ広島": "マツダスカイアクティブズ広島",
        },
    }
    
    def __init__(self, *, update_team_master: bool = False):
        self.output_dir = Path("data/matches")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._team_master = self._load_team_master()
        self._competition_id = None  # サブクラスで設定
        self._base_team_names = self._build_base_team_names_cache()  # 動的スポンサー検知用
        self._thesportsdb_api_key = os.environ.get("THESPORTSDB_API_KEY", "3")  # Free tier
        self._logo_cache = {}  # ロゴURL取得のキャッシュ（メモリ内）
        self._logo_cache_file = Path("data/team_logos_cache.json")  # 永続キャッシュファイル
        self._load_logo_cache()  # ファイルからキャッシュ読み込み
        self._update_team_master = update_team_master

    @staticmethod
    def _prefer_selenium_manager() -> None:
        """Prefer Selenium Manager by removing any PATH entries that contain chromedriver."""
        path = os.environ.get("PATH", "")
        if not path:
            return
        parts = []
        for p in path.split(os.pathsep):
            candidate = Path(p) / "chromedriver"
            if candidate.exists():
                continue
            parts.append(p)
        os.environ["PATH"] = os.pathsep.join(parts)
    
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

    def _save_team_master(self) -> bool:
        """Persist team master data to data/teams.json."""
        if not self._update_team_master:
            return False
        teams_file = self.output_dir.parent / "teams.json"
        try:
            with open(teams_file, "w", encoding="utf-8") as f:
                json.dump(self._team_master, f, ensure_ascii=False, indent=2)
                f.write("\n")
            return True
        except Exception as e:
            print(f"⚠️ チームマスタ保存エラー: {e}")
            return False

    def _should_replace_logo(self, existing_url: str) -> bool:
        """Determine if an official logo should overwrite existing value."""
        if not existing_url:
            return True
        lower = existing_url.lower()
        if "thesportsdb.com" in lower or "r2.thesportsdb.com" in lower:
            return True
        return False

    def _apply_official_team_logos(self, team_logos: Dict[str, Dict[str, str]], competition_id: str) -> None:
        """Apply official logo URLs to team master (fill or replace TheSportsDB)."""
        if not self._update_team_master:
            return
        if not team_logos:
            return

        updated = False
        for team_name, logo_info in team_logos.items():
            if not team_name or not logo_info:
                continue
            logo_url = logo_info.get("logo_url", "")
            badge_url = logo_info.get("badge_url", "") or ""
            if logo_url and not badge_url:
                badge_url = logo_url

            # 1) competition_id に紐づくチームを更新
            team_id = self._resolve_team_id(team_name, competition_id)
            if team_id:
                team_data = self._team_master.get(team_id)
                if team_data:
                    if logo_url and self._should_replace_logo(team_data.get("logo_url", "")):
                        team_data["logo_url"] = logo_url
                        updated = True
                    if badge_url and self._should_replace_logo(team_data.get("badge_url", "")):
                        team_data["badge_url"] = badge_url
                        updated = True

            # 2) 同名チーム（他大会）も公式ロゴで更新
            normalized_name = team_name.strip().lower()
            for other_id, other_data in self._team_master.items():
                if other_id == team_id:
                    continue
                if normalized_name == (other_data.get("name", "").strip().lower()) or normalized_name == (
                    other_data.get("short_name", "").strip().lower()
                ):
                    if logo_url and self._should_replace_logo(other_data.get("logo_url", "")):
                        other_data["logo_url"] = logo_url
                        updated = True
                    if badge_url and self._should_replace_logo(other_data.get("badge_url", "")):
                        other_data["badge_url"] = badge_url
                        updated = True

        if updated:
            self._save_team_master()
    
    def _build_base_team_names_cache(self) -> Dict[str, set]:
        """既存チーム名のキャッシュを構築（動的スポンサー検知用）
        
        Returns:
            大会IDごとのチーム名セット
            例: {"srp": {"CHIEFS", "BLUES", ...}, "m6n": {"England", "France", ...}}
        """
        cache = {}
        
        for team_id, team_data in self._team_master.items():
            comp_id = team_data.get("competition_id", "")
            name = team_data.get("name", "").strip()
            short_name = team_data.get("short_name", "").strip()
            
            if comp_id:
                if comp_id not in cache:
                    cache[comp_id] = set()
                
                if name:
                    cache[comp_id].add(name)
                if short_name and short_name != name:
                    cache[comp_id].add(short_name)
        
        return cache
    
    def _is_national_team_variant(self, team_name: str) -> bool:
        """代表チームの派生形かどうか判定
        
        例: "England A", "Italy XV", "Scotland A" → True
            "England", "France", "Japan" → False
        """
        variant_patterns = [
            r'\s+A$',
            r'\s+XV$',
            r'\s+Barbarians$',
            r'\s+Women$',
            r'\s+U20$',
            r'\s+Development$',
        ]
        
        for pattern in variant_patterns:
            if re.search(pattern, team_name, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_national_team_variant_suffix(self, team_name: str) -> Optional[str]:
        """代表チームバリエーションの接尾辞を抽出
        
        Args:
            team_name: チーム名（例: "England A", "Italy XV"）
            
        Returns:
            接尾辞（例: "A", "XV"）、バリエーションでない場合はNone
        """
        variant_patterns = [
            (r'\s+(A)$', 'A'),
            (r'\s+(XV)$', 'XV'),
            (r'\s+(Barbarians)$', 'Barbarians'),
            (r'\s+(Development)$', 'Dev'),
        ]
        
        for pattern, suffix in variant_patterns:
            match = re.search(pattern, team_name, re.IGNORECASE)
            if match:
                return suffix
        
        return None
    
    def _generate_national_team_id(self, team_name: str, competition_id: str) -> str:
        """国代表チームのIDを生成
        
        新ID形式: NT-{カテゴリ}-{国コード}[-{バリエーション}]
        - NT: National Team
        - カテゴリ: M (Men), W (Women), U20
        - 国コード: ENG, FRA, IRE, ITA, SCO, WAL等の3文字
        - バリエーション: A, XV等（オプション）
        
        例:
            - NT-M-ENG (England Men)
            - NT-W-IRE (Ireland Women)
            - NT-U20-WAL (Wales U20)
            - NT-M-ENG-A (England A)
            - NT-M-ITA-XV (Italy XV)
        
        Args:
            team_name: チーム名（例: "England", "England A"）
            competition_id: 大会ID（例: "m6n", "w6n"）
            
        Returns:
            国代表チームID、国際大会でない場合は空文字列
        """
        # 国際大会かチェック
        if competition_id not in self.INTERNATIONAL_COMPETITIONS:
            return ""
        
        # カテゴリ取得（M, W, U20）
        category = self.INTERNATIONAL_COMPETITIONS[competition_id]
        
        # バリエーション接尾辞を抽出
        variant_suffix = self._extract_national_team_variant_suffix(team_name)
        
        # ベースチーム名（バリエーション接尾辞を除去）
        base_team = team_name
        if variant_suffix:
            # 接尾辞を除去
            base_team = re.sub(r'\s+(A|XV|Barbarians|Development)$', '', team_name, flags=re.IGNORECASE).strip()
        
        # 国コード取得
        country_code = self.COUNTRY_CODES.get(base_team.upper())
        if not country_code:
            country_code = self.COUNTRY_CODES.get(base_team)
        
        if not country_code:
            # 国コードが見つからない場合は空文字列
            return ""
        
        # ID生成（アンダースコア区切りに変更）
        if variant_suffix:
            return f"NT_{category}_{country_code}_{variant_suffix}"
        else:
            return f"NT_{category}_{country_code}"
    
    def _normalize_team_name(self, team_name: str, competition_id: Optional[str] = None) -> str:
        """チーム名からスポンサー名を除去してベース名を取得
        
        【動的スポンサー検知】
        既存チーム名をベースに、スポンサー名を自動検出:
        1. 既存チーム名と完全一致 → そのまま返す
        2. "既存チーム名 + 何か" → 既存チーム名を返す
        3. "何か + 既存チーム名" → 既存チーム名を返す
        4. 静的パターンにマッチ → パターン除去
        
        【国際試合の特別扱い】
        - 国際大会では同名チームを同一視（チーム名正規化のみ）
        - "England A", "Italy XV" などは別チーム扱い
        - チームIDの解決は各大会内で行う
        
        Args:
            team_name: 元のチーム名
            competition_id: 大会ID（オプション）
            
        Returns:
            スポンサー名を除去したベースチーム名
        """
        if not team_name:
            return ""
        
        team_name = team_name.strip()

        # Competition-specific alias mapping
        if competition_id:
            aliases = self.COMPETITION_TEAM_ALIASES.get(competition_id, {})
            if aliases:
                alias_key = self._normalize_alias_key(team_name)
                mapped = aliases.get(alias_key)
                if not mapped:
                    for raw_name, official_name in aliases.items():
                        if self._normalize_alias_key(raw_name) == alias_key:
                            mapped = official_name
                            break
                if mapped:
                    return mapped

        # SRP公式表記の補正（スポンサー除去ではない別名）
        if competition_id == "srp":
            srp_aliases = {
                "BLUES": "Blues",
                "BRUMBIES": "Brumbies",
                "CHIEFS": "Chiefs",
                "CRUSADERS": "Crusaders",
                "FIJIAN DRUA": "Fijian Drua",
                "FORCE": "Western Force",
                "HIGHLANDERS": "Highlanders",
                "HURRICANES": "Hurricanes",
                "MOANA PASIFIKA": "Moana Pasifika",
                "REDS": "Queensland Reds",
                "WARATAHS": "NSW Waratahs",
            }
            mapped = srp_aliases.get(team_name.upper())
            if mapped:
                return mapped
        
        # 国際試合の場合、代表チームバリエーションはそのまま保持
        if competition_id and competition_id in self.INTERNATIONAL_COMPETITIONS:
            if self._is_national_team_variant(team_name):
                return team_name
        
        # 動的スポンサー検知の検索範囲
        # 国際試合では全国際大会から検索、それ以外は指定大会のみ
        search_comps = []
        
        if competition_id:
            if competition_id in self.INTERNATIONAL_COMPETITIONS:
                # 国際試合: 全国際大会から検索（チーム名を統一）
                search_comps = list(self.INTERNATIONAL_COMPETITIONS)
            else:
                # クラブ試合: 指定大会のみ
                search_comps = [competition_id]
        else:
            # 大会ID不明の場合、全大会から検索
            search_comps = list(self._base_team_names.keys())
        
        # 既存チーム名との完全一致・部分一致チェック
        for comp in search_comps:
            base_names = self._base_team_names.get(comp, set())
            
            for base_name in base_names:
                # 完全一致
                if team_name.upper() == base_name.upper():
                    return base_name
                
                # "BASE_NAME + スポンサー" パターン（大文字小文字無視）
                if team_name.upper().startswith(base_name.upper() + " "):
                    # スポンサー部分が英数字のみならマッチ
                    suffix = team_name[len(base_name):].strip()
                    if suffix and re.match(r'^[A-Z0-9\s]+$', suffix, re.IGNORECASE):
                        return base_name
                
                # "スポンサー + BASE_NAME" パターン
                if team_name.upper().endswith(" " + base_name.upper()):
                    # プレフィックス部分が英数字のみならマッチ
                    prefix = team_name[:-(len(base_name) + 1)].strip()
                    if prefix and re.match(r'^[A-Z0-9\s]+$', prefix, re.IGNORECASE):
                        return base_name
        
        # 静的パターンでのフォールバック
        normalized = team_name
        for pattern in self.SPONSOR_PATTERNS:
            candidate = re.sub(pattern, '', normalized, flags=re.IGNORECASE).strip()
            if candidate and candidate != normalized:
                if any(
                    candidate.upper() == base.upper()
                    for base in self._base_team_names.get(competition_id, set())
                ):
                    normalized = candidate
        return normalized.strip()

    @staticmethod
    def _normalize_alias_key(value: str) -> str:
        import unicodedata

        normalized = unicodedata.normalize("NFKC", value or "")
        normalized = normalized.strip()
        normalized = re.sub(r"\s+", " ", normalized)
        normalized = normalized.casefold()
        normalized = re.sub(r"[^\w\s]", "", normalized, flags=re.UNICODE)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized
    
    def _register_national_team(self, team_id: str, team_name: str, competition_id: str) -> bool:
        """Register new national team to teams.json.
        
        Args:
            team_id: Generated national team ID (e.g., NT-M-ENG)
            team_name: Team display name
            competition_id: Competition ID
            
        Returns:
            True if registered, False if already exists or error.
        """
        if not self._update_team_master:
            return False
        if not team_id or team_id in self._team_master:
            return False
        
        # 新規国代表チーム登録
        self._team_master[team_id] = {
            "id": team_id,
            "competition_id": competition_id,
            "name": team_name,
            "name_ja": "",
            "short_name": team_name,
            "country": "",
            "division": "",
            "logo_url": "",
            "badge_url": "",
        }
        
        # teams.jsonに保存
        teams_file = self.output_dir.parent / "teams.json"
        try:
            with open(teams_file, "w", encoding="utf-8") as f:
                json.dump(self._team_master, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print(f"✅ 新規国代表チーム登録: {team_id} ({team_name})")
            return True
        except Exception as e:
            print(f"⚠️ チーム登録エラー ({team_id}): {e}")
            return False
    
    def _generate_club_team_id(self, team_name: str, competition_id: str) -> str:
        """クラブチーム用のteam_idを生成（連番形式）
        
        形式: {大会略称}_{連番}
        例: premier_1, urc_1, jrlo-div1_1
        
        Args:
            team_name: チーム名
            competition_id: 大会ID
            
        Returns:
            生成されたteam_id
        """
        # 大会ID→略称マッピング
        comp_abbr_map = {
            'premier': 'premier',
            'urc': 'urc',
            'wr': 'wr',
            'jrlo-div1': 'jrlo-div1',
            'jrlo-div2': 'jrlo-div2',
            'jrlo-div3': 'jrlo-div3',
            'epcr-champions': 'epcr-champions',
            'epcr-challenge': 'epcr-challenge',
        }
        
        comp_abbr = comp_abbr_map.get(competition_id, competition_id)
        
        # 同じ大会の既存チーム数を取得
        existing_teams = [
            t for t in self._team_master.values()
            if t.get('competition_id') == competition_id
        ]
        
        # 次の連番を決定
        next_num = len(existing_teams) + 1
        
        return f"{comp_abbr}_{next_num}"
    
    def _load_logo_cache(self) -> None:
        """永続キャッシュファイルからロゴ情報を読み込み"""
        if not self._logo_cache_file.exists():
            return
        
        try:
            with open(self._logo_cache_file, 'r', encoding='utf-8') as f:
                file_cache = json.load(f)
                # ファイルキャッシュをメモリキャッシュにロード
                for team_name, cache_data in file_cache.items():
                    self._logo_cache[team_name] = {
                        "logo_url": cache_data.get("logo_url", ""),
                        "badge_url": cache_data.get("badge_url", ""),
                    }
        except Exception as e:
            print(f"⚠️ ロゴキャッシュ読み込みエラー: {e}")
    
    def _save_logo_cache(self) -> None:
        """ロゴキャッシュをファイルに保存"""
        try:
            cache_data = {}
            for team_name, logo_info in self._logo_cache.items():
                if logo_info:  # 空辞書は保存しない
                    cache_data[team_name] = {
                        "logo_url": logo_info.get("logo_url", ""),
                        "badge_url": logo_info.get("badge_url", ""),
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    }
            
            self._logo_cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._logo_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                f.write("\n")
        except Exception as e:
            print(f"⚠️ ロゴキャッシュ保存エラー: {e}")
    
    def _fetch_team_logo_from_thesportsdb(self, team_name: str) -> Dict[str, str]:
        """TheSportsDB APIからチームのロゴURLを取得
        
        Args:
            team_name: チーム名（例: "Bath Rugby", "England"）
            
        Returns:
            {"logo_url": "...", "badge_url": "..."} または空辞書
        """
        if not REQUESTS_AVAILABLE:
            return {}
        
        # キャッシュチェック（メモリ内＋ファイル）
        if team_name in self._logo_cache:
            return self._logo_cache[team_name]
        
        try:
            # API Rate Limit対策: 1秒待機
            import time
            time.sleep(1.0)
            
            # チーム検索API
            api_base = "https://www.thesportsdb.com/api/v1/json"
            url = f"{api_base}/{self._thesportsdb_api_key}/searchteams.php?t={quote_plus(team_name)}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            teams = data.get("teams") or []
            if not teams:
                self._logo_cache[team_name] = {}
                return {}
            
            # 最初のチームのロゴ情報を取得
            team = teams[0]
            result = {
                "logo_url": team.get("strLogo") or "",
                "badge_url": team.get("strBadge") or "",
            }
            
            # メモリキャッシュに保存
            self._logo_cache[team_name] = result
            
            # ファイルキャッシュにも保存
            self._save_logo_cache()
            
            return result
            
        except Exception as e:
            print(f"⚠️ TheSportsDB APIエラー ({team_name}): {e}")
            self._logo_cache[team_name] = {}
            return {}

    def _register_club_team_with_logo_provider(self, team_id: str, team_name: str, competition_id: str, logo_provider_func=None) -> bool:
        """クラブチームを登録（ロゴ取得関数を使用）
        
        Args:
            team_id: 生成されたteam_id
            team_name: チーム表示名
            competition_id: 大会ID
            logo_provider_func: ロゴURL取得関数（team_name を引数に取り、dict を返す）
            
        Returns:
            True if registered, False if already exists or error.
        """
        logo_info = {}
        if logo_provider_func and callable(logo_provider_func):
            try:
                logo_info = logo_provider_func(team_name) or {}
            except Exception as e:
                print(f"⚠️  ロゴ取得エラー ({team_name}): {e}")
        
        return self._register_club_team(team_id, team_name, competition_id, logo_info)
    
    def _register_club_team(self, team_id: str, team_name: str, competition_id: str, logo_info: dict = None) -> bool:
        """クラブチームをteams.jsonに登録
        
        Args:
            team_id: 生成されたteam_id (例: premier_1)
            team_name: チーム表示名
            competition_id: 大会ID
            logo_info: ロゴ情報辞書 {"logo_url": "...", "badge_url": "..."} (オプション)
            
        Returns:
            True if registered, False if already exists or error.
        """
        if not self._update_team_master:
            return False
        if not team_id or team_id in self._team_master:
            return False
        
        # ロゴ情報の取得（渡されていない場合は空）
        if logo_info is None:
            logo_info = {}
        
        logo_url = logo_info.get("logo_url", "")
        badge_url = logo_info.get("badge_url", "")
        
        # 新規クラブチーム登録
        self._team_master[team_id] = {
            "id": team_id,
            "competition_id": competition_id,
            "name": team_name,
            "name_ja": "",
            "short_name": team_name[:20],
            "country": "",
            "division": "",
            "logo_url": logo_url,
            "badge_url": badge_url,
        }
        
        # teams.jsonに保存
        teams_file = self.output_dir.parent / "teams.json"
        try:
            with open(teams_file, "w", encoding="utf-8") as f:
                json.dump(self._team_master, f, ensure_ascii=False, indent=2)
                f.write("\n")
            
            logo_status = ""
            if logo_url:
                logo_status = f" 🖼️ ロゴ取得済み"
            print(f"✅ 新規クラブチーム登録: {team_id} ({team_name}){logo_status}")
            return True
        except Exception as e:
            print(f"⚠️ チーム登録エラー ({team_id}): {e}")
            return False
    
    def _resolve_team_id(self, team_name: str, competition_id: Optional[str] = None) -> str:
        """Resolve team ID from team name using master data.
        
        新ID形式対応 + 動的スポンサー検知 + 国代表チーム自動登録:
        - team_nameから自動的にスポンサー名を除去
        - 国際大会の場合、NT-{カテゴリ}-{国コード}形式のIDを生成
        - 新規国代表チームは update_team_master=True の場合のみ自動登録
        - 例: competition_id="w6n", team_name="Ireland" → "NT-W-IRE" (自動登録)
        - 例: competition_id="wr", team_name="England A" → "NT-M-ENG-A" (自動登録)
        
        Args:
            team_name: Team display name (スポンサー名含む可能性あり)
            competition_id: Competition ID to narrow search (optional)
            
        Returns:
            Team ID from master, or empty string if not found.
        """
        if not team_name:
            return ""
        
        # スポンサー名を除去
        base_team_name = self._normalize_team_name(team_name, competition_id)
        
        # 国際大会の場合、国代表チームIDを生成して検索
        if competition_id and competition_id in self.INTERNATIONAL_COMPETITIONS:
            national_team_id = self._generate_national_team_id(base_team_name, competition_id)
            if national_team_id:
                # 生成したIDがteams.jsonに存在するか確認
                if national_team_id in self._team_master:
                    return national_team_id
                
                # 新規国代表チーム → 自動登録
                if self._update_team_master:
                    self._register_national_team(national_team_id, base_team_name, competition_id)
                    return national_team_id
                return ""
        
        # 大会IDが指定されている場合、その大会のチームのみを検索
        if competition_id:
            for team_id, team_data in self._team_master.items():
                if team_data.get("competition_id") == competition_id:
                    # short_name, name のいずれかが一致するかチェック
                    if base_team_name.upper() == team_data.get("short_name", "").upper():
                        return team_id
                    if base_team_name.lower() == team_data.get("name", "").lower():
                        return team_id
            
            # マスタに存在しない → 新規クラブチームとして登録
            if competition_id not in self.INTERNATIONAL_COMPETITIONS:
                if self._update_team_master:
                    club_team_id = self._generate_club_team_id(base_team_name, competition_id)
                    self._register_club_team(club_team_id, team_name, competition_id)
                    return club_team_id
                return ""
        
        # 全体から検索（後方互換性）
        key = base_team_name.lower()
        if key in self._team_master:
            return key
        
        # Try matching against short_name or name
        for team_id, team_data in self._team_master.items():
            if base_team_name.upper() == team_data.get("short_name", "").upper():
                return team_id
            if base_team_name.lower() == team_data.get("name", "").lower():
                return team_id
        
        return ""
    
    def _extract_round_number(self, round_name: str) -> str:
        """Extract numeric round number from round name.
        
        Args:
            round_name: Round name (e.g., "Round 1", "Round 15", "1", "")
            
        Returns:
            Numeric string (e.g., "1", "15") or empty string
        """
        if not round_name:
            return ""
        
        # Extract digits from round name
        import re
        match = re.search(r'(\d+)', round_name)
        return match.group(1) if match else ""
    
    def _generate_match_id(self, competition_id: str, season: str, round_num: str, sequence: int) -> str:
        """Generate stable match ID.
        
        新形式: {comp_id}-{season}[-rd{round_num}]-{seq}
        例: m6n-2026-rd1-1, jrlo-div1-2026-15, premier-202501-rd5-3
        
        Args:
            competition_id: Competition identifier (e.g., "m6n", "jrlo-div1")
            season: Season identifier (e.g., "2026", "202501")
            round_num: Round number (numeric string, e.g., "1", "5", or "" if no round)
            sequence: Sequence number within the competition/season/round
            
        Returns:
            Unique match ID
        """
        if not competition_id or not season:
            return ""
        
        parts = [competition_id, season]
        
        if round_num:
            parts.append(f"rd{round_num}")
        
        parts.append(str(sequence))
        
        return "-".join(parts)
    
    def assign_match_ids(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assign sequential match IDs after sorting matches.
        
        試合リストをkickoff_utc順にソートし、シーケンス番号を付与してmatch_idを生成。
        
        Args:
            matches: List of match dictionaries
            
        Returns:
            Matches with assigned match_ids
        """
        if not matches:
            return matches
        
        # Sort by kickoff_utc
        sorted_matches = sorted(matches, key=lambda m: m.get("kickoff_utc", ""))
        
        # Group by competition_id, season, round
        from collections import defaultdict
        groups = defaultdict(list)
        
        for match in sorted_matches:
            comp_id = match.get("competition_id", "")
            season = match.get("season", "")
            round_num = match.get("round", "")
            key = (comp_id, season, round_num)
            groups[key].append(match)
        
        # Assign sequential IDs within each group
        result = []
        for (comp_id, season, round_num), group_matches in groups.items():
            for seq, match in enumerate(group_matches, start=1):
                # Ensure season and round_num are strings
                match["match_id"] = self._generate_match_id(
                    comp_id, 
                    str(season) if season else "", 
                    str(round_num) if round_num else "", 
                    seq
                )
                result.append(match)
        
        # Return in original sorted order
        return sorted(result, key=lambda m: m.get("kickoff_utc", ""))
    
    @abstractmethod
    def scrape(self):
        pass
    
    def save_to_json(self, data: Union[List[Dict[str, Any]], Dict[str, Any]], filename: str):
        """Save data to JSON file.
        
        新ディレクトリ構造対応 + チーム名自動正規化:
        - filename に大会ID/シーズン形式を使用 (例: "w6n/2026")
        - 旧形式 (例: "six-nations-women") もサポート
        - home_team/away_teamからスポンサー名を自動除去
        """
        # データがリストの場合、各試合のチーム名を正規化
        if isinstance(data, list):
            for match in data:
                if isinstance(match, dict):
                    if "home_team" in match:
                        match["home_team"] = self._normalize_team_name(
                            match["home_team"], 
                            self._competition_id
                        )
                    if "away_team" in match:
                        match["away_team"] = self._normalize_team_name(
                            match["away_team"],
                            self._competition_id
                        )
        
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
        competition_id: str,
        season: str,
        kickoff: Optional[Union[str, datetime]],
        timezone_name: Optional[str],
        venue: str,
        home_team: str,
        away_team: str,
        match_url: str,
        broadcasters: Optional[List[str]] = None,
        round_name: str = "",
        status: str = "",
        match_id: Optional[Union[str, int]] = None,
        home_team_id: Optional[Union[str, int]] = None,
        away_team_id: Optional[Union[str, int]] = None,
    ) -> Dict[str, Any]:
        """Build match data dictionary with normalized fields.
        
        新形式: 14フィールド（メタ情報削除、正規化重視）
        
        Args:
            competition_id: Competition ID (required)
            season: Season (required)
            kickoff: Kickoff datetime
            timezone_name: Timezone name
            venue: Venue name
            home_team: Home team name
            away_team: Away team name
            match_url: Match URL
            broadcasters: Broadcasters list
            round_name: Round name (will be converted to numeric)
            status: Match status
            match_id: Match ID (will be auto-generated if not provided)
            home_team_id: Home team ID (will be auto-resolved if not provided)
            away_team_id: Away team ID (will be auto-resolved if not provided)
            
        Returns:
            Match data dictionary
        """
        kickoff_local, kickoff_utc, tz_name = self._normalize_datetime(kickoff, timezone_name)
        
        # Extract numeric round
        round_num = self._extract_round_number(round_name)
        
        # Auto-resolve team IDs from master if not provided
        if home_team_id is None:
            home_team_id = self._resolve_team_id(home_team, competition_id)
        if away_team_id is None:
            away_team_id = self._resolve_team_id(away_team, competition_id)
        
        # match_id is temporarily empty (will be generated after sorting)
        # シーケンス番号が必要なため、ここでは空文字列
        if match_id is None:
            match_id = ""

        return {
            "match_id": str(match_id) if match_id else "",
            "competition_id": competition_id,
            "season": season,
            "round": round_num,
            "status": status or "",
            "kickoff": kickoff_local or "",
            "kickoff_utc": kickoff_utc or "",
            "timezone": tz_name or "",
            "venue": venue or "",
            "home_team": home_team or "",
            "away_team": away_team or "",
            "home_team_id": str(home_team_id) if home_team_id else "",
            "away_team_id": str(away_team_id) if away_team_id else "",
            "match_url": match_url or "",
            "broadcasters": broadcasters or [],
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
