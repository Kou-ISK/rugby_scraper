#!/usr/bin/env python3
"""
Clear teams.json to prepare for re-generation with correct IDs.

This script resets teams.json to an empty state, so that scraping will
regenerate team IDs in the correct format (manual update required):
- National teams: NT_M_ENG, NT_W_IRE, etc.
- Club teams: {comp_id}_{num} (e.g., premier_1, epcr-champions_3)
"""

import json
from pathlib import Path

def main():
    teams_file = Path(__file__).parent.parent.parent / "data" / "teams.json"
    
    # Create empty teams.json
    empty_teams = {}
    
    with open(teams_file, 'w', encoding='utf-8') as f:
        json.dump(empty_teams, f, ensure_ascii=False, indent=2)
        f.write("\n")
    
    print("✅ teams.json cleared - ready for re-generation")
    print("\n次のステップ:")
    print("1. 全大会をスクレイピングして試合データを取得")
    print("2. python -m src.main extract-teams を実行してチームマスタを更新")

if __name__ == "__main__":
    main()
