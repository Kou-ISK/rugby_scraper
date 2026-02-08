# JSON インターフェイス仕様

このドキュメントは、itsuneru プロジェクトが rugby_scraper から取得する JSON のインターフェイス定義です。

## 1. 試合データ（`data/matches/*.json`）

各大会の試合データを含む配列。大会・チームのIDはマスタ（`data/competitions.json` / `data/teams.json`）を基に付与します。

### エンドポイント

```
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/{comp_id}/{season}.json
```

例:

```
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/m6n/2025.json
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/gp/2025.json
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/jrlo_div1/2026.json
```

### スキーマ

```typescript
interface Match {
  // 安定した一意ID（competition_id + kickoff_utc + home/awayで生成）
  match_id: string;

  // 大会名
  competition: string;

  // 大会ID（マスタの id と一致）
  competition_id: string;

  // シーズン（存在すれば）
  season: string;

  // ラウンド/節（存在すれば）
  round: string;

  // 試合ステータス（例: "scheduled", "finished"）
  status: string;

  // キックオフ日時（ローカル）
  kickoff: string; // ISO8601

  // キックオフ日時（UTC）
  kickoff_utc: string; // ISO8601

  // タイムゾーン
  timezone: string;

  // タイムゾーンの決定根拠（例: "home_team_default"）
  timezone_source: string;

  // 会場
  venue: string;

  // ホームチーム表示名
  home_team: string;

  // アウェイチーム表示名
  away_team: string;

  // ホームチームID（マスタと一致）
  home_team_id: string;

  // アウェイチームID（マスタと一致）
  away_team_id: string;

  // 試合詳細ページURL
  match_url: string;

  // 放送局リスト
  broadcasters: string[];

  // 取得元情報
  source_name: string;
  source_url: string;
  source_type: string;
}

type Matches = Match[];
```

### サンプル

```json
[
  {
    "match_id": "six-nations-2026-02-05t20:10:00z-fra-ire",
    "competition": "Six Nations",
    "competition_id": "six-nations",
    "season": "2026",
    "round": "Round 1",
    "status": "scheduled",
    "kickoff": "2026-02-05T21:10:00+01:00",
    "kickoff_utc": "2026-02-05T20:10:00Z",
    "timezone": "Europe/Paris",
    "timezone_source": "home_team_default",
    "venue": "Stade de France",
    "home_team": "FRA",
    "away_team": "IRE",
    "home_team_id": "fra",
    "away_team_id": "ire",
    "match_url": "https://www.sixnationsrugby.com/en/m6n/fixtures/202600/france-v-ireland-05022026-2110/build-up",
    "broadcasters": [],
    "source_name": "Six Nations Rugby",
    "source_url": "https://www.sixnationsrugby.com/en/m6n/fixtures/2026",
    "source_type": "official"
  }
]
```

### フィールド詳細

| フィールド        | 型         | 必須 | 説明                                                                     |
| ----------------- | ---------- | ---- | ------------------------------------------------------------------------ |
| `match_id`        | `string`   | ✓    | 安定ID（`competition_id`/`kickoff_utc`/`home_team`/`away_team`から生成） |
| `competition`     | `string`   | ✓    | 大会名                                                                   |
| `competition_id`  | `string`   | ✓    | 大会ID（マスタと一致）                                                   |
| `season`          | `string`   | -    | シーズン                                                                 |
| `round`           | `string`   | -    | ラウンド/節                                                              |
| `status`          | `string`   | -    | 試合ステータス                                                           |
| `kickoff`         | `string`   | ✓    | キックオフ日時（ローカル、ISO8601）                                      |
| `kickoff_utc`     | `string`   | ✓    | キックオフ日時（UTC、ISO8601）                                           |
| `timezone`        | `string`   | ✓    | タイムゾーン                                                             |
| `timezone_source` | `string`   | -    | タイムゾーン決定根拠                                                     |
| `venue`           | `string`   | ✓    | 会場                                                                     |
| `home_team`       | `string`   | ✓    | ホームチーム表示名                                                       |
| `away_team`       | `string`   | ✓    | アウェイチーム表示名                                                     |
| `home_team_id`    | `string`   | -    | ホームチームID（マスタと一致）                                           |
| `away_team_id`    | `string`   | -    | アウェイチームID（マスタと一致）                                         |
| `match_url`       | `string`   | ✓    | 試合詳細URL                                                              |
| `broadcasters`    | `string[]` | ✓    | 放送局配列（空配列可）                                                   |
| `source_name`     | `string`   | ✓    | 取得元名                                                                 |
| `source_url`      | `string`   | ✓    | 取得元URL                                                                |
| `source_type`     | `string`   | ✓    | 取得元種別（official/third-partyなど）                                   |

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

  // 大会ロゴの外部URL（可能な限りオリジナルの出典を利用）
  logo_url?: string;

  // リポジトリ内に保存した大会ロゴのパス（外部URLが使えない場合のみ）
  logo_repo_path?: string;

  // ロゴのライセンス情報を参照するキー（data/logo_licenses.json）
  license_key?: string;

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

| フィールド           | 型            | 必須 | 説明                                                            |
| -------------------- | ------------- | ---- | --------------------------------------------------------------- |
| `id`                 | `string`      | ✓    | 大会ID（ケバブケース）。試合データファイル名と対応              |
| `name`               | `string`      | ✓    | 大会正式名称                                                    |
| `short_name`         | `string`      | ✓    | 大会略称                                                        |
| `sport`              | `string`      | ✓    | スポーツ種目（現在は `"rugby union"` のみ）                     |
| `category`           | `string`      | ✓    | カテゴリー: `"international"` または `"club"`                   |
| `gender`             | `string`      | ✓    | 性別: `"men"`, `"women"`, `"mixed"`                             |
| `age_grade`          | `string`      | ✓    | 年齢区分: `"senior"`, `"u20"`                                   |
| `tier`               | `string`      | ✓    | ティア: `"tier-1"`, `"tier-2"`, `"tier-3"`                      |
| `region`             | `string`      | ✓    | 地域（例: `"Europe"`, `"Japan"`, `"Oceania/Americas/Africa"`）  |
| `governing_body`     | `string`      | ✓    | 統括団体名                                                      |
| `organizer`          | `string`      | ✓    | 主催者名                                                        |
| `official_sites`     | `string[]`    | ✓    | 公式サイトURL配列                                               |
| `official_feeds`     | `string[]`    | ✓    | 公式データフィードURL配列（空配列の場合あり）                   |
| `logo_url`           | `string`      | -    | 大会ロゴの外部URL（Wikimedia/TheSportsDBなどオリジナル出典）    |
| `logo_repo_path`     | `string`      | -    | リポジトリ内に保存した大会ロゴパス（外部URLが使えない場合のみ） |
| `license_key`        | `string`      | -    | ロゴのライセンス情報キー（`data/logo_licenses.json` を参照）    |
| `timezone_default`   | `string`      | ✓    | デフォルトタイムゾーン（IANA形式）                              |
| `season_pattern`     | `string`      | ✓    | シーズンパターン: `"annual"` または `"variable"`                |
| `match_url_template` | `string`      | ✓    | 試合URLテンプレート（空文字列の場合あり）                       |
| `data_paths`         | `string[]`    | ✓    | 試合データファイルの相対パス配列                                |
| `coverage`           | `Coverage`    | ✓    | 視聴情報オブジェクト                                            |
| `teams`              | `string[]`    | ✓    | 参加チーム名配列（空配列の場合あり）                            |
| `data_summary`       | `DataSummary` | ✓    | データサマリーオブジェクト                                      |

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

### ロゴとライセンス

ブランド情報は以下の方針で追加します。

- `logo_url` / `badge_url` には極力オリジナルの配信元（TheSportsDB, Wikimedia など）のURLを保存し、再配布を避けます。
- オリジナルURLが不安定または再配布が許可されている場合のみ、`logo_repo_path` にリポジトリ内パスを保存します。
- このプロジェクトではS3など外部ストレージは使用せず、オリジナルURL参照またはGitHubリポジトリ内保存の二択とします。
- ライセンス情報は `data/logo_licenses.json` に集約し、各オブジェクトからは `license_key` で参照します。

#### Team Branding オブジェクト（オプショナル）

大会ごとのチームロゴを管理する場合、以下のような Team Branding を別JSON（例: `data/team_logos.json`）で扱います。大会スキーマ自体は保持したまま、ロゴ関連のみ別ファイルに分離します。

| フィールド       | 型       | 必須 | 説明                                                 |
| ---------------- | -------- | ---- | ---------------------------------------------------- |
| `team`           | `string` | ✓    | チーム名またはスラッグ                               |
| `badge_url`      | `string` | -    | チームバッジの外部URL（TheSportsDB `strBadge` など） |
| `logo_url`       | `string` | -    | チームロゴの外部URL（必要に応じて使用）              |
| `logo_repo_path` | `string` | -    | リポジトリ内に保存したロゴパス                       |
| `license_key`    | `string` | -    | ロゴのライセンス情報キー                             |

#### ライセンス情報ファイル（`data/logo_licenses.json`）

ロゴやバッジのライセンス・出典情報を集約します。`license_key` で参照します。

```json
{
  "challenge_cup_logo": {
    "license": "CC BY-SA 4.0",
    "source": "Wikimedia Commons",
    "notes": "再配布時は著作者表示と同一ライセンスを要求"
  },
  "top14_logo": {
    "license": "public_domain",
    "source": "Wikimedia Commons",
    "notes": "簡素な幾何学的形状で著作権対象外"
  },
  "premiership_logo": {
    "license": "public_domain",
    "source": "Wikimedia Commons",
    "notes": "著作権対象外だが商標権に注意"
  }
}
```

---

## 3. マスタデータ

### 3.1 大会マスタ（`data/competitions.json`）

既存の大会メタデータにロゴ関連フィールドをオプショナルで追加済み。試合保存時は `competition_id` にこの `id` をセットする。

### 3.2 チームマスタ（`data/teams.json`）

大会横断で利用するチームID・正式名・ロゴ参照を定義します。例：

```json
{
  "fra": {
    "id": "fra",
    "name": "France",
    "short_name": "FRA",
    "country": "France"
  },
  "ire": {
    "id": "ire",
    "name": "Ireland",
    "short_name": "IRE",
    "country": "Ireland"
  }
}
```

`home_team_id` / `away_team_id` はこのマスタのキーを参照します。

### 3.3 チームロゴ（大会別）（`data/team_logos.json`）

大会ごとのチームロゴを配列で管理する場合に利用。`TeamBranding` 型で表現し、キーは `competition_id`。

---

## 4. 大会ID一覧

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

## 5. バージョニングと互換性

### 現在のバージョン

- **Schema Version**: 1.1
- **Last Updated**: 2026-02-05

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

## 6. 使用例（itsuneru側）

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
  logo_url?: string;
  logo_repo_path?: string;
  license_key?: string;
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

export interface TeamBranding {
  team: string;
  badge_url?: string;
  logo_url?: string;
  logo_repo_path?: string;
  license_key?: string;
}

// 大会IDをキーにしたチームブランド情報のレコード
export type TeamBrandings = Record<string, TeamBranding[]>;
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
