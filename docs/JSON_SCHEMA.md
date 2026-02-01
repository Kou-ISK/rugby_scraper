# JSON インターフェイス仕様

このドキュメントは、itsuneru プロジェクトが rugby_scraper から取得する JSON のインターフェイス定義です。

## 1. 試合データ（`data/matches/*.json`）

各大会の試合データを含む配列。

### エンドポイント

```
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/<competition-id>.json
```

### スキーマ

```typescript
interface Match {
  // 試合日時（現地時間、形式: "YYYY-MM-DD HH:MM:SS"）
  date: string;

  // 会場名
  venue: string;

  // ホームチーム名
  home_team: string;

  // アウェイチーム名
  away_team: string;

  // 放送局リスト（空配列または文字列配列）
  broadcasters: string[] | string;

  // 試合詳細ページURL
  url: string;
}

type Matches = Match[];
```

### サンプル

```json
[
  {
    "date": "2024-12-21 12:10:00",
    "venue": "三重交通G スポーツの杜 鈴鹿 (三重県)",
    "home_team": "三重ホンダヒート",
    "away_team": "ブラックラムズ東京",
    "broadcasters": [
      "J SPORTS 3",
      "三重テレビ",
      "イッツコムチャンネル",
      "J SPORTSオンデマンド"
    ],
    "url": "https://league-one.jp/match/27447"
  }
]
```

### フィールド詳細

| フィールド     | 型                     | 必須 | 説明                                              |
| -------------- | ---------------------- | ---- | ------------------------------------------------- |
| `date`         | `string`               | ✓    | 試合日時（現地時間）。形式: `YYYY-MM-DD HH:MM:SS` |
| `venue`        | `string`               | ✓    | 会場名。地域情報を含む場合あり                    |
| `home_team`    | `string`               | ✓    | ホームチーム名                                    |
| `away_team`    | `string`               | ✓    | アウェイチーム名                                  |
| `broadcasters` | `string[]` or `string` | ✓    | 放送局。配列または空文字列                        |
| `url`          | `string`               | ✓    | 試合詳細ページのURL                               |

### 注意事項

1. **日時形式**: タイムゾーン情報は含まれない。`competitions.json` の `timezone_default` を参照
2. **broadcasters**: スクレイパーによって `string[]` または `""` (空文字列) の場合あり
3. **チーム名**: 大会によって略称（例: `ENG`, `FRA`）またはフル名（例: `三重ホンダヒート`）

---

## 2. 大会メタデータ（`data/competitions.json`）

全大会の詳細情報を含む配列。

### エンドポイント

```
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/competitions.json
```

### スキーマ

```typescript
interface Competition {
  // 大会ID（ファイル名に対応）
  id: string;

  // 大会正式名称
  name: string;

  // 大会略称
  short_name: string;

  // スポーツ種目
  sport: 'rugby union';

  // カテゴリー
  category: 'international' | 'club';

  // 性別
  gender: 'men' | 'women' | 'mixed';

  // 年齢区分
  age_grade: 'senior' | 'u20';

  // ティア
  tier: 'tier-1' | 'tier-2' | 'tier-3';

  // 地域
  region: string;

  // 統括団体
  governing_body: string;

  // 主催者
  organizer: string;

  // 公式サイトURL配列
  official_sites: string[];

  // 公式データフィードURL配列
  official_feeds: string[];

  // デフォルトタイムゾーン
  timezone_default: string;

  // シーズンパターン
  season_pattern: 'annual' | 'variable';

  // 試合URLテンプレート
  match_url_template: string;

  // 試合データファイルパス配列
  data_paths: string[];

  // 視聴情報
  coverage: Coverage;

  // 参加チーム一覧
  teams: string[];

  // データサマリー
  data_summary: DataSummary;
}

interface Coverage {
  // 地域別放送情報
  broadcast_regions: BroadcastRegion[];

  // 分析プロバイダー
  analysis_providers: AnalysisProvider[];

  // 視聴に関する注意事項（VPN、地域制限など）
  notes?: string;
}

interface BroadcastRegion {
  // 対象地域（ISO国コードまたは地域名）
  region: string;

  // 配信・放送プロバイダー
  providers: string[];

  // 公式情報源URL
  official_source: string;
}

interface AnalysisProvider {
  // プロバイダー名
  name: string;

  // 公式サイトURL
  official_source: string;
}

interface DataSummary {
  // 試合数
  match_count: number;

  // シーズン一覧
  seasons: string[];

  // 日付範囲
  date_range: {
    start: string; // ISO8601形式 or 空文字列
    end: string; // ISO8601形式 or 空文字列
  };

  // 最終更新日時（ISO8601形式 or 空文字列）
  last_updated: string;
}

type Competitions = Competition[];
```

### サンプル

```json
[
  {
    "id": "six-nations",
    "name": "Six Nations",
    "short_name": "6N",
    "sport": "rugby union",
    "category": "international",
    "gender": "men",
    "age_grade": "senior",
    "tier": "tier-1",
    "region": "Europe",
    "governing_body": "Six Nations Rugby",
    "organizer": "Six Nations Rugby",
    "official_sites": ["https://www.sixnationsrugby.com"],
    "official_feeds": [],
    "timezone_default": "Europe/London",
    "season_pattern": "annual",
    "match_url_template": "https://www.sixnationsrugby.com/en/m6n/fixtures/{season}/{slug}",
    "data_paths": ["data/matches/six-nations.json"],
    "coverage": {
      "broadcast_regions": [
        {
          "region": "JP",
          "providers": ["WOWOW"],
          "official_source": "https://www.sixnationsrugby.com/en/m6n/where-to-watch-guinness-six-nations"
        }
      ],
      "analysis_providers": [
        {
          "name": "ESPN Rugby",
          "official_source": "https://www.espn.com/rugby/"
        }
      ],
      "notes": "Regional availability varies. Some streaming services require geo-location within their service area or VPN for international access."
    },
    "teams": ["ENG", "FRA", "IRE", "ITA", "SCO", "WAL"],
    "data_summary": {
      "match_count": 15,
      "seasons": [],
      "date_range": {
        "start": "",
        "end": ""
      },
      "last_updated": "2025-02-02T07:32:24.139795"
    }
  }
]
```

### フィールド詳細

#### Competition オブジェクト

| フィールド           | 型            | 必須 | 説明                                                           |
| -------------------- | ------------- | ---- | -------------------------------------------------------------- |
| `id`                 | `string`      | ✓    | 大会ID（ケバブケース）。試合データファイル名と対応             |
| `name`               | `string`      | ✓    | 大会正式名称                                                   |
| `short_name`         | `string`      | ✓    | 大会略称                                                       |
| `sport`              | `string`      | ✓    | スポーツ種目（現在は `"rugby union"` のみ）                    |
| `category`           | `string`      | ✓    | カテゴリー: `"international"` または `"club"`                  |
| `gender`             | `string`      | ✓    | 性別: `"men"`, `"women"`, `"mixed"`                            |
| `age_grade`          | `string`      | ✓    | 年齢区分: `"senior"`, `"u20"`                                  |
| `tier`               | `string`      | ✓    | ティア: `"tier-1"`, `"tier-2"`, `"tier-3"`                     |
| `region`             | `string`      | ✓    | 地域（例: `"Europe"`, `"Japan"`, `"Oceania/Americas/Africa"`） |
| `governing_body`     | `string`      | ✓    | 統括団体名                                                     |
| `organizer`          | `string`      | ✓    | 主催者名                                                       |
| `official_sites`     | `string[]`    | ✓    | 公式サイトURL配列                                              |
| `official_feeds`     | `string[]`    | ✓    | 公式データフィードURL配列（空配列の場合あり）                  |
| `timezone_default`   | `string`      | ✓    | デフォルトタイムゾーン（IANA形式）                             |
| `season_pattern`     | `string`      | ✓    | シーズンパターン: `"annual"` または `"variable"`               |
| `match_url_template` | `string`      | ✓    | 試合URLテンプレート（空文字列の場合あり）                      |
| `data_paths`         | `string[]`    | ✓    | 試合データファイルの相対パス配列                               |
| `coverage`           | `Coverage`    | ✓    | 視聴情報オブジェクト                                           |
| `teams`              | `string[]`    | ✓    | 参加チーム名配列（空配列の場合あり）                           |
| `data_summary`       | `DataSummary` | ✓    | データサマリーオブジェクト                                     |

#### Coverage オブジェクト

| フィールド           | 型                   | 必須 | 説明                                      |
| -------------------- | -------------------- | ---- | ----------------------------------------- |
| `broadcast_regions`  | `BroadcastRegion[]`  | ✓    | 地域別放送情報配列                        |
| `analysis_providers` | `AnalysisProvider[]` | ✓    | 分析プロバイダー配列                      |
| `notes`              | `string`             | -    | 視聴時の注意事項（VPN要否、地域制限など） |

#### BroadcastRegion オブジェクト

| フィールド        | 型         | 必須 | 説明                                                       |
| ----------------- | ---------- | ---- | ---------------------------------------------------------- |
| `region`          | `string`   | ✓    | 対象地域（ISO国コードまたは地域名。例: `"JP"`, `"UK/IE"`） |
| `providers`       | `string[]` | ✓    | 配信・放送プロバイダー名配列                               |
| `official_source` | `string`   | ✓    | 公式情報源URL                                              |

#### DataSummary オブジェクト

| フィールド         | 型         | 必須 | 説明                                      |
| ------------------ | ---------- | ---- | ----------------------------------------- |
| `match_count`      | `number`   | ✓    | 試合数                                    |
| `seasons`          | `string[]` | ✓    | シーズン一覧（空配列の場合あり）          |
| `date_range`       | `object`   | ✓    | 日付範囲オブジェクト                      |
| `date_range.start` | `string`   | ✓    | 開始日（ISO8601形式または空文字列）       |
| `date_range.end`   | `string`   | ✓    | 終了日（ISO8601形式または空文字列）       |
| `last_updated`     | `string`   | ✓    | 最終更新日時（ISO8601形式または空文字列） |

---

## 3. 大会ID一覧

itsuneru が参照可能な大会IDとそのデータパス：

| 大会ID                       | データパス                                     | 大会名                     |
| ---------------------------- | ---------------------------------------------- | -------------------------- |
| `six-nations`                | `data/matches/six-nations.json`                | Six Nations                |
| `six-nations-women`          | `data/matches/six-nations-women.json`          | Women's Six Nations        |
| `six-nations-u20`            | `data/matches/six-nations-u20.json`            | Six Nations U20            |
| `epcr-champions`             | `data/matches/epcr-champions.json`             | EPCR Champions Cup         |
| `epcr-challenge`             | `data/matches/epcr-challenge.json`             | EPCR Challenge Cup         |
| `top14`                      | `data/matches/top14.json`                      | Top 14                     |
| `league-one`                 | `data/matches/league-one.json`                 | Japan Rugby League One     |
| `gallagher-premiership`      | `data/matches/gallagher-premiership.json`      | Gallagher Premiership      |
| `urc`                        | `data/matches/urc.json`                        | United Rugby Championship  |
| `super-rugby-pacific`        | `data/matches/super-rugby-pacific.json`        | Super Rugby Pacific        |
| `rugby-championship`         | `data/matches/rugby-championship.json`         | The Rugby Championship     |
| `autumn-nations-series`      | `data/matches/autumn-nations-series.json`      | Autumn Nations Series      |
| `world-rugby-internationals` | `data/matches/world-rugby-internationals.json` | World Rugby Internationals |

---

## 4. バージョニングと互換性

### 現在のバージョン

- **Schema Version**: 1.0
- **Last Updated**: 2026-02-01

### 互換性ポリシー

1. **後方互換性の維持**
   - 既存フィールドの削除は行わない
   - 既存フィールドの型変更は行わない
   - 新規フィールドの追加は可能（オプショナル）

2. **非推奨化プロセス**
   - フィールド廃止の6ヶ月前に通知
   - `@deprecated` マーカーの追加

3. **破壊的変更**
   - メジャーバージョンアップ時のみ
   - 事前に GitHub Issues で告知

### 変更履歴

#### v1.0 (2026-02-01)

- 初版リリース
- 試合データスキーマ定義
- 大会メタデータスキーマ定義

---

## 5. 使用例（itsuneru側）

### TypeScript型定義ファイル

```typescript
// types/rugby-scraper.d.ts

export interface Match {
  date: string;
  venue: string;
  home_team: string;
  away_team: string;
  broadcasters: string[] | string;
  url: string;
}

export type Matches = Match[];

export interface Competition {
  id: string;
  name: string;
  short_name: string;
  sport: 'rugby union';
  category: 'international' | 'club';
  gender: 'men' | 'women' | 'mixed';
  age_grade: 'senior' | 'u20';
  tier: 'tier-1' | 'tier-2' | 'tier-3';
  region: string;
  governing_body: string;
  organizer: string;
  official_sites: string[];
  official_feeds: string[];
  timezone_default: string;
  season_pattern: 'annual' | 'variable';
  match_url_template: string;
  data_paths: string[];
  coverage: Coverage;
  teams: string[];
  data_summary: DataSummary;
}

export interface Coverage {
  broadcast_regions: BroadcastRegion[];
  analysis_providers: AnalysisProvider[];
  notes?: string;
}

export interface BroadcastRegion {
  region: string;
  providers: string[];
  official_source: string;
}

export interface AnalysisProvider {
  name: string;
  official_source: string;
}

export interface DataSummary {
  match_count: number;
  seasons: string[];
  date_range: {
    start: string;
    end: string;
  };
  last_updated: string;
}

export type Competitions = Competition[];
```

### フェッチ例

```typescript
// 大会メタデータ取得
const competitions: Competitions = await fetch(
  'https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/competitions.json',
).then((r) => r.json());

// 特定大会の試合データ取得
const sixNationsMatches: Matches = await fetch(
  'https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/six-nations.json',
).then((r) => r.json());
```

---

## 6. サポート

インターフェイスに関する質問や変更リクエストは、以下で受け付けます：

- **GitHub Issues**: https://github.com/Kou-ISK/rugby_scraper/issues
- **ラベル**: `interface`, `breaking-change`, `enhancement`
