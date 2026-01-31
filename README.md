# rugby_scraper

itsuneru 向けに世界のラグビー試合日程を取得するスクレイパーです。

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
- World Rugby Internationals (Autumn Nations Series / The Rugby Championship / Test Matches)
  - 公式サイト: world.rugby
  - 公式データ: api.wr-rims-prod.pulselive.com (World Rugby の公開データエンドポイント)
  - ソース種別: official

## 出力JSONの共通スキーマ
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

## 使い方

```bash
python src/main.py <scraper-type>
```

例:

```bash
python src/main.py six-nations
python src/main.py gallagher-premiership
python src/main.py urc
python src/main.py super-rugby-pacific
python src/main.py world-rugby-internationals
```

## 取得パス一覧 (itsuneru向け)
itsuneru 側から取得する場合は、以下の JSON パスを参照してください。

- Six Nations: `data/matches/six-nations.json`
- Women's Six Nations: `data/matches/six-nations-women.json`
- Six Nations U20: `data/matches/six-nations-u20.json`
- EPCR Champions Cup: `data/matches/epcr-champions.json`
- EPCR Challenge Cup: `data/matches/epcr-challenge.json`
- Top 14: `data/matches/top14.json`
- Japan Rugby League One: `data/matches/league-one.json`
- Gallagher Premiership: `data/matches/gallagher-premiership.json`
- United Rugby Championship: `data/matches/urc.json`
- Super Rugby Pacific: `data/matches/super-rugby-pacific.json`
- World Rugby Internationals: `data/matches/world-rugby-internationals.json`

## 大会メタデータ
大会ごとの詳細情報は `data/competitions.json` にまとめています。

主なフィールド:
- id / name / short_name
- sport / category / gender / age_grade / tier / region
- governing_body / organizer
- official_sites / official_feeds
- timezone_default / season_pattern / match_url_template
- data_paths
- coverage.broadcast_regions / coverage.analysis_providers
- teams
- data_summary.match_count / data_summary.seasons / data_summary.date_range / data_summary.last_updated

`data/competitions.json` は取得済みの試合データから自動生成されます。

```bash
python -m src.metadata.generate_competitions
```

## GitHub Raw での取得URL例
`data` ブランチに更新されるため、以下の形式で最新データを取得できます。

```
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/<file>.json
```

例:

```
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/six-nations.json
```
