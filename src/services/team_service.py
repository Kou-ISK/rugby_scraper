"""
【legacy】全試合データからチーム名を抽出してteams.jsonマスタを生成

【重要】ID安定性保証:
- 既存チームのIDは絶対に変更しない
- 新チームのみ新IDを採番（最大ID+1から）
- チーム名での照合（大文字小文字無視、空白正規化）

【ロゴ取得】:
- 非推奨（TheSportsDB API）
- 公式ロゴは team_master_service で取得

【重複検出】:
- スポンサー名違いの同一チーム検出
- マージ推奨レポート生成
"""

import json
import re
from pathlib import Path
from collections import defaultdict
import requests
import time

ROOT = Path(__file__).resolve().parents[2]
MATCHES_DIR = ROOT / "data" / "matches"
TEAMS_JSON = ROOT / "data" / "teams.json"
DUPLICATES_REPORT = ROOT / "data" / "team_duplicates_report.json"

# TheSportsDB API設定
THESPORTSDB_API_KEY = "3"  # 無料プランのキー
THESPORTSDB_BASE_URL = "https://www.thesportsdb.com/api/v1/json"

# 大会ID・略称マッピング（新形式対応）
COMPETITION_IDS = {
    "six-nations": "m6n",
    "six-nations-women": "w6n",
    "six-nations-u20": "u6n",
    "league-one": "jrlo-div1",  # Division 1がデフォルト
    "top14": "t14",
    "premier": "premier",
    "urc": "urc",
    "epcr-champions": "epcr-champions",
    "epcr-challenge": "epcr-challenge",
    "super-rugby-pacific": "srp",
    "rugby-championship": "trc",
    "autumn-nations-series": "ans",
    "wr": "wr",
}

# 国際大会の定義（BaseScraper.INTERNATIONAL_COMPETITIONSと同期）
INTERNATIONAL_COMPETITIONS = {
    "m6n": "M",      # Six Nations (Men)
    "w6n": "W",      # Six Nations (Women)
    "u6n": "U20",    # Six Nations U20
    "trc": "M",      # The Rugby Championship
    "ans": "M",      # Autumn Nations Series
    "wr": "M",       # World Rugby Internationals
}

# 国コードマッピング（BaseScraper.COUNTRY_CODESと同期）
COUNTRY_CODES = {
    # Six Nations
    "ENGLAND": "ENG", "England": "ENG", "ENG": "ENG",
    "FRANCE": "FRA", "France": "FRA", "FRA": "FRA",
    "IRELAND": "IRE", "Ireland": "IRE", "IRE": "IRE",
    "ITALY": "ITA", "Italy": "ITA", "ITA": "ITA",
    "SCOTLAND": "SCO", "Scotland": "SCO", "SCO": "SCO",
    "WALES": "WAL", "Wales": "WAL", "WAL": "WAL",
    # The Rugby Championship
    "ARGENTINA": "ARG", "Argentina": "ARG", "ARG": "ARG",
    "AUSTRALIA": "AUS", "Australia": "AUS", "AUS": "AUS",
    "NEW ZEALAND": "NZL", "New Zealand": "NZL", "NZL": "NZL",
    "SOUTH AFRICA": "RSA", "South Africa": "RSA", "RSA": "RSA",
    # Others
    "JAPAN": "JPN", "Japan": "JPN", "JPN": "JPN",
    "FIJI": "FIJ", "Fiji": "FIJ", "FIJ": "FIJ",
    "CHILE": "CHI", "Chile": "CHI", "CHI": "CHI",
    "USA": "USA",
}


def normalize_team_name(name):
    """チーム名を正規化（比較用）"""
    if not name:
        return ""
    # 大文字化、空白正規化、記号除去
    normalized = name.upper().strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return normalized


def extract_national_team_variant_suffix(team_name):
    """代表チームのバリエーション接尾辞を抽出（BaseScraperと同じロジック）"""
    if not team_name:
        return ""
    
    # A代表、XV代表等のパターン
    variant_patterns = [
        (r'\s+A$', 'A'),
        (r'\s+XV$', 'XV'),
        (r'\s+Barbarians$', 'Barbarians'),
        (r'\s+Development$', 'Dev'),
    ]
    
    for pattern, suffix in variant_patterns:
        if re.search(pattern, team_name, re.IGNORECASE):
            return suffix
    
    return ""


def generate_national_team_id(team_name, comp_id):
    """国代表チームIDを生成（BaseScraper._generate_national_team_idと同じロジック）
    
    Returns:
        NT-{M|W|U20}-{ENG|FRA|...}[-{A|XV|...}] 形式のID、または空文字列
    """
    if not team_name or comp_id not in INTERNATIONAL_COMPETITIONS:
        return ""
    
    # 1. カテゴリ取得
    category = INTERNATIONAL_COMPETITIONS[comp_id]
    
    # 2. バリエーション抽出
    variant = extract_national_team_variant_suffix(team_name)
    base_name = re.sub(r'\s+(A|XV|Barbarians|Development)$', '', team_name, flags=re.IGNORECASE).strip()
    
    # 3. 国コード取得
    country_code = COUNTRY_CODES.get(base_name, "")
    if not country_code:
        # 大文字化で再試行
        country_code = COUNTRY_CODES.get(base_name.upper(), "")
    
    if not country_code:
        return ""
    
    # 4. ID生成
    if variant:
        return f"NT-{category}-{country_code}-{variant}"
    else:
        return f"NT-{category}-{country_code}"


def get_base_team_name(name):
    """スポンサー名を除去してベースチーム名を取得"""
    # スポンサー名パターン（BaseScraper.SPONSOR_PATTERNSと同期）
    sponsor_patterns = [
        # 先頭のスポンサー名
        r'^DHL\s+',
        r'^ISUZU\s+',
        r'^GALLAGHER\s+',
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
    
    base_name = name
    for pattern in sponsor_patterns:
        base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
    
    return base_name.strip()


def is_placeholder_team(team_name: str) -> bool:
    if not team_name:
        return False
    placeholders = [
        "リーグ戦",
        "準々決勝",
        "準決勝",
        "決勝",
    ]
    return any(p in team_name for p in placeholders)


def fetch_team_logo(team_name, comp_id):
    """TheSportsDB APIからチームロゴを取得"""
    try:
        # ベースチーム名を使用
        search_name = get_base_team_name(team_name)

        data = _fetch_logo_payload(search_name)
        if data:
            teams = data.get("teams")
            if teams and len(teams) > 0:
                team = teams[0]
                logo_url = team.get("strTeamBadge") or team.get("strTeamLogo") or ""
                badge_url = team.get("strTeamBanner") or ""
                return logo_url, badge_url

        return "", ""

    except Exception as e:
        print(f"    ⚠️ ロゴ取得エラー ({team_name}): {e}")
        return "", ""


def _fetch_logo_payload(search_name: str):
    url = f"{THESPORTSDB_BASE_URL}/{THESPORTSDB_API_KEY}/searchteams.php"
    params = {"t": search_name}
    backoffs = [1.0, 2.0, 4.0]
    last_error = None
    for idx, backoff in enumerate(backoffs, 1):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 429:
                time.sleep(backoff)
                last_error = f"429 Too Many Requests (attempt {idx})"
                continue
            response.raise_for_status()
            time.sleep(0.5)  # APIレート制限対策（基本待機）
            return response.json()
        except Exception as e:  # noqa: BLE001
            last_error = e
            time.sleep(backoff)
            continue
    raise last_error


def fetch_logo_from_thesportsdb(team_name: str):
    """update_team_logos用: TheSportsDB APIからロゴ取得"""
    try:
        search_name = get_base_team_name(team_name)
        data = _fetch_logo_payload(search_name)
        if not data:
            return {"logo_url": "", "badge_url": ""}
        teams = data.get("teams")
        if teams and len(teams) > 0:
            team = teams[0]
            logo_url = team.get("strTeamBadge") or team.get("strTeamLogo") or ""
            badge_url = team.get("strTeamBanner") or ""
            return {"logo_url": logo_url, "badge_url": badge_url}
        return {"logo_url": "", "badge_url": ""}
    except Exception as e:
        print(f"  ⚠️ ロゴ取得エラー ({team_name}): {e}")
        return {"logo_url": "", "badge_url": ""}


def load_existing_teams():
    """既存teams.jsonを読み込み"""
    if not TEAMS_JSON.exists():
        return {}
    
    with open(TEAMS_JSON, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ teams.json が空/壊れています。空のマスタとして再生成します。")
            return {}


def extract_teams_from_matches():
    """全試合データからチーム名を抽出"""
    teams_by_comp = defaultdict(set)
    
    for comp_dir in sorted(MATCHES_DIR.iterdir()):
        if not comp_dir.is_dir():
            continue
        
        comp_id = comp_dir.name
        print(f"\n大会: {comp_id}")
        
        for match_file in sorted(comp_dir.glob("*.json")):
            try:
                with open(match_file, 'r', encoding='utf-8') as f:
                    matches = json.load(f)
                
                for match in matches:
                    home_team = match.get("home_team", "").strip()
                    away_team = match.get("away_team", "").strip()

                    if comp_id.startswith("jrlo") and is_placeholder_team(home_team):
                        home_team = ""
                    if comp_id.startswith("jrlo") and is_placeholder_team(away_team):
                        away_team = ""
                    
                    if home_team:
                        teams_by_comp[comp_id].add(home_team)
                    if away_team:
                        teams_by_comp[comp_id].add(away_team)
            
            except Exception as e:
                print(f"  ⚠️ エラー ({match_file.name}): {e}")
    
    # setをsortedリストに変換
    for comp_id in teams_by_comp:
        teams_by_comp[comp_id] = sorted(teams_by_comp[comp_id])
        print(f"  {comp_id}: {len(teams_by_comp[comp_id])}チーム")
    
    return dict(teams_by_comp)


def detect_duplicates(teams_by_comp):
    """重複チームを検出（スポンサー名違い等）"""
    duplicates = []
    
    for comp_id, team_names in teams_by_comp.items():
        # ベース名でグループ化
        base_to_teams = defaultdict(list)
        
        for name in team_names:
            base_name = normalize_team_name(get_base_team_name(name))
            if base_name:
                base_to_teams[base_name].append(name)
        
        # 2つ以上あるものが重複候補
        for base_name, names in base_to_teams.items():
            if len(names) > 1:
                duplicates.append({
                    "competition_id": comp_id,
                    "base_name": base_name,
                    "variations": names,
                    "suggestion": f"統合推奨: {names[0]} を代表とする"
                })
    
    return duplicates


def generate_team_master(teams_by_comp, existing_teams, fetch_logos=False, official_logos_by_comp=None):
    """チームマスタを生成（ID安定性保証）"""
    
    # 既存チームをチーム名で索引化（正規化名でマッピング）
    existing_by_name = {}
    existing_by_id = {}
    
    for team_id, team_data in existing_teams.items():
        name = team_data.get("name", "")
        comp_id = team_data.get("competition_id", "")
        
        if name and comp_id:
            key = (comp_id, normalize_team_name(name))
            existing_by_name[key] = team_id
            existing_by_id[team_id] = team_data
    
    # 大会別の最大ID番号を取得
    max_id_by_comp = defaultdict(int)
    for team_id in existing_teams.keys():
        if "_" in team_id:
            comp_prefix, num_str = team_id.rsplit("_", 1)
            try:
                num = int(num_str)
                max_id_by_comp[comp_prefix] = max(max_id_by_comp[comp_prefix], num)
            except ValueError:
                pass
    
    # 新チームマスタ
    new_teams = {}
    added_count = 0
    preserved_count = 0
    
    for comp_id, team_names in sorted(teams_by_comp.items()):
        print(f"\n大会: {comp_id}")
        official_logos = (official_logos_by_comp or {}).get(comp_id, {})
        
        for team_name in team_names:
            # 国際大会の場合、NT-*形式のIDを生成
            if comp_id in INTERNATIONAL_COMPETITIONS:
                team_id = generate_national_team_id(team_name, comp_id)
                
                if not team_id:
                    # ID生成失敗（国コードが見つからない等）
                    print(f"  ⚠️ {team_name}: 国代表ID生成失敗（スキップ）")
                    continue
                
                # 既存チーム確認
                if team_id in existing_by_id:
                    # 既存チーム: IDを保持
                    team_data = existing_by_id[team_id]
                    official = official_logos.get(team_name)
                    if official and official.get("logo_url"):
                        team_data = {
                            **team_data,
                            "logo_url": official.get("logo_url", ""),
                            "badge_url": official.get("badge_url", official.get("logo_url", "")),
                        }
                    new_teams[team_id] = team_data
                    preserved_count += 1
                    if not fetch_logos:
                        print(f"  ✓ {team_id}: {team_name} (既存ID保持)")
                else:
                    # 新規国代表チーム
                    official = official_logos.get(team_name, {})
                    logo_url = official.get("logo_url", "")
                    badge_url = official.get("badge_url", official.get("logo_url", ""))
                    print(f"  ➕ {team_id}: {team_name} (新規追加)")
                    
                    new_teams[team_id] = {
                        "id": team_id,
                        "competition_id": comp_id,
                        "name": team_name,
                        "name_ja": "",
                        "short_name": team_name,
                        "country": "",
                        "division": "",
                        "logo_url": logo_url,
                        "badge_url": badge_url,
                    }
                    added_count += 1
            
            else:
                # クラブチーム: 既存ロジック（{comp_id}_{num}形式）
                # 既存チーム確認
                key = (comp_id, normalize_team_name(team_name))
                
                if key in existing_by_name:
                    # 既存チーム: IDを保持
                    team_id = existing_by_name[key]
                    team_data = existing_by_id[team_id]
                    official = official_logos.get(team_name)
                    if official and official.get("logo_url"):
                        team_data = {
                            **team_data,
                            "logo_url": official.get("logo_url", ""),
                            "badge_url": official.get("badge_url", official.get("logo_url", "")),
                        }
                    new_teams[team_id] = team_data
                    preserved_count += 1
                    if not fetch_logos:
                        print(f"  ✓ {team_id}: {team_name} (既存ID保持)")
                
                else:
                    # 新チーム: 新ID採番
                    max_id_by_comp[comp_id] += 1
                    team_id = f"{comp_id}_{max_id_by_comp[comp_id]}"
                    
                    # ロゴ取得
                    official = official_logos.get(team_name, {})
                    logo_url = official.get("logo_url", "")
                    badge_url = official.get("badge_url", official.get("logo_url", ""))
                    print(f"  ➕ {team_id}: {team_name} (新規追加)")
                    
                    new_teams[team_id] = {
                        "id": team_id,
                        "competition_id": comp_id,
                        "name": team_name,
                        "name_ja": "",
                        "short_name": team_name,
                        "country": "",
                        "division": "",
                        "logo_url": logo_url,
                        "badge_url": badge_url,
                    }
                    
                    added_count += 1
    
    return new_teams, added_count, preserved_count


def update_team_logos():
    """Deprecated: logos are now sourced from official sites during master update."""
    print("=" * 60)
    print("update-logos は非推奨です")
    print("ロゴは update-team-master 内で公式サイトから取得してください。")
    print("=" * 60)
    return


def main():
    print("=" * 60)
    print("チームマスタ更新（ID安定性保証 + ロゴ取得）")
    print("=" * 60)
    
    # 既存teams.json読み込み
    existing_teams = load_existing_teams()
    print(f"\n既存teams.json: {len(existing_teams)}チーム")
    
    # 全試合データからチーム抽出
    print("\n全試合データをスキャン中...")
    teams_by_comp = extract_teams_from_matches()
    
    total_unique = sum(len(names) for names in teams_by_comp.values())
    print(f"\n✅ 抽出完了: {total_unique}ユニークチーム")
    
    # 重複検出
    print("\n重複チーム検出中...")
    duplicates = detect_duplicates(teams_by_comp)
    
    if duplicates:
        print(f"\n⚠️ {len(duplicates)}件の重複候補を検出")
        for dup in duplicates[:5]:  # 最初の5件表示
            print(f"  {dup['competition_id']}: {', '.join(dup['variations'])}")
        
        # 重複レポート保存
        with open(DUPLICATES_REPORT, 'w', encoding='utf-8') as f:
            json.dump(duplicates, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"\n詳細レポート: {DUPLICATES_REPORT}")
    
    # チームマスタ生成（ロゴ取得は別コマンドで実施）
    print("\nチームマスタ生成中（ロゴ取得は別コマンドで実施）...")
    
    new_teams, added_count, preserved_count = generate_team_master(
        teams_by_comp, 
        existing_teams,
        fetch_logos=False  # ロゴ取得は別コマンドで実施
    )
    
    # 保存
    with open(TEAMS_JSON, 'w', encoding='utf-8') as f:
        json.dump(new_teams, f, ensure_ascii=False, indent=2)
        f.write("\n")
    
    print("\n" + "=" * 60)
    print("✅ teams.json 更新完了")
    print("=" * 60)
    print(f"総チーム数: {len(new_teams)}")
    print(f"  - 既存ID保持: {preserved_count}")
    print(f"  - 新規追加: {added_count}")
    
    if duplicates:
        print(f"\n⚠️ 重複候補: {len(duplicates)}件")
        print(f"   レポート: {DUPLICATES_REPORT}")


if __name__ == "__main__":
    main()
