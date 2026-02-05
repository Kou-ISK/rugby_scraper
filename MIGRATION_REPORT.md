# データ構造マイグレーション完了レポート

## 📊 マイグレーション概要

既存のrugby_scraperデータを新しいRESTful設計のディレクトリ構造に移行しました。

### 主な変更点

1. **チームID体系の変更**
   - 旧: `eng`, `fra`, `black-rams-tokyo` (統一性なし)
   - 新: `m6n-1`, `w6n-2`, `jrlo-1` (大会略称-番号形式)

2. **大会ID体系の統一**
   - 旧: `six-nations`, `six-nations-women`, `league-one` (kebab-case)
   - 新: `m6n`, `w6n`, `jrlo` (略称コード、性別明示)

3. **ディレクトリ構造の変更**
   - 旧: `data/matches/{competition-name}.json` (フラット)
   - 新: `data/matches/{comp_id}/{season}.json` (階層化)

---

## 🆔 新ID体系

### 大会ID一覧

| 旧ID | 新ID | 正式名称 | 説明 |
|------|------|----------|------|
| six-nations | **m6n** | Men's Six Nations | 男子シックスネーションズ |
| six-nations-women | **w6n** | Women's Six Nations | 女子シックスネーションズ |
| six-nations-u20 | **u6n** | U20 Six Nations | U20シックスネーションズ |
| league-one | **jrlo** | Japan Rugby League One | 日本ラグビーリーグワン |
| top14 | **t14** | Top 14 | フランスTop 14 |
| gallagher-premiership | **gp** | Gallagher Premiership | イングランドプレミアシップ |
| urc | **urc** | United Rugby Championship | ユナイテッドラグビーチャンピオンシップ |
| epcr-champions | **ecc** | EPCR Champions Cup | ヨーロピアンチャンピオンズカップ |
| epcr-challenge | **ech** | EPCR Challenge Cup | ヨーロピアンチャレンジカップ |
| super-rugby-pacific | **srp** | Super Rugby Pacific | スーパーラグビーパシフィック |
| rugby-championship | **trc** | The Rugby Championship | ザ・ラグビーチャンピオンシップ |
| autumn-nations-series | **ans** | Autumn Nations Series | オータムネーションズシリーズ |
| world-rugby-internationals | **wri** | World Rugby Internationals | ワールドラグビー国際試合 |

### チームID形式

```
{competition_abbr}-{number}
```

**例:**
- `m6n-1`: Men's Six Nations - England
- `w6n-2`: Women's Six Nations - France
- `jrlo-1`: Japan Rugby League One - Saitama Wild Knights

---

## 📁 新ディレクトリ構造

```
data/
├── teams.json                    # 統合チームマスタ
├── competitions.json             # 大会マスタ
└── matches/
    ├── m6n/
    │   └── 2026.json            # Men's Six Nations 2026シーズン
    ├── w6n/
    │   └── 2026.json            # Women's Six Nations 2026シーズン
    ├── u6n/
    │   └── 2026.json            # U20 Six Nations 2026シーズン
    ├── jrlo/
    │   └── 2026.json            # League One 2026シーズン
    ├── t14/
    │   └── 2026-2027.json       # Top 14 2026-2027シーズン
    ├── gp/
    │   └── 202501.json          # Gallagher Premiership 2025-01シーズン
    ├── urc/
    │   └── 202501.json          # URC 2025-01シーズン
    ├── ecc/
    │   └── 2026.json            # Champions Cup 2026
    ├── ech/
    │   └── 2026.json            # Challenge Cup 2026
    ├── srp/
    │   └── 2026.json            # Super Rugby Pacific 2026
    ├── trc/
    │   └── (未使用)
    ├── ans/
    │   └── (未使用)
    └── wri/
        └── 2026.json            # World Rugby Internationals 2026
```

---

## 🎯 マイグレーション実績

### データ移行結果

| 大会ID | ファイル数 | 試合数 | チームID付与 | ステータス |
|--------|-----------|--------|-------------|-----------|
| m6n | 1 | 15 | ✅ 30箇所 | 完了 |
| w6n | 1 | 15 | ✅ 30箇所 | 完了 |
| u6n | 1 | 15 | ✅ 30箇所 | 完了 |
| jrlo | 1 | 215 | ✅ 0箇所 (既存) | 完了 |
| t14 | 1 | 188 | - | 完了 |
| gp | 1 | 93 | - | 完了 |
| urc | 1 | 151 | - | 完了 |
| ecc | 1 | 63 | - | 完了 |
| ech | 1 | 51 | - | 完了 |
| srp | 1 | 77 | - | 完了 |
| wri | 1 | 31 | - | 完了 |

**合計**: 11大会、914試合を移行

### チームマスタ生成

- **総チーム数**: 34チーム
- **大会別内訳**:
  - m6n: 6チーム (Men's Six Nations)
  - w6n: 6チーム (Women's Six Nations)
  - u6n: 6チーム (U20 Six Nations)
  - jrlo: 12チーム (Japan Rugby League One)
  - trc: 4チーム (The Rugby Championship)

---

## 🔧 実装変更

### 1. BaseScraper拡張

```python
class BaseScraper(ABC):
    def __init__(self):
        self._competition_id = None  # サブクラスで設定
        self._team_master = self._load_team_master()
    
    def _resolve_team_id(self, team_name: str, competition_id: Optional[str] = None) -> str:
        """新ID形式対応のチームID解決"""
        # 大会IDを使って検索を絞り込み
        # 例: "ENG" + "w6n" → "w6n-1"
    
    def save_to_json(self, data, filename: str):
        """新ディレクトリ構造対応"""
        # 親ディレクトリを自動作成
```

### 2. Six Nationsスクレイパー更新

```python
class SixNationsWomensScraper(SixNationsBaseScraper):
    def __init__(self):
        super().__init__("w6n", "Women's Six Nations", "w6n")
        # competition_id: "six-nations-women" → "w6n"
```

### 3. main.py保存処理更新

```python
# 新ディレクトリ構造: {comp_id}/{season}
comp_id = sample.get('competition_id', scraper_type)
season = sample.get('season', 'unknown')
save_path = f"{comp_id}/{season}"
scraper.save_to_json(matches, save_path)
# → data/matches/w6n/2026.json
```

---

## ✅ 動作検証結果

### テスト実行結果

```bash
$ python3 scripts/test_new_id_system.py

✅ 34 チーム読み込み済み

w6n チーム:
  w6n-1: ENG - England
  w6n-2: FRA - France
  w6n-3: IRE - Ireland
  w6n-4: ITA - Italy
  w6n-5: SCO - Scotland
  w6n-6: WAL - Wales

試合 #1:
  competition_id: w6n
  home_team: ENG (ID: w6n-1)
  away_team: FRA (ID: w6n-2)
  match_id: w6n-2026-03-14t15:00:00z-eng-fra-cf4bd079cf

✅ すべてのテスト完了
```

### 既存データ検証

- ✅ w6n/2026.json: 15試合、30箇所のチームID正常付与
- ✅ m6n/2026.json: 15試合、30箇所のチームID正常付与
- ✅ u6n/2026.json: 15試合、30箇所のチームID正常付与

---

## 📝 今後の作業

### 高優先度

1. **他の大会のチームマスタ追加**
   - Top 14 (14チーム)
   - Gallagher Premiership (10チーム)
   - URC (16チーム)
   - Super Rugby Pacific (12チーム)
   - EPCR (可変)

2. **competitions.json生成**
   - 各大会のteam_ids配列を含む
   - 正式名称・略称・シーズン情報

3. **他スクレイパーの更新**
   - rugbyviz.py: 数値ID → gp, urc
   - super_rugby.py: "205" → srp
   - world_rugby.py: UUID → wri
   - epcr.py, top14.py: 空文字 → ecc, ech, t14

### 中優先度

4. **match_id生成ロジック改善**
   - 現在の空文字を実際のIDに更新
   - 既存データへの一括適用

5. **バックアップデータの整理**
   - data/matches_backup/ の保管または削除

### 低優先度

6. **JSONスキーマバージョン更新**
   - 1.1 → 1.2への移行検討

7. **ドキュメント更新**
   - README.md
   - JSON_SCHEMA.md
   - USAGE_EXAMPLES.md

---

## 🛠️ 使用したスクリプト

| スクリプト | 用途 | 実行状況 |
|-----------|------|---------|
| `scripts/generate_teams_master.py` | 新ID形式のteams.json生成 | ✅ 実行済み |
| `scripts/migrate_to_new_structure.py` | 既存データの新ディレクトリへの移行 | ✅ 実行済み |
| `scripts/enrich_team_ids.py` | 移行済みデータへのチームID付与 | ✅ 実行済み |
| `scripts/test_new_id_system.py` | 新ID体系の動作確認テスト | ✅ 実行済み |
| `scripts/check_migration.py` | マイグレーション結果の確認 | ⏭️ (手動確認済み) |

---

## 📌 重要な注意事項

1. **後方互換性**: 旧チームID形式のデータは teams.json から削除されました
2. **バックアップ**: 旧データは `data/matches_backup/` に保存されています
3. **スクレイパー実行**: 新しいスクレイパーは自動的に新ディレクトリ構造に保存します
4. **チームID解決**: BaseScraperが自動的に大会IDを使ってチームを検索します

---

生成日時: 2026-02-06
