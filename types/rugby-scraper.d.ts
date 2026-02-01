/**
 * rugby_scraper JSON インターフェイス型定義
 *
 * @version 1.0
 * @description itsuneru プロジェクトが rugby_scraper から取得する JSON の型定義
 * @see https://github.com/Kou-ISK/rugby_scraper/blob/main/docs/JSON_SCHEMA.md
 */

/**
 * 試合データ（data/matches/*.json）
 */
export interface Match {
  /**
   * 試合日時（現地時間）
   * @format "YYYY-MM-DD HH:MM:SS"
   * @example "2024-12-21 12:10:00"
   */
  date: string;

  /**
   * 会場名
   * @example "三重交通G スポーツの杜 鈴鹿 (三重県)"
   */
  venue: string;

  /**
   * ホームチーム名
   * @example "三重ホンダヒート"
   */
  home_team: string;

  /**
   * アウェイチーム名
   * @example "ブラックラムズ東京"
   */
  away_team: string;

  /**
   * 放送局リスト
   * @description 配列または空文字列。スクレイパーによって異なる
   * @example ["J SPORTS 3", "三重テレビ"]
   */
  broadcasters: string[] | string;

  /**
   * 試合詳細ページURL
   * @example "https://league-one.jp/match/27447"
   */
  url: string;
}

/**
 * 試合データ配列
 */
export type Matches = Match[];

/**
 * 大会メタデータ（data/competitions.json）
 */
export interface Competition {
  /**
   * 大会ID（ケバブケース）
   * @description 試合データファイル名と対応
   * @example "league-one"
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
   * @example ["data/matches/league-one.json"]
   */
  data_paths: string[];

  /**
   * 視聴情報
   */
  coverage: Coverage;

  /**
   * 参加チーム名配列
   * @description 空配列の場合あり
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
 * 大会ID一覧
 * @description itsuneru が参照可能な大会ID
 */
export type CompetitionId =
  | 'six-nations'
  | 'six-nations-women'
  | 'six-nations-u20'
  | 'epcr-champions'
  | 'epcr-challenge'
  | 'top14'
  | 'league-one'
  | 'gallagher-premiership'
  | 'urc'
  | 'super-rugby-pacific'
  | 'rugby-championship'
  | 'autumn-nations-series'
  | 'world-rugby-internationals';

/**
 * GitHub Raw URL を生成するヘルパー型
 */
export type MatchesUrl<T extends CompetitionId> =
  `https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/${T}.json`;

/**
 * 大会メタデータURL
 */
export type CompetitionsUrl =
  'https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/competitions.json';
