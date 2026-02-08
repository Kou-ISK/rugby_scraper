#!/usr/bin/env python3
"""
Clear teams.json to prepare for re-generation with correct IDs.

This script resets teams.json to an empty state, so that scraping will
automatically regenerate team IDs in the correct format:
- National teams: NT-M-ENG, NT-W-IRE, etc.
- Club teams: {comp_id}-{slug} (e.g., gp-bath, ecc-clermont)
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
    print("1. 全大会をスクレイピングして、チームIDを自動生成")
    print("2. extract_all_teams.py を実行して、チームマスタを更新")

if __name__ == "__main__":
    main()
