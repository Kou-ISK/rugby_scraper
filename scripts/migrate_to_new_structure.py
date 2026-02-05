"""
既存の試合データを新しいディレクトリ構造へ移行

旧構造: data/matches/{competition-name}.json
新構造: data/matches/{comp_id}/{season}.json

例:
  data/matches/six-nations-women.json
  → data/matches/w6n/2025.json, data/matches/w6n/2026.json
"""

import json
import shutil
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
OLD_MATCHES_DIR = ROOT / "data" / "matches"
NEW_MATCHES_DIR = ROOT / "data" / "matches"

# 大会ID変換マップ
COMPETITION_ID_MAP = {
    "six-nations": "m6n",
    "six-nations-women": "w6n",
    "six-nations-u20": "u6n",
    "league-one": "jrlo",
    "top14": "t14",
    "gallagher-premiership": "gp",
    "urc": "urc",
    "epcr-champions": "ecc",
    "epcr-challenge": "ech",
    "super-rugby-pacific": "srp",
    "rugby-championship": "trc",
    "autumn-nations-series": "ans",
    "world-rugby-internationals": "wri",
}

def migrate_matches():
    """既存の試合データを新ディレクトリに移行"""
    
    # 旧ファイル一覧を取得
    old_files = list(OLD_MATCHES_DIR.glob("*.json"))
    
    if not old_files:
        print("移行対象のファイルがありません")
        return
    
    print(f"移行対象ファイル: {len(old_files)}個")
    
    # 一時ディレクトリにバックアップ
    backup_dir = OLD_MATCHES_DIR.parent / "matches_backup"
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir(exist_ok=True)
    
    for old_file in old_files:
        shutil.copy2(old_file, backup_dir / old_file.name)
    print(f"バックアップ作成: {backup_dir}")
    
    # 各ファイルを処理
    for old_file in old_files:
        old_comp_id = old_file.stem  # six-nations-women
        new_comp_id = COMPETITION_ID_MAP.get(old_comp_id)
        
        if not new_comp_id:
            print(f"⚠️  スキップ: {old_file.name} (マッピング未定義)")
            continue
        
        # ファイルを読み込み
        with open(old_file, 'r', encoding='utf-8') as f:
            matches = json.load(f)
        
        if not matches:
            print(f"⚠️  スキップ: {old_file.name} (試合データなし)")
            continue
        
        # シーズン別にグループ化
        by_season = defaultdict(list)
        for match in matches:
            season = match.get("season", "unknown")
            # competition_idを新IDに更新
            match["competition_id"] = new_comp_id
            by_season[season].append(match)
        
        # 新ディレクトリに保存
        new_dir = NEW_MATCHES_DIR / new_comp_id
        new_dir.mkdir(parents=True, exist_ok=True)
        
        for season, season_matches in by_season.items():
            new_file = new_dir / f"{season}.json"
            with open(new_file, 'w', encoding='utf-8') as f:
                json.dump(season_matches, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print(f"✅ {old_file.name} → {new_comp_id}/{season}.json ({len(season_matches)}試合)")
        
        # 旧ファイルを削除
        old_file.unlink()
    
    print(f"\n✅ 移行完了")
    print(f"バックアップ: {backup_dir}")
    print(f"新構造: {NEW_MATCHES_DIR}")

def main():
    print("=" * 60)
    print("試合データ移行スクリプト")
    print("=" * 60)
    migrate_matches()
    
    # 新構造の確認
    print("\n新しいディレクトリ構造:")
    for comp_dir in sorted(NEW_MATCHES_DIR.iterdir()):
        if comp_dir.is_dir():
            files = list(comp_dir.glob("*.json"))
            total_matches = 0
            for f in files:
                with open(f, 'r', encoding='utf-8') as fp:
                    matches = json.load(fp)
                    total_matches += len(matches)
            print(f"  {comp_dir.name}/: {len(files)}ファイル, {total_matches}試合")

if __name__ == "__main__":
    main()
