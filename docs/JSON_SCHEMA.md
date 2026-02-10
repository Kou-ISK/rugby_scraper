# JSON インターフェイス仕様

このドキュメントは、itsuneru プロジェクトが rugby_scraper から取得する JSON のインターフェイス定義です。

## 1. 試合データ（`data/matches/{comp_id}/{season}.json`）

各大会の試合データを含む配列。大会・チームのIDはマスタ（`data/competitions.json` / `data/teams.json`）を基に付与します。

### エンドポイント

```
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/{comp_id}/{season}.json
```

例:

```
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/m6n/2025.json
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/premier/2025.json
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/jrlo-div1/2026.json
```

### スキーマ

```typescript
interface Match {
  // 安定した一意ID（スクレイパーが生成）
  match_id: string;

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

  // ディビジョン（JRLOなど）
  division?: string;
}

type Matches = Match[];
```

### サンプル

```json
[
  {
    "match_id": "w6n-2026-1",
    "competition_id": "w6n",
    "season": "2026",
    "round": "",
    "status": "",
    "kickoff": "2026-04-11T11:25:00+02:00",
    "kickoff_utc": "2026-04-11T09:25:00Z",
    "timezone": "Europe/Paris",
    "venue": "Stade des Alpes",
    "home_team": "FRA",
    "away_team": "ITA",
    "home_team_id": "",
    "away_team_id": "",
    "match_url": "https://www.sixnationsrugby.com/en/w6n/fixtures/202600/france-women-v-italy-women-11042026-1125/build-up",
    "broadcasters": []
  }
]
```

### フィールド詳細

| フィールド        | 型         | 必須 | 説明                                                                     |
| ----------------- | ---------- | ---- | ------------------------------------------------------------------------ |
| `match_id`        | `string`   | ✓    | 安定ID（スクレイパーが生成）                                           |
| `competition_id`  | `string`   | ✓    | 大会ID（マスタと一致）                                                   |
| `season`          | `string`   | -    | シーズン                                                                 |
| `round`           | `string`   | -    | ラウンド/節                                                              |
| `status`          | `string`   | -    | 試合ステータス                                                           |
| `kickoff`         | `string`   | ✓    | キックオフ日時（ローカル、ISO8601）                                      |
| `kickoff_utc`     | `string`   | ✓    | キックオフ日時（UTC、ISO8601）                                           |
| `timezone`        | `string`   | ✓    | タイムゾーン                                                             |
| `venue`           | `string`   | ✓    | 会場                                                                     |
| `home_team`       | `string`   | ✓    | ホームチーム表示名                                                       |
| `away_team`       | `string`   | ✓    | アウェイチーム表示名                                                     |
| `home_team_id`    | `string`   | -    | ホームチームID（マスタと一致）                                           |
| `away_team_id`    | `string`   | -    | アウェイチームID（マスタと一致）                                         |
| `match_url`       | `string`   | ✓    | 試合詳細URL                                                              |
| `broadcasters`    | `string[]` | ✓    | 放送局配列（空配列可）                                                   |
| `division`        | `string`   | -    | ディビジョン（JRLOなど）                                                 |

### 注意事項

1. **日時形式**: `kickoff` はオフセット付きISO8601、`timezone` は IANA 形式
2. **broadcasters**: 常に配列（空配列を含む）
3. **home_team_id/away_team_id**: 未確定の場合は空文字列
4. **チーム名**: 大会によって略称（例: `ENG`, `FRA`）またはフル名（例: `三重ホンダヒート`）

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

  // 試合データファイル/ディレクトリの相対パス配列
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
    "id": "m6n",
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
    "data_paths": ["data/matches/m6n"],
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
| `logo_url`           | `string`      | -    | 大会ロゴの外部URL（公式サイト/公式CDNのオリジナル出典）    |
| `logo_repo_path`     | `string`      | -    | リポジトリ内に保存した大会ロゴパス（外部URLが使えない場合のみ） |
| `license_key`        | `string`      | -    | ロゴのライセンス情報キー（`data/logo_licenses.json` を参照）    |
| `timezone_default`   | `string`      | ✓    | デフォルトタイムゾーン（IANA形式）                              |
| `season_pattern`     | `string`      | ✓    | シーズンパターン: `"annual"` または `"variable"`                |
| `match_url_template` | `string`      | ✓    | 試合URLテンプレート（空文字列の場合あり）                       |
| `data_paths`         | `string[]`    | ✓    | 試合データファイル/ディレクトリの相対パス配列                    |
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

- `logo_url` / `badge_url` には公式サイト/公式CDNのURLを保存し、再配布を避けます。
- オリジナルURLが不安定または再配布が許可されている場合のみ、`logo_repo_path` にリポジトリ内パスを保存します。
- このプロジェクトではS3など外部ストレージは使用せず、オリジナルURL参照またはGitHubリポジトリ内保存の二択とします。
- ライセンス情報は `data/logo_licenses.json` に集約し、各オブジェクトからは `license_key` で参照します。

#### Team Branding オブジェクト（オプショナル）

大会ごとのチームロゴを管理する場合、以下のような Team Branding を別JSON（例: `data/team_logos.json`）で扱います。大会スキーマ自体は保持したまま、ロゴ関連のみ別ファイルに分離します。

| フィールド       | 型       | 必須 | 説明                                                 |
| ---------------- | -------- | ---- | ---------------------------------------------------- |
| `team`           | `string` | ✓    | チーム名またはスラッグ                               |
| `badge_url`      | `string` | -    | チームバッジの外部URL（公式サイト/公式CDN） |
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
  "premier_1": {
    "id": "premier_1",
    "competition_id": "premier",
    "name": "Leicester Tigers",
    "name_ja": "",
    "short_name": "Leicester",
    "country": "England",
    "division": "",
    "logo_url": "https://media-cdn.incrowdsports.com/...",
    "badge_url": "https://media-cdn.incrowdsports.com/..."
  },
  "NT-M-ENG": {
    "id": "NT-M-ENG",
    "competition_id": "m6n",
    "name": "England",
    "name_ja": "イングランド",
    "short_name": "ENG",
    "country": "England",
    "division": "",
    "logo_url": "",
    "badge_url": ""
  }
}
```

`home_team_id` / `away_team_id` はこのマスタのキーを参照します（未確定の場合は空文字列）。

### 3.3 チームロゴ（大会別）（`data/team_logos.json`）

大会ごとのチームロゴを配列で管理する場合に利用。`TeamBranding` 型で表現し、キーは `competition_id`。

---

## 4. 大会ID一覧

itsuneru が参照可能な大会IDとそのデータパス：

| 大会ID            | データパス                        | 大会名                        |
| ----------------- | --------------------------------- | ----------------------------- |
| `m6n`             | `data/matches/m6n`                | Six Nations                   |
| `w6n`             | `data/matches/w6n`                | Women's Six Nations           |
| `u6n`             | `data/matches/u6n`                | Six Nations U20               |
| `epcr-champions`  | `data/matches/epcr-champions`     | EPCR Champions Cup            |
| `epcr-challenge`  | `data/matches/epcr-challenge`     | EPCR Challenge Cup            |
| `t14`             | `data/matches/t14`                | Top 14                        |
| `jrlo-div1`       | `data/matches/jrlo-div1`          | Japan Rugby League One (D1)   |
| `jrlo-div2`       | `data/matches/jrlo-div2`          | Japan Rugby League One (D2)   |
| `jrlo-div3`       | `data/matches/jrlo-div3`          | Japan Rugby League One (D3)   |
| `premier`         | `data/matches/premier`            | Gallagher Premiership         |
| `urc`             | `data/matches/urc`                | United Rugby Championship     |
| `srp`             | `data/matches/srp`                | Super Rugby Pacific           |
| `trc`             | `data/matches/trc`                | The Rugby Championship        |
| `ans`             | `data/matches/ans`                | Autumn Nations Series         |
| `wr`              | `data/matches/wr`                 | World Rugby Internationals    |

---

## 5. バージョニングと互換性

### 現在のバージョン

- **Schema Version**: 1.2
- **Last Updated**: 2026-02-10

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

- 型定義は `types/rugby-scraper.d.ts` に集約
- 使い方は `docs/TYPESCRIPT_TYPES.md` を参照

### フェッチ例

```typescript
// 大会メタデータ取得
const competitions: Competitions = await fetch(
  'https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/competitions.json',
).then((r) => r.json());

// 特定大会の試合データ取得
const sixNationsMatches: Matches = await fetch(
  'https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/m6n/2026.json',
).then((r) => r.json());
```

---

## 6. サポート

インターフェイスに関する質問や変更リクエストは、以下で受け付けます：

- **GitHub Issues**: https://github.com/Kou-ISK/rugby_scraper/issues
- **ラベル**: `interface`, `breaking-change`, `enhancement`
