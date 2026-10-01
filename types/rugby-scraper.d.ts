/**
 * rugby_scraper JSON インターフェイス型定義
 *
 * @version 1.4
 * @description itsuneru プロジェクトが rugby_scraper から取得する JSON の型定義
 * @see https://github.com/Kou-ISK/rugby_scraper/blob/main/docs/JSON_SCHEMA.md
 * @updated 2026-02-10 - 現行JSON出力に合わせてフィールドを整理
 */

/**
 * 試合データ（data/matches/{comp_id}/{season}.json）
 */
export interface Match {
  /**
   * 試合ID（ユニークID）
   * @description 互換用の並び順ID。保存プランの照合には stable_id を使う
   * @example "w6n-2026-1"
   */
  match_id: string;

  /** 公式識別子／URLから生成した、並び順に依存しないID */
  stable_id: string;
  source_match_id?: string;
  source_provider: string;
  identity_version: 2;
  /** 移行候補。大会/season/provider/元snapshotも照合してから使う */
  previous_stable_ids?: string[];
  /** weak の場合は日付・対戦カードの変更を自動照合しない */
  identity_strength: 'official' | 'url' | 'weak';
  /** 時刻未定で日付のみ判明している場合。深夜0時として扱わない */
  kickoff_date?: string;

  /**
   * 大会ID（新形式）
   * @description competitions.json の id と一致
   * @example "w6n", "m6n", "jrlo"
   */
  competition_id: string;

  /**
   * シーズン
   * @example "2026", "2026-2027"
   */
  season: string;

  /**
   * ラウンド
   * @example "Round 1", "Pool A"
   */
  round: string;

  /**
   * 試合ステータス
   * @example "scheduled", "live", "completed"
   */
  status: string;

  /**
   * キックオフ日時（現地時間、ISO8601形式）
   * @example "2026-03-14T15:00:00+00:00"
   */
  kickoff: string;

  /**
   * キックオフ日時（UTC、ISO8601形式）
   * @example "2026-03-14T15:00:00Z"
   */
  kickoff_utc: string;

  /**
   * タイムゾーン（IANA形式）
   * @example "Europe/London", "Asia/Tokyo"
   */
  timezone: string;

  /**
   * 会場名
   * @example "Twickenham Stadium"
   */
  venue: string;

  /**
   * ホームチーム名（表示名）
   * @example "ENG", "England"
   */
  home_team: string;

  /**
   * アウェイチーム名（表示名）
   * @example "FRA", "France"
   */
  away_team: string;

  /**
   * ホームチームID（新形式）
   * @description チームマスタの id と一致（未確定の場合は空文字列）
   * @example "w6n_1", "jrlo-div1_1", ""
   */
  home_team_id: string;

  /**
   * アウェイチームID（新形式）
   * @description チームマスタの id と一致（未確定の場合は空文字列）
   * @example "w6n_2", "jrlo-div1_2", ""
   */
  away_team_id: string;

  /**
   * 試合詳細ページURL
   * @example "https://www.sixnationsrugby.com/en/w6n/fixtures/2026/..."
   */
  match_url: string;

  /**
   * 放送局リスト
   * @example ["J SPORTS 3", "三重テレビ"]
   */
  broadcasters: string[];

  /**
   * ディビジョン（JRLO の場合など）
   * @example "Division 1"
   */
  division?: string;
}

/**
 * 試合データ配列
 */
export type Matches = Match[];

export interface FixtureCoverage {
  match_count: number;
  known_kickoffs: number;
  unknown_kickoffs: number;
  date_range: { start: string; end: string };
}

export interface FixtureFile {
  path: string;
  season: string;
  sha256: string;
  match_count: number;
  known_kickoffs: number;
  unknown_kickoffs: number;
  trust: 'verified' | 'unverified' | 'invalid';
  validated_at: string;
  error: string;
}

export interface FixtureManifest {
  schema_version: 1;
  generated_at: string;
  competitions: Array<{
    id: string;
    name: string;
    data_paths: string[];
    seasons: string[];
    status: 'healthy' | 'partial' | 'stale' | 'unavailable';
    last_success_at: string;
    last_attempt_at: string;
    error: string;
    coverage: FixtureCoverage;
    files: FixtureFile[];
  }>;
}

/**
 * チームマスタデータ（data/teams.json）
 */
export interface Team {
  /**
   * チームID（新形式）
   * @description クラブ: {comp_id}_{number}, 国代表: NT-{M|W|U20}-{COUNTRY}[-{VARIANT}]
   * @example "premier_1", "jrlo-div1_12", "NT-M-ENG"
   */
  id: string;

  /**
   * 所属大会ID
   * @example "w6n", "m6n", "jrlo"
   */
  competition_id: string;

  /**
   * チーム名（英語）
   * @example "England", "Saitama Wild Knights"
   */
  name: string;

  /**
   * チーム名（日本語）
   * @example "イングランド", "埼玉ワイルドナイツ"
   */
  name_ja: string;

  /**
   * チーム略称
   * @example "ENG", "Wild Knights"
   */
  short_name: string;

  /**
   * 国名
   * @example "England", "Japan"
   */
  country: string;

  /**
   * ディビジョン（クラブチームの場合）
   * @example "Division 1"
   */
  division: string;

  /**
   * チームロゴURL
   * @description 公式サイト/公式CDNなどの外部URL
   */
  logo_url: string;

  /**
   * チームバッジURL
   * @description 公式サイト/公式CDNなどの外部URL
   */
  badge_url: string;
}

/**
 * チームマスタ
 * @description チームIDをキーとするレコード型
 */
export type Teams = Record<string, Team>;

/**
 * 大会メタデータ（data/competitions.json）
 */
export interface Competition {
  /**
   * 大会ID（新形式）
   * @description 性別を明示した略称コード
   * @example "m6n", "w6n", "jrlo"
   */
  id: string;

  /**
   * 大会正式名称
   * @example "Japan Rugby League One"
   */
  name: string;

  /**
   * 大会略称
   * @example "League One"
   */
  short_name: string;

  /**
   * スポーツ種目
   * @description 現在は rugby union のみ
   */
  sport: 'rugby union';

  /**
   * カテゴリー
   */
  category: 'international' | 'club';

  /**
   * 性別
   */
  gender: 'men' | 'women' | 'mixed';

  /**
   * 年齢区分
   */
  age_grade: 'senior' | 'u20';

  /**
   * ティア
   */
  tier: 'tier-1' | 'tier-2' | 'tier-3';

  /**
   * 地域
   * @example "Japan", "Europe", "Oceania"
   */
  region: string;

  /**
   * 統括団体
   * @example "Japan Rugby League One"
   */
  governing_body: string;

  /**
   * 主催者
   * @example "Japan Rugby League One"
   */
  organizer: string;

  /**
   * 公式サイトURL配列
   * @example ["https://league-one.jp"]
   */
  official_sites: string[];

  /**
   * 公式データフィードURL配列
   * @description 空配列の場合あり
   */
  official_feeds: string[];

  /**
   * 大会ロゴの外部URL
   * @description 可能な限りオリジナル出典（TheSportsDB / Wikimedia 等）のURLを保持
   */
  logo_url?: string;

  /**
   * リポジトリ内に保存したロゴパス
   * @description 外部URLが使えない場合のみ設定
   */
  logo_repo_path?: string;

  /**
   * ロゴのライセンス情報キー
   * @description data/logo_licenses.json のキーを参照
   */
  license_key?: string;

  /**
   * デフォルトタイムゾーン
   * @description IANA タイムゾーン形式
   * @example "Asia/Tokyo", "Europe/London"
   */
  timezone_default: string;

  /**
   * シーズンパターン
   */
  season_pattern: 'annual' | 'variable';

  /**
   * 試合URLテンプレート
   * @description 空文字列の場合あり
   * @example "https://league-one.jp/match/{matchId}"
   */
  match_url_template: string;

  /**
   * 試合データファイルの相対パス配列
   * @description ディレクトリパスまたはファイルパス
   * @example ["data/matches/w6n"]
   */
  data_paths: string[];

  /**
   * 視聴情報
   */
  coverage: Coverage;

  /**
   * 参加チーム名配列
   * @description 空配列の場合あり（現状は未登録）
   * @example ["三重ホンダヒート", "ブラックラムズ東京"]
   */
  teams: string[];

  /**
   * データサマリー
   */
  data_summary: DataSummary;
}

/**
 * 視聴情報
 */
export interface Coverage {
  /**
   * 地域別放送情報配列
   */
  broadcast_regions: BroadcastRegion[];

  /**
   * 分析プロバイダー配列
   */
  analysis_providers: AnalysisProvider[];

  /**
   * 視聴時の注意事項
   * @description VPN要否、地域制限などを記載
   * @optional
   */
  notes?: string;
}

/**
 * 地域別放送情報
 */
export interface BroadcastRegion {
  /**
   * 対象地域
   * @description ISO国コードまたは地域名
   * @example "JP", "UK/IE", "International"
   */
  region: string;

  /**
   * 配信・放送プロバイダー名配列
   * @example ["J SPORTS", "J SPORTSオンデマンド"]
   */
  providers: string[];

  /**
   * 公式情報源URL
   * @example "https://league-one.jp/news/3842"
   */
  official_source: string;
}

/**
 * 分析プロバイダー
 */
export interface AnalysisProvider {
  /**
   * プロバイダー名
   * @example "ESPN Rugby"
   */
  name: string;

  /**
   * 公式サイトURL
   * @example "https://www.espn.com/rugby/"
   */
  official_source: string;
}

/**
 * データサマリー
 */
export interface DataSummary {
  /**
   * 試合数
   * @example 209
   */
  match_count: number;

  /**
   * シーズン一覧
   * @description 空配列の場合あり
   * @example ["2024-25"]
   */
  seasons: string[];

  /**
   * 日付範囲
   */
  date_range: {
    /**
     * 開始日
     * @description ISO8601形式または空文字列
     * @example "2024-12-21T12:10:00"
     */
    start: string;

    /**
     * 終了日
     * @description ISO8601形式または空文字列
     * @example "2025-05-31T15:00:00"
     */
    end: string;
  };

  /**
   * 最終更新日時
   * @description ISO8601形式または空文字列
   * @example "2025-02-02T15:58:10.806643"
   */
  last_updated: string;
}

/**
 * 大会メタデータ配列
 */
export type Competitions = Competition[];

/**
 * チームのブランド情報（ロゴ・バッジ）
 */
export interface TeamBranding {
  /**
   * チーム名またはスラッグ
   */
  team: string;

  /**
   * チームバッジの外部URL（TheSportsDB strBadge 等）
   */
  badge_url?: string;

  /**
   * チームロゴの外部URL
   */
  logo_url?: string;

  /**
   * リポジトリ内に保存したロゴパス
   */
  logo_repo_path?: string;

  /**
   * ライセンス情報キー（data/logo_licenses.json）
   */
  license_key?: string;
}

/**
 * 大会IDをキーにしたチームブランド情報レコード
 */
export type TeamBrandings = Record<string, TeamBranding[]>;

/**
 * 大会ID一覧（新形式）
 * @description itsuneru が参照可能な大会ID - 性別を明示した略称コード
 */
export type CompetitionId =
  | 'm6n' // Men's Six Nations
  | 'w6n' // Women's Six Nations
  | 'u6n' // U20 Six Nations
  | 'epcr-champions' // EPCR Champions Cup
  | 'epcr-challenge' // EPCR Challenge Cup
  | 't14' // Top 14
  | 'jrlo-div1' // Japan Rugby League One Division 1
  | 'jrlo-div2' // Japan Rugby League One Division 2
  | 'jrlo-div3' // Japan Rugby League One Division 3
  | 'premier' // Gallagher Premiership
  | 'urc' // United Rugby Championship
  | 'srp' // Super Rugby Pacific
  | 'trc' // The Rugby Championship
  | 'ans' // Autumn Nations Series
  | 'wr'; // World Rugby Internationals

/**
 * 旧大会ID（非推奨）
 * @deprecated 新しい CompetitionId を使用してください
 */
export type LegacyCompetitionId =
  | 'six-nations'
  | 'six-nations-women'
  | 'six-nations-u20'
  | 'top14'
  | 'league-one'
  | 'gallagher-premiership'
  | 'urc'
  | 'super-rugby-pacific'
  | 'rugby-championship'
  | 'autumn-nations-series'
  | 'world-rugby-internationals'
  | 'gp'
  | 'ecc'
  | 'ech'
  | 'wri'
  | 'jrlo_div1'
  | 'jrlo_div2'
  | 'jrlo_div3';

/**
 * GitHub Raw URL を生成するヘルパー型（新構造対応）
 * @description 新ディレクトリ構造: data/matches/{comp_id}/{season}.json
 */
export type MatchesUrl<
  T extends CompetitionId,
  S extends string = string,
> = `https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/${T}/${S}.json`;

/**
 * チームマスタURL
 */
export type TeamsUrl =
  'https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/teams.json';

/**
 * 大会メタデータURL
 */
export type CompetitionsUrl =
  'https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/competitions.json';
