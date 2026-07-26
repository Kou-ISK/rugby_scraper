#!/usr/bin/env python3
"""
全大会のスクレイピングを実行
"""
import subprocess
import sys
from pathlib import Path

# スクレイピング対象大会（高速→低速の順）
COMPETITIONS = [
    ("wr", "World Rugby Internationals"),
    ("premier", "Gallagher Premiership"),
    ("urc", "United Rugby Championship"),
    ("trc", "The Rugby Championship"),
    ("ans", "Autumn Nations Series"),
    ("nc", "Nations Championship"),
    ("srp", "Super Rugby Pacific"),
    ("epcr-champions", "EPCR Champions Cup"),
    ("epcr-challenge", "EPCR Challenge Cup"),
    ("t14", "Top 14"),
    ("jrlo", "Japan Rugby League One"),
    ("m6n", "Six Nations"),
    ("w6n", "Women's Six Nations"),
    ("u6n", "U20 Six Nations"),
]

def main():
    print("=" * 70)
    print("全大会スクレイピング開始")
    print("=" * 70)
    
    success_count = 0
    failed = []
    
    for comp_id, comp_name in COMPETITIONS:
        print(f"\n{'='*70}")
        print(f"スクレイピング中: {comp_name} ({comp_id})")
        print(f"{'='*70}")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "src.main", comp_id],
                capture_output=True,
                text=True,
                timeout=300  # 5分タイムアウト
            )
            
            if result.returncode == 0:
                print(result.stdout)
                print(f"✅ {comp_name} 完了")
                success_count += 1
            else:
                print(result.stdout)
                print(result.stderr)
                print(f"❌ {comp_name} 失敗")
                failed.append(comp_name)
                
        except subprocess.TimeoutExpired:
            print(f"⏱️ {comp_name} タイムアウト（5分超過）")
            failed.append(comp_name)
        except Exception as e:
            print(f"❌ {comp_name} エラー: {e}")
            failed.append(comp_name)
    
    # サマリー
    print("\n" + "=" * 70)
    print("スクレイピング完了サマリー")
    print("=" * 70)
    print(f"✅ 成功: {success_count}/{len(COMPETITIONS)}大会")
    
    if failed:
        print(f"\n❌ 失敗した大会:")
        for comp in failed:
            print(f"  - {comp}")
    else:
        print("\n🎉 全大会のスクレイピングが成功しました！")
    
    return 0 if not failed else 1

if __name__ == "__main__":
    sys.exit(main())
