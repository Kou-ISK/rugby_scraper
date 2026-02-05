"""
スクレイパーの新ID体系動作確認テスト

BaseScraper の新機能をテスト:
1. チームID解決 (_resolve_team_id)
2. match_id生成
3. 新ディレクトリ構造への保存
"""

import json
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scraper.base import BaseScraper

class TestScraper(BaseScraper):
    """テスト用スクレイパー"""
    def __init__(self, competition_id: str):
        super().__init__()
        self._competition_id = competition_id
    
    def scrape(self):
        """ダミーデータで動作確認"""
        matches = []
        
        # テストデータ: w6n (Women's Six Nations)
        test_data = [
            {
                "home_team": "ENG",
                "away_team": "FRA",
                "kickoff": "2026-03-14T15:00:00",
                "timezone": "Europe/London",
                "venue": "Twickenham Stadium",
            },
            {
                "home_team": "Ireland",  # 正式名でも解決できるかテスト
                "away_team": "Italy",
                "kickoff": "2026-03-14T17:45:00",
                "timezone": "Europe/Dublin",
                "venue": "Aviva Stadium",
            },
        ]
        
        for data in test_data:
            match = self.build_match(
                competition="Women's Six Nations",
                competition_id=self._competition_id,
                season="2026",
                source_name="Test Source",
                source_url="https://test.example.com",
                source_type="test",
                kickoff=data["kickoff"],
                timezone_name=data["timezone"],
                timezone_source="test",
                venue=data["venue"],
                home_team=data["home_team"],
                away_team=data["away_team"],
                match_url="https://test.example.com/match",
            )
            matches.append(match)
        
        return matches

def main():
    print("=" * 60)
    print("新ID体系スクレイパー動作確認")
    print("=" * 60)
    
    # w6n (Women's Six Nations) でテスト
    scraper = TestScraper(competition_id="w6n")
    
    print("\n1. チームマスタ読み込み")
    print(f"   ✅ {len(scraper._team_master)} チーム読み込み済み")
    
    # w6nチームを表示
    w6n_teams = {k: v for k, v in scraper._team_master.items() if k.startswith('w6n-')}
    print(f"\n   w6n チーム:")
    for team_id in sorted(w6n_teams.keys()):
        team = w6n_teams[team_id]
        print(f"     {team_id}: {team['short_name']} - {team['name']}")
    
    print("\n2. スクレイピング実行（テストデータ）")
    matches = scraper.scrape()
    print(f"   ✅ {len(matches)} 試合生成")
    
    print("\n3. 生成されたデータ検証")
    for i, match in enumerate(matches, 1):
        print(f"\n   試合 #{i}:")
        print(f"     competition_id: {match['competition_id']}")
        print(f"     home_team: {match['home_team']} (ID: {match['home_team_id']})")
        print(f"     away_team: {match['away_team']} (ID: {match['away_team_id']})")
        print(f"     match_id: {match['match_id'][:50]}..." if len(match['match_id']) > 50 else f"     match_id: {match['match_id']}")
        print(f"     kickoff: {match['kickoff']}")
        print(f"     kickoff_utc: {match['kickoff_utc']}")
        
        # チームID解決の検証
        if not match['home_team_id']:
            print(f"     ⚠️ home_team_id が空です")
        if not match['away_team_id']:
            print(f"     ⚠️ away_team_id が空です")
        if not match['match_id']:
            print(f"     ⚠️ match_id が空です")
    
    # 4. 新ディレクトリ構造へ保存テスト
    print("\n4. 保存テスト（data/matches/w6n/2026-test.json）")
    test_output_dir = Path("data/matches/w6n")
    test_output_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = test_output_dir / "2026-test.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)
        f.write("\n")
    
    print(f"   ✅ 保存完了: {test_file}")
    print(f"   ファイルサイズ: {test_file.stat().st_size} bytes")
    
    print("\n" + "=" * 60)
    print("✅ すべてのテスト完了")
    print("=" * 60)

if __name__ == "__main__":
    main()
