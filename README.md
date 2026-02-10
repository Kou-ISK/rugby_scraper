# rugby_scraper

itsuneru 向けに世界のラグビー試合日程を取得するスクレイパーです。

## 📋 ドキュメント

- **[JSON インターフェイス仕様](docs/JSON_SCHEMA.md)** - itsuneru が参照する JSON の詳細仕様
  - 試合データスキーマ（`data/matches/{comp_id}/{season}.json`）
  - 大会メタデータスキーマ（`data/competitions.json`）
  - チームマスタ（`data/teams.json`）
  - TypeScript 型定義
  - 使用例
- **[プロジェクト構造](docs/ARCHITECTURE.md)** - スクレイパー設計とディレクトリ構成
- **[使用例](docs/USAGE_EXAMPLES.md)** - itsuneru での実装サンプル

## 📂 プロジェクト構造

### データディレクトリ

```
data/
├── teams.json                    # 統合チームマスタ
├── teams_sources.json            # チームマスタ取得ソース定義（公式）
├── competitions.json             # 大会マスタ
├── competitions_base.json        # 大会マスタの固定テンプレ
└── matches/                      # 試合データ（大会ID別・シーズン別）
    ├── m6n/2025.json
    ├── w6n/2025.json
    ├── premier/2025.json
    ├── urc/2025.json
    ├── jrlo-div1/2026.json
    ├── jrlo-div2/2026.json
    ├── jrlo-div3/2026.json
    └── wr/2026.json
```

### ソースコード構造

```
src/
├── collectors/                   # データ収集層
│   ├── base.py                   # BaseScraper
│   ├── international/            # 国際大会
│   │   ├── six_nations.py
│   │   ├── rugby_championship.py
│   │   ├── autumn_nations.py
│   │   └── world_rugby.py
│   ├── european/                 # 欧州大会
│   │   ├── epcr.py
│   │   ├── top14.py
│   │   └── rugbyviz.py
│   └── domestic/                 # 国内リーグ
│       ├── league_one_divisions.py
│       └── super_rugby.py
├── services/                     # ビジネスロジック層
│   └── team_service.py           # チーム抽出・統合
├── validators/                   # バリデーション層
│   └── team_validator.py         # 重複チェック
├── repositories/                 # データ永続化層
│   └── competition_repository.py # メタデータ生成
├── core/                         # コア機能
└── main.py                       # CLIエントリーポイント

scripts/
├── automation/                   # 自動化
│   ├── scrape_all.py
│   ├── scrape_all.sh
│   └── scrape_remaining.sh
├── data/                         # データ処理（アーカイブ）
└── maintenance/                  # メンテナンス（アーカイブ）
```

### ID体系

**大会ID**: 短縮コード形式

- `m6n`, `w6n`, `u6n`: Six Nations (Men/Women/U20)
- `epcr-champions`, `epcr-challenge`: EPCR (Champions/Challenge)
- `t14`: Top 14
- `jrlo-div1`, `jrlo-div2`, `jrlo-div3`: Japan Rugby League One
- `premier`: Gallagher Premiership
- `urc`: United Rugby Championship
- `srp`: Super Rugby Pacific
- `trc`: The Rugby Championship
- `ans`: Autumn Nations Series
- `wr`: World Rugby Internationals

**チームID**: 形式

- 国代表: `NT_{GENDER}_{COUNTRY}` (例: `NT_M_ENG`, `NT_W_FRA`)
- クラブ: `{comp_id}_{number}` (例: `premier_1`, `jrlo-div1_1`)

## 取得対象リーグと公式ソース

- Six Nations / Women's Six Nations / Six Nations U20
  - 公式サイト: sixnationsrugby.com
  - ソース種別: official
- EPCR Champions Cup / EPCR Challenge Cup
  - 公式サイト: epcrugby.com
  - ソース種別: official
- Top 14
  - 公式サイト: top14.lnr.fr
  - ソース種別: official
- Japan Rugby League One
  - 公式サイト: league-one.jp
  - ソース種別: official
- Gallagher Premiership
  - 公式サイト: premiershiprugby.com
  - 公式データフィード: rugby-union-feeds.incrowdsports.com (RugbyViz)
  - ソース種別: official
- United Rugby Championship (URC)
  - 公式サイト: unitedrugby.com
  - 公式データフィード: rugby-union-feeds.incrowdsports.com (RugbyViz)
  - ソース種別: official
- Super Rugby Pacific
  - 公式サイト: super.rugby
  - 公式PDF日程: super.rugby の公開PDF
  - ソース種別: official
- The Rugby Championship
  - 公式サイト: therugbychampionship.com
  - ソース種別: official (スクレイパー準備中)
- Autumn Nations Series
  - 公式サイト: autumnnationsseries.com
  - ソース種別: official (スクレイパー準備中)
- World Rugby Internationals (Test Matches)
  - 公式サイト: world.rugby
  - 公式データ: api.wr-rims-prod.pulselive.com (World Rugby の公開データエンドポイント)
  - ソース種別: official

## JSON インターフェイス

**重要**: itsuneru プロジェクトとのインターフェイス契約を保証するため、詳細な JSON スキーマを定義しています。

👉 **[JSON_SCHEMA.md](docs/JSON_SCHEMA.md) を参照してください**

### クイックリファレンス

#### 試合データ（`data/matches/*.json`）

```json
[
  {
    "date": "2024-12-21 12:10:00",
    "venue": "三重交通G スポーツの杜 鈴鹿 (三重県)",
    "home_team": "三重ホンダヒート",
    "away_team": "ブラックラムズ東京",
    "broadcasters": ["J SPORTS 3", "三重テレビ"],
    "url": "https://league-one.jp/match/27447"
  }
]
```

#### 大会メタデータ（`data/competitions.json`）

```json
[
  {
    "id": "jrlo-div1",
    "name": "Japan Rugby League One",
    "timezone_default": "Asia/Tokyo",
    "data_paths": ["data/matches/jrlo-div1/2026.json"],
    "coverage": {
      "broadcast_regions": [...],
      "analysis_providers": [...],
      "notes": "..."
    },
    "teams": [...],
    "data_summary": {...}
  }
]
```

## 出力JSONの共通スキーマ（非推奨）

> **注意**: このセクションは古い記述です。最新の仕様は [JSON_SCHEMA.md](docs/JSON_SCHEMA.md) を参照してください。

各スクレイパーは以下の統一フォーマットで出力します。

- match_id: 公式ID（あれば）
- competition: 大会名
- competition_id: 公式ID（あれば）
- season: シーズン
- round: ラウンド名
- status: 試合ステータス
- kickoff: 現地時間のISO8601 (TZ付き)
- kickoff_utc: UTCのISO8601
- timezone: タイムゾーン名またはUTCオフセット
- timezone_source: タイムゾーン推定の根拠
- venue: 会場名
- home_team: ホームチーム
- away_team: アウェイチーム
- home_team_id / away_team_id: 公式ID（あれば）
- match_url: 公式試合詳細URL（あれば）
- broadcasters: 放送局
- source_name / source_url / source_type: 出典メタ情報

## 注意事項

- 公式サイトでも「閲覧地域のローカル時間」で表示されるケースがあるため、
  Selenium を使うスクレイパーはブラウザのタイムゾーンを大会の標準TZに固定して取得します。
- Super Rugby Pacific は公式PDFの「LOCAL/GMT」列からタイムゾーンを算出します。
- 外部サイト/公式フィードに依存するため、仕様変更に強くする設計を優先しています。
  (チーム名などの固定定数に極力依存しない方針)

## 🚀 使い方

## ✅ 運用フロー（最重要）

**マスタは試合データと独立して更新します。**

### A. マスタ独立運用（推奨）
1. **チームマスタ更新**（公式チーム一覧から）
2. **大会マスタ更新**（公式情報 + テンプレ補完）
3. **試合取得**
4. **team_id Backfill**（必要な場合のみ）

### B. 試合先行運用（簡単）
1. 試合取得  
2. チームマスタ更新  
3. team_id Backfill  
4. 大会マスタ更新

**どちらでも `team_id` を保証できるよう Backfill コマンドを用意しています。**

### 1) 試合データ取得

```bash
python -m src.main <competition-id>
```

**利用可能な大会ID:**

```bash
# 国際大会
python -m src.main m6n    # Men's Six Nations
python -m src.main w6n    # Women's Six Nations
python -m src.main u6n    # Six Nations U20
python -m src.main trc    # The Rugby Championship
python -m src.main ans    # Autumn Nations Series
python -m src.main wr     # World Rugby Internationals

# 欧州大会
python -m src.main epcr-champions # EPCR Champions Cup
python -m src.main epcr-challenge # EPCR Challenge Cup
python -m src.main t14    # Top 14
python -m src.main premier # Gallagher Premiership
python -m src.main urc    # United Rugby Championship

# 国内リーグ
python -m src.main jrlo   # Japan Rugby League One (全Division)
python -m src.main srp    # Super Rugby Pacific
```

**補足**:
- このコマンドは **試合データのみ** 更新します。
- `teams.json` / `competitions.json` は **自動更新されません**。

### 2) チームマスタ更新（公式チーム一覧から）

```bash
python -m src.main update-team-master
```

**いつ実行する？**
- 新しい大会を追加したとき
- チームが増減したとき
- チームIDやチーム名の整合性を取り直したいとき

**注意**:
- JRLOのプレースホルダー（例: `準決勝(1)勝者`）は自動除外されます。
- ロゴURLは公式サイトから同時に取得します（TheSportsDBは使用しません）。
- 公式チーム一覧の取得元は `data/teams_sources.json` で管理します。

**legacy**:
- `extract-teams` は **試合データ依存の旧方式** です（非推奨）

### 3) 大会マスタ更新（公式情報 + テンプレ補完）

```bash
python -m src.main update-competition-master
```

**いつ実行する？**
- `data/matches` を更新したあと、`competitions.json` を最新化したいとき
  - 公式サイトから取得できる情報（logo_url など）を自動反映
  - テンプレは `data/competitions_base.json` で管理

### 4) team_id Backfill（必要な場合のみ）

```bash
python -m src.main backfill-team-ids
```

**用途**:
- 試合取得を先に行った場合に `home_team_id/away_team_id` を埋め直す
- `--force` で既存のIDも上書き可能

### 5) 大会メタデータサマリー（任意）

```bash
python -m src.main generate-metadata
```

**出力**: `data/competitions_summary.json`
  
試合データから集計したサマリーを出力します（マスタ更新とは独立）。
### サービス実行

```bash
# チームマスタ更新（公式チーム一覧）
python -m src.main update-team-master

# 大会マスタ更新（公式情報 + テンプレ補完）
python -m src.main update-competition-master

# team_id 後埋め
python -m src.main backfill-team-ids

# 重複チェック
python -m src.main validate-duplicates

# 大会メタデータ生成（サマリー）
python -m src.main generate-metadata

# legacy: 試合データ依存のチーム抽出
python -m src.main extract-teams

# 全大会を一括スクレイピング
python scripts/automation/scrape_all.py
```

### 推奨ワークフロー: マスタ独立運用

```bash
# 1) チームマスタ更新（公式チーム一覧）
python -m src.main update-team-master

# 2) 大会マスタ更新（公式情報 + テンプレ補完）
python -m src.main update-competition-master

# 3) 試合取得（必要な大会だけ）
python -m src.main premier
python -m src.main urc
python -m src.main epcr-champions

# 4) team_id を後から埋め直す（必要な場合のみ）
python -m src.main backfill-team-ids

# 5) 公式ロゴ検証（任意）
python scripts/validate_official_logos.py
```

**手順**:

```bash
# 1. 大会データをスクレイピング
python -m src.main premier

# 2. チームマスタを再生成（試合データから抽出）
python -m src.main extract-teams

```

**検証**:

```bash
# 公式ロゴURLの妥当性チェック
python scripts/validate_official_logos.py
```

**複数大会の場合**:

```bash
# 全大会スクレイピング → 必要に応じてロゴ取得
python -m src.main premier
python -m src.main urc
python -m src.main epcr-champions
python -m src.main extract-teams
python scripts/validate_official_logos.py  # 公式ロゴURLの妥当性チェック
```

## 📡 取得パス一覧 (itsuneru向け)

**📖 詳細仕様**: [JSON_SCHEMA.md](docs/JSON_SCHEMA.md) | **💡 使用例**: [USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md)

### GitHub Raw URL形式

```
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/{comp_id}/{season}.json
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/competitions.json
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/teams.json
```

### 大会別データパス例

- Men's Six Nations: `data/matches/m6n/2025.json`
- Women's Six Nations: `data/matches/w6n/2025.json`
- Gallagher Premiership: `data/matches/premier/2025.json`
- Japan Rugby League One D1: `data/matches/jrlo-div1/2026.json`
- World Rugby Internationals: `data/matches/wr/2026.json`

**注**: 各大会の正確な `data_paths` は `data/competitions.json` の各エントリを参照してください。

### TypeScript 型定義

```typescript
// types/rugby-scraper.d.ts をプロジェクトにコピー
import type {
  Match,
  Matches,
  Competition,
  Competitions,
} from './types/rugby-scraper';
```

👉 型定義ファイル: [types/rugby-scraper.d.ts](types/rugby-scraper.d.ts)

## 大会メタデータ

大会ごとの詳細情報は `data/competitions.json` にまとめています。

主なフィールド:

- id / name / short_name
- sport / category / gender / age_grade / tier / region
- governing_body / organizer
- official_sites / official_feeds
- timezone_default / season_pattern / match_url_template
- data_paths
- coverage.broadcast_regions / coverage.analysis_providers / coverage.notes
- teams
- data_summary.match_count / data_summary.seasons / data_summary.date_range / data_summary.last_updated

### 視聴情報 (coverage)

各大会の `coverage` フィールドには以下の情報が含まれています：

- **broadcast_regions**: 地域別の公式放送・配信プロバイダー
  - region: 対象地域（JP, UK, IE, FR, AU, NZ, ZA など）
  - providers: 配信・放送サービス名のリスト
  - official_source: 公式情報源のURL
- **analysis_providers**: 分析・統計プロバイダー（ESPN Rugby, RugbyPass, RugbyPass TV）
- **notes**: 視聴時の注意事項（VPN要否、地域制限、契約情報など）

### データ生成

`data/competitions.json` は **テンプレ + 公式サイト情報** を統合して生成します。
試合データ由来の集計サマリーは `data/competitions_summary.json` に出力します。

```bash
# competitions.json を更新（公式情報 + テンプレ補完）
python -m src.main update-competition-master

# 集計サマリーを更新（試合データから）
python -m src.main generate-metadata
```

## GitHub Raw での取得URL例

`data` ブランチに更新されるため、以下の形式で最新データを取得できます。

```
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/{comp_id}/{season}.json
```

例:

```
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/m6n/2026.json
```
