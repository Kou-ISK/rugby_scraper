"""
チーム重複の詳細分析

原因特定:
1. 試合データ内でのチーム名表記パターン調査
2. スポンサー名のバリエーション分析
3. 統合推奨チームのマッピング生成
"""

import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
TEAMS_JSON = ROOT / "data" / "teams.json"
MATCHES_DIR = ROOT / "data" / "matches"
ANALYSIS_REPORT = ROOT / "data" / "duplicate_analysis_report.json"


def normalize_team_name(name):
    """チーム名を正規化（比較用）"""
    if not name:
        return ""
    normalized = name.upper().strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return normalized


def get_base_team_name(name):
    """スポンサー名を除去してベースチーム名を取得"""
    sponsor_patterns = [
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


def load_teams():
    """teams.json読み込み"""
    with open(TEAMS_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_duplicates_in_teams(teams):
    """teams.json内の重複を分析"""
    by_comp = defaultdict(lambda: defaultdict(list))
    
    for team_id, team_data in teams.items():
        comp_id = team_data.get("competition_id", "")
        name = team_data.get("name", "")
        
        if comp_id and name:
            base_name = normalize_team_name(get_base_team_name(name))
            by_comp[comp_id][base_name].append({
                "id": team_id,
                "name": name,
                "base_name": base_name,
            })
    
    # 重複のみ抽出
    duplicates = {}
    for comp_id, base_teams in by_comp.items():
        comp_dups = []
        for base_name, team_list in base_teams.items():
            if len(team_list) > 1:
                comp_dups.append({
                    "base_name": base_name,
                    "count": len(team_list),
                    "teams": team_list,
                    "primary_id": team_list[0]["id"],  # 最初のIDを代表とする
                    "merge_candidates": [t["id"] for t in team_list[1:]],
                })
        
        if comp_dups:
            duplicates[comp_id] = comp_dups
    
    return duplicates


def analyze_match_data_usage(duplicates):
    """試合データでの使用状況を分析"""
    usage_stats = defaultdict(lambda: defaultdict(int))
    
    for comp_dir in MATCHES_DIR.iterdir():
        if not comp_dir.is_dir():
            continue
        
        comp_id = comp_dir.name
        
        for match_file in comp_dir.glob("*.json"):
            try:
                with open(match_file, 'r', encoding='utf-8') as f:
                    matches = json.load(f)
                
                for match in matches:
                    home = match.get("home_team", "")
                    away = match.get("away_team", "")
                    
                    if home:
                        usage_stats[comp_id][home] += 1
                    if away:
                        usage_stats[comp_id][away] += 1
            
            except Exception as e:
                print(f"⚠️ エラー ({match_file}): {e}")
    
    return dict(usage_stats)


def generate_merge_plan(duplicates, usage_stats):
    """統合計画を生成"""
    merge_plan = []
    
    for comp_id, dup_list in duplicates.items():
        for dup in dup_list:
            teams = dup["teams"]
            
            # 使用頻度を取得
            for team in teams:
                team_name = team["name"]
                team["usage_count"] = usage_stats.get(comp_id, {}).get(team_name, 0)
            
            # 使用頻度順にソート
            teams.sort(key=lambda x: x["usage_count"], reverse=True)
            
            # 最も使われているチーム名を代表とする
            primary = teams[0]
            merge_candidates = teams[1:]
            
            merge_plan.append({
                "competition_id": comp_id,
                "base_name": dup["base_name"],
                "primary_team": {
                    "id": primary["id"],
                    "name": primary["name"],
                    "usage_count": primary["usage_count"],
                },
                "merge_targets": [
                    {
                        "id": t["id"],
                        "name": t["name"],
                        "usage_count": t["usage_count"],
                    }
                    for t in merge_candidates
                ],
                "name_mappings": {
                    t["name"]: primary["name"]
                    for t in teams
                },
            })
    
    return merge_plan


def main():
    print("=" * 60)
    print("チーム重複の詳細分析")
    print("=" * 60)
    
    # teams.json読み込み
    teams = load_teams()
    print(f"\n総チーム数: {len(teams)}")
    
    # 重複分析
    print("\n【teams.json内の重複分析】")
    duplicates = analyze_duplicates_in_teams(teams)
    
    total_dups = sum(len(dups) for dups in duplicates.values())
    total_redundant = sum(
        sum(d["count"] - 1 for d in dups)
        for dups in duplicates.values()
    )
    
    print(f"重複グループ数: {total_dups}")
    print(f"冗長チーム数: {total_redundant}")
    
    for comp_id, dups in duplicates.items():
        print(f"\n{comp_id}:")
        for dup in dups:
            print(f"  {dup['base_name']}: {dup['count']}チーム")
            for team in dup["teams"]:
                print(f"    - {team['id']}: {team['name']}")
    
    # 試合データでの使用状況
    print("\n【試合データでのチーム名使用状況を分析中...】")
    usage_stats = analyze_match_data_usage(duplicates)
    
    # 統合計画生成
    print("\n【統合計画生成中...】")
    merge_plan = generate_merge_plan(duplicates, usage_stats)
    
    # レポート保存
    report = {
        "summary": {
            "total_teams": len(teams),
            "duplicate_groups": total_dups,
            "redundant_teams": total_redundant,
            "teams_after_merge": len(teams) - total_redundant,
        },
        "duplicates_by_competition": duplicates,
        "merge_plan": merge_plan,
    }
    
    with open(ANALYSIS_REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    
    print(f"\n✅ 詳細レポート保存: {ANALYSIS_REPORT}")
    
    # サマリー表示
    print("\n" + "=" * 60)
    print("統合後の予測")
    print("=" * 60)
    print(f"現在のチーム数: {len(teams)}")
    print(f"削除予定: {total_redundant}チーム")
    print(f"統合後: {len(teams) - total_redundant}チーム")
    
    print("\n【統合計画サマリー】")
    for plan in merge_plan[:10]:  # 最初の10件表示
        primary = plan["primary_team"]
        merge_count = len(plan["merge_targets"])
        print(f"\n{plan['competition_id']} - {plan['base_name']}:")
        print(f"  代表: {primary['id']} ({primary['name']}) - {primary['usage_count']}回使用")
        print(f"  統合対象: {merge_count}チーム")
        for target in plan["merge_targets"]:
            print(f"    - {target['id']} ({target['name']}) - {target['usage_count']}回使用")


if __name__ == "__main__":
    main()
