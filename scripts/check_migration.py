"""新ディレクトリ構造とチームIDの確認スクリプト"""
import json
from pathlib import Path

def check_migration():
    print("=" * 60)
    print("マイグレーション結果の確認")
    print("=" * 60)
    
    # 1. teams.jsonの確認
    teams_file = Path('data/teams.json')
    if teams_file.exists():
        with open(teams_file, 'r', encoding='utf-8') as f:
            teams = json.load(f)
        print(f"\n✅ teams.json: {len(teams)}チーム")
        
        # 大会別チーム数を集計
        by_comp = {}
        for team_id, team_data in teams.items():
            comp_id = team_data.get('competition_id', 'unknown')
            by_comp[comp_id] = by_comp.get(comp_id, 0) + 1
        
        print("\n大会別チーム数:")
        for comp_id, count in sorted(by_comp.items()):
            print(f"  {comp_id}: {count}チーム")
        
        # w6nチームの詳細表示
        w6n_teams = {k: v for k, v in teams.items() if k.startswith('w6n-')}
        print(f"\nw6n (Women's Six Nations) チーム:")
        for team_id in sorted(w6n_teams.keys()):
            team = w6n_teams[team_id]
            print(f"  {team_id}: {team['name']} ({team['short_name']}) - {team['name_ja']}")
    else:
        print("❌ teams.json が見つかりません")
    
    # 2. 新ディレクトリ構造の確認
    matches_dir = Path('data/matches')
    print(f"\n新ディレクトリ構造:")
    for comp_dir in sorted(matches_dir.iterdir()):
        if comp_dir.is_dir():
            files = list(comp_dir.glob("*.json"))
            total_matches = 0
            for f in files:
                with open(f, 'r', encoding='utf-8') as fp:
                    matches = json.load(fp)
                    total_matches += len(matches)
            print(f"  {comp_dir.name}/: {len(files)}ファイル, {total_matches}試合")
    
    # 3. w6n/2026.jsonの詳細確認
    w6n_file = Path('data/matches/w6n/2026.json')
    if w6n_file.exists():
        with open(w6n_file, 'r', encoding='utf-8') as f:
            matches = json.load(f)
        print(f"\n✅ w6n/2026.json の詳細:")
        print(f"  試合数: {len(matches)}")
        if matches:
            m = matches[0]
            print(f"\n  サンプル試合:")
            print(f"    competition_id: {m.get('competition_id')}")
            print(f"    season: {m.get('season')}")
            print(f"    home_team: {m.get('home_team')} (ID: {m.get('home_team_id')})")
            print(f"    away_team: {m.get('away_team')} (ID: {m.get('away_team_id')})")
            print(f"    venue: {m.get('venue')}")
            print(f"    kickoff: {m.get('kickoff')}")
            
            # チームID解決状況を確認
            unresolved = []
            for match in matches:
                if not match.get('home_team_id'):
                    unresolved.append(match.get('home_team'))
                if not match.get('away_team_id'):
                    unresolved.append(match.get('away_team'))
            
            if unresolved:
                print(f"\n  ⚠️ チームID未解決: {len(unresolved)}件")
                print(f"    未解決チーム: {set(unresolved)}")
            else:
                print(f"\n  ✅ すべてのチームIDが解決されています")
    else:
        print("❌ w6n/2026.json が見つかりません")

if __name__ == "__main__":
    check_migration()
