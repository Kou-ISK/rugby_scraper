# プロジェクト構造とアーキテクチャ

このドキュメントでは、rugby_scraper プロジェクトの設計思想、レイヤー構成、実装方法について説明します。

## 🏗️ アーキテクチャ設計

### データパイプラインアーキテクチャ

このプロジェクトは、責務ごとに明確なレイヤー分離を実現したデータパイプラインアーキテクチャを採用しています。

**レイヤー構成**:

```
src/
├── collectors/      # データ収集層
├── services/        # ビジネスロジック層
├── validators/      # データ検証層
├── repositories/    # データ永続化層
├── core/            # コアユーティリティ
└── main.py          # CLIエントリーポイント
```

### 基本原則

1. **レイヤー分離**: 各層の責務を明確化し、依存関係を制御
2. **単一責任の原則**: 各スクレイパーは1つの大会のみを担当
3. **一貫性**: すべてのスクレイパーが `BaseScraper` を継承し、統一されたインターフェースを提供
4. **保守性**: 競技会カテゴリ別にスクレイパーを分類し、関連性の高いコードをまとめる
5. **拡張性**: 新しい大会のスクレイパー追加が容易な構造
6. **自動化**: match_id/team_id自動生成でデータ整合性を保証

### データフロー全体像

```
公式サイト/API
    ↓ 1. データ収集（Collectors）
スクレイパー (collectors/)
    ↓ データ正規化 + ID自動生成
data/matches/{comp_id}/{season}.json, teams.json
    ↓ 2. ビジネスロジック（Services）
チーム統合・エンリッチメント
    ↓ TheSportsDB API連携
teams.json (enriched)
    ↓ 3. データ検証（Validators）
重複チェック・整合性確認
    ↓ バリデーションレポート
validation_report.json
    ↓ 4. メタデータ管理（Repositories）
competitions.json生成
    ↓
完成データセット
```

## 📁 レイヤー構成

### 1. Collectors（データ収集層）

**役割**: 外部データソースからラグビー試合データを収集

**ディレクトリ構造**:

```
src/collectors/
├── base.py                   # BaseScraper抽象クラス
├── __init__.py               # パッケージ定義
│
├── international/            # 国際大会スクレイパー
│   ├── __init__.py
│   ├── six_nations.py        # Six Nations 3大会
│   ├── rugby_championship.py # Rugby Championship
│   ├── autumn_nations.py     # Autumn Nations Series
│   └── world_rugby.py        # World Rugby Internationals
│
├── european/                 # 欧州大会スクレイパー
│   ├── __init__.py
│   ├── epcr.py               # EPCR Champions/Challenge
│   ├── top14.py              # Top 14
│   └── rugbyviz.py           # GP, URC
│
└── domestic/                 # 国内リーグスクレイパー
    ├── __init__.py
    ├── league_one_divisions.py # England League One
    └── super_rugby.py          # Super Rugby Pacific
```

**主要クラス**: `BaseScraper`

- `build_match()`: match_id/team_id自動生成
- `_resolve_team_id()`: team_id自動解決・teams.json登録
- `assign_match_ids()`: match_id自動付与
- `scrape()`: データ収集エントリーポイント

### 2. Services（ビジネスロジック層）

**役割**: データ変換、統合、エンリッチメント処理

**ファイル**:

```
src/services/
└── team_service.py           # チーム抽出・統合サービス
```

**主要機能**:

- 全試合データからチーム抽出
- TheSportsDB APIでロゴURL取得
- スポンサー名除去による正規化
- ID安定性保証（既存ID変更なし）
- 重複検出レポート生成

### 3. Validators（データ検証層）

**役割**: データ品質チェック、整合性検証

**ファイル**:

```
src/validators/
└── team_validator.py         # チーム重複検証
```

**検証ルール**:

- スポンサー名違いの同一チーム検出
- team_id整合性確認
- 大会別出現頻度分析

### 4. Repositories（データ永続化層）

**役割**: メタデータ管理、マスターデータ生成

**ファイル**:

```
src/repositories/
└── competition_repository.py # 大会メタデータ管理
```

**機能**:

- competitions.json生成
- 大会ID・名称・種別の一元管理

### 5. Core（コアユーティリティ）

**役割**: プロジェクト横断的な共通機能

**想定機能**:

```
src/core/
├── config.py        # 設定管理
├── logger.py        # ロギング
└── exceptions.py    # エラーハンドリング
```

## 📁 旧ディレクトリ構成（参考）

### ソースコード (`src/`)

## 🎯 CLIコマンド体系

### スクレイピング

```bash
python -m src.main <comp_id>
```

**対応大会ID**:

- `six-nations`: Six Nations Championship
- `gp`: Gallagher Premiership
- `urc`: United Rugby Championship
- `top14`: Top 14
- `epcr-champions`: Champions Cup
- `epcr-challenge`: Challenge Cup
- `rc`: Rugby Championship
- `ans`: Autumn Nations Series
- `super-rugby`: Super Rugby Pacific
- `league-one`: England League One
- `six-nations-u20`: Six Nations U20
- `six-nations-women`: Six Nations Women
- `world-rugby`: World Rugby Internationals

### サービス実行

```bash
# チーム抽出・統合（Services層）
python -m src.main extract-teams

# 重複検証（Validators層）
python -m src.main validate-duplicates

# メタデータ生成（Repositories層）
python -m src.main generate-metadata
```

### 自動化スクリプト

```bash
# 全大会を一括スクレイピング
python scripts/automation/scrape_all.py

# 不足データのみスクレイピング
bash scripts/automation/scrape_remaining.sh
```

## 🔧 スクレイパーの実装

### BaseScraper クラス

すべてのスクレイパーは `src/collectors/base.py` の `BaseScraper` を継承します。

```python
from src.collectors.base import BaseScraper

class MyScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            comp_id="my-comp",
            base_url="https://...",
            type="international"  # or "european", "domestic"
        )

    def scrape(self):
        # データ収集ロジック
        matches = self._fetch_matches()

        # BaseScraper.build_match()で自動ID付与
        for match_data in matches:
            self.build_match(match_data)

        return self.matches
```

**重要メソッド**:

- `build_match(match_data)`: match_id/team_id自動生成
- `_resolve_team_id(team_name, country)`: team_id自動解決
- `assign_match_ids(matches)`: match_id自動付与
- `save_to_json(matches, path)`: JSONファイル保存

### カテゴリ分類基準

#### International（国際大会）

- 複数国の代表チームが参加
- 国際統括団体（World Rugby等）が主催・承認
- 例: Six Nations, Rugby Championship

#### European（欧州大会）

- 欧州のクラブチームが参加
- 欧州域内の競技会
- 例: EPCR, Top 14, Gallagher Premiership, URC

#### Domestic（国内リーグ）

- 単一国内のクラブリーグ
- 例: Japan Rugby League One, Super Rugby Pacific

## 🆕 新しいスクレイパーの追加手順

### 1. カテゴリを決定

大会の性質に応じて `international/`, `european/`, `domestic/` のいずれかを選択。

### 2. スクレイパーファイルを作成

```bash
# 例: 新しい国際大会スクレイパー
touch src/collectors/international/my_competition.py
```

### 3. BaseScraper を継承して実装

```python
from ..base import BaseScraper

class MyCompetitionScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            comp_id="my-comp",
            base_url="https://example.com",
            type="international"
        )

    def scrape(self):
        # 1. データ取得
        raw_data = self._fetch_data()

        # 2. 正規化 + ID自動生成
        for item in raw_data:
            self.build_match(
                home_team=item["home"],
                away_team=item["away"],
                date=item["date"],
                venue=item["venue"],
                # ... 他のフィールド
            )

        return self.matches

    def _fetch_data(self):
        # スクレイピング実装
        response = requests.get(self.base_url)
        # ... パース処理
        return parsed_data
```

### 4. **init**.py にエクスポート追加

```python
# src/collectors/international/__init__.py
from .my_competition import MyCompetitionScraper

__all__ = [
    # ... 既存
    "MyCompetitionScraper",
]
```

### 5. main.py に登録

```python
# src/main.py
from src.collectors.international import MyCompetitionScraper

scrapers = {
    # ... 既存
    "my-comp": MyCompetitionScraper(),
}
```

### 6. メタデータ生成

```bash
# competitions.json に自動追加
python -m src.main generate-metadata
```

### 7. 動作確認

```bash
# スクレイピング実行
python -m src.main my-comp

# チーム抽出
python -m src.main extract-teams

# 検証
python -m src.main validate-duplicates
```

## 📦 Import方法

### スクレイパーから

```python
# BaseScraper
from src.collectors.base import BaseScraper

# 他のスクレイパーを参照する場合
from src.collectors.international import SixNationsScraper
from src.collectors.european import EPCRChampionsCupScraper
```

### スクリプトから

```python
# 特定のスクレイパーを使用
from src.collectors.international import SixNationsScraper
from src.collectors.european import GallagherPremiershipScraper

# メタデータ生成
from src.repositories.competition_repository import main as generate_metadata
```

## 🔄 データ処理フロー

### 1. スクレイピング（Collectors層）

```bash
python -m src.main six-nations
# → data/matches/six-nations/{season}.json
# → teams.json（自動更新）
```

### 2. チーム統合（Services層）

```bash
python -m src.main extract-teams
# → teams.json（TheSportsDB連携、ロゴURL付与）
```

### 3. データ検証（Validators層）

```bash
python -m src.main validate-duplicates
# → validation_report.json
```

### 4. メタデータ生成（Repositories層）

```bash
python -m src.main generate-metadata
# → data/competitions.json
```

## 🎯 ベストプラクティス

### スクレイパー実装

1. **エラーハンドリング**: ネットワークエラー、HTML構造変更に対応
2. **レート制限**: 過度なリクエストを避ける（必要に応じてsleep）
3. **タイムゾーン**: 正確なタイムゾーン情報を取得・保存
4. **team_id**: BaseScraper.\_resolve_team_id()で自動生成・teams.json登録

### データ形式

1. **日時**: ISO8601形式（`date`, `date_utc`）
2. **ID**: BaseScraper自動生成（`match_id`, `team_id`）
3. **出典**: `source_name`, `source_url` を必ず記録

### コード品質

1. **型ヒント**: 可能な限り型ヒントを使用
2. **ドキュメント**: 各スクレイパーにdocstringを記載
3. **テスト**: 新機能追加時は動作確認を実施

## 🛠️ トラブルシューティング

### ImportError

```python
# ❌ 古い構造
from src.scrapers.six_nations import SixNationsScraper

# ✅ 新しい構造
from src.collectors.international import SixNationsScraper
```

### match_id重複

`BaseScraper.assign_match_ids()` が自動的にUUID付与します。
重複する場合は試合データの一意性（日時・チーム・会場）を確認してください。

### team_id未解決

`BaseScraper._resolve_team_id()` が自動解決します。
新規チームの場合、teams.jsonに自動登録されます。

### スクレイピング失敗

1. 公式サイトのHTML構造変更を確認
2. ネットワーク接続を確認
3. レート制限に引っかかっていないか確認

## 📊 データ構造

### teams.json

```json
{
  "england-bath": {
    "name": "Bath Rugby",
    "country": "England",
    "logo_url": "https://...",
    "competitions": ["gp", "epcr-champions"]
  }
}
```

### matches/{comp_id}/{season}.json

```json
[
  {
    "match_id": "six-nations-2024-abc123",
    "date": "2024-02-03T15:00:00Z",
    "home_team": {
      "id": "england-england",
      "name": "England",
      "score": 27
    },
    "away_team": {
      "id": "wales-wales",
      "name": "Wales",
      "score": 24
    },
    "venue": "Twickenham Stadium",
    "round": "Round 1"
  }
]
```

## 📚 関連ドキュメント

- [JSON_SCHEMA.md](JSON_SCHEMA.md) - データスキーマ仕様
- [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - itsuneru での使用例
- [README.md](../README.md) - プロジェクト概要
