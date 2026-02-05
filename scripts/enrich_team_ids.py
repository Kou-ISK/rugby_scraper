"""
移行済みデータにチームIDを付与

新ID形式でteam_idを解決して既存データを更新
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAMS_JSON = ROOT / "data" / "teams.json"
MATCHES_DIR = ROOT / "data" / "matches"

def load_team_master():
    """teams.jsonを読み込み"""
    if not TEAMS_JSON.exists():
        print(f"❌ teams.json not found: {TEAMS_JSON}")
        sys.exit(1)
    
    with open(TEAMS_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def resolve_team_id(team_name: str, competition_id: str, team_master: dict) -> str:
    """チーム名からチームIDを解決"""
    if not team_name:
        return ""
    
    # 指定大会のチームから検索
    for team_id, team_data in team_master.items():
        if team_data.get("competition_id") == competition_id:
            # short_name または name が一致するかチェック
            if team_name.upper() == team_data.get("short_name", "").upper():
                return team_id
            if team_name.lower() == team_data.get("name", "").lower():
                return team_id
    
    return ""

def enrich_matches_in_file(file_path: Path, team_master: dict) -> int:
    """1つのファイル内の試合データにチームIDを付与"""
    with open(file_path, 'r', encoding='utf-8') as f:
        matches = json.load(f)
    
    if not matches:
        return 0
    
    updated_count = 0
    for match in matches:
        comp_id = match.get("competition_id", "")
        home_team = match.get("home_team", "")
        away_team = match.get("away_team", "")
        
        # home_team_id
        if not match.get("home_team_id") and home_team:
            team_id = resolve_team_id(home_team, comp_id, team_master)
            if team_id:
                match["home_team_id"] = team_id
                updated_count += 1
        
        # away_team_id
        if not match.get("away_team_id") and away_team:
            team_id = resolve_team_id(away_team, comp_id, team_master)
            if team_id:
                match["away_team_id"] = team_id
                updated_count += 1
    
    # 更新されたデータを書き戻し
    if updated_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)
            f.write("\n")
    
    return updated_count

def main():
    print("=" * 60)
    print("移行済みデータへのチームID付与")
    print("=" * 60)
    
    # teams.jsonを読み込み
    team_master = load_team_master()
    print(f"✅ チームマスタ読み込み: {len(team_master)}チーム\n")
    
    # 各大会ディレクトリを処理
    total_updated = 0
    for comp_dir in sorted(MATCHES_DIR.iterdir()):
        if not comp_dir.is_dir():
            continue
        
        comp_id = comp_dir.name
        print(f"📁 {comp_id}/")
        
        for json_file in sorted(comp_dir.glob("*.json")):
            updated = enrich_matches_in_file(json_file, team_master)
            if updated > 0:
                print(f"  ✅ {json_file.name}: {updated}箇所更新")
                total_updated += updated
            else:
                # ファイル内の試合数を確認
                with open(json_file, 'r', encoding='utf-8') as f:
                    matches = json.load(f)
                print(f"  ⏭️  {json_file.name}: {len(matches)}試合 (更新なし)")
    
    print(f"\n✅ 完了: 合計{total_updated}箇所のチームIDを付与しました")

if __name__ == "__main__":
    main()
