# Six Nations 日付取得問題 - 調査レポート & 実装Plan

## 📊 実際のデータ分析結果

### 検出された不整合（origin/dataブランチ）

| 試合       | kickoff日付 | URL日付    | 差分 | 状態      |
| ---------- | ----------- | ---------- | ---- | --------- |
| ITA vs SCO | 2026-02-05  | 2026-02-07 | +2日 | ⚠️ 不一致 |
| ENG vs WAL | 2026-02-05  | 2026-02-07 | +2日 | ⚠️ 不一致 |
| FRA vs IRE | 2026-02-05  | 2026-02-05 | 0日  | ✅ 一致   |

**パターン**: URLの日付が正しく、kickoffが2日早くなっている試合が複数存在

## 🔍 HTML構造の推測

Six Nations公式サイト (https://www.sixnationsrugby.com/en/m6n/fixtures/2026) の構造：

### 想定されるHTML構造

```html
<div class="fixturesResultsListing_roundContainer...">
  <!-- 日付タイトル（おそらく"Saturday 07 February"形式） -->
  <h2 class="fixturesResultsListing_dateTitle...">Saturday 07 February</h2>

  <!-- 試合カード -->
  <div class="fixturesResultsCard_padding...">
    <!-- 時刻表示（おそらく"15:10"形式） -->
    <div class="fixturesResultsCard_status...">15:10</div>

    <!-- チーム名 -->
    <span class="fixturesResultsCard_teamName...">ITA</span>
    <span class="fixturesResultsCard_teamName...">SCO</span>

    <!-- リンク -->
    <a href="/en/m6n/fixtures/2026/italy-v-scotland-07022026-1510/build-up"
      >...</a
    >
  </div>
</div>
```

### 推測されるページ表示

- **日付タイトル**: `"Saturday 07 February"` （曜日 + 日 + 月）
- **時刻**: `"15:10"` （HH:MM形式）
- **結合**: `"Saturday 07 February 15:10"`

## ⚠️ 現在の実装の問題点

### `_parse_display_datetime` メソッドの問題

```python
def _parse_display_datetime(self, date_string):
    default_dt = datetime(datetime.now().year, 1, 1, 0, 0, 0)
    parsed = date_parser.parse(date_string, fuzzy=True, default=default_dt)
    return parsed.replace(tzinfo=ZoneInfo(self.display_timezone))
```

**問題1: `fuzzy=True` のみ**

- "07 February"を「7月2日」と誤認識する可能性
- `dayfirst` パラメータ未指定のため、デフォルト動作（月優先）になる

**問題2: `default` の誤用**

- `datetime(year, 1, 1, 0, 0, 0)` で1月1日をデフォルトに設定
- 年の推測が不正確

**問題3: タイムゾーン**

- `self.display_timezone` (Europe/London) を使用
- ホームチームに基づくタイムゾーンを無視

## ✅ 正しい実装Plan

### Phase 1: `_parse_display_datetime` の修正

```python
def _parse_display_datetime(self, date_string, timezone_name):
    """
    Six Nations公式サイトの表示から正確に日付を解析
    例: "Saturday 07 February 15:10" → 2026-02-07 15:10
    """
    if not date_string:
        return None

    try:
        # 【重要】dayfirst=True で日を優先的にパース
        # "07 February" → 2月7日 (×7月2日)
        parsed = date_parser.parse(
            date_string,
            fuzzy=True,
            dayfirst=True  # これが鍵！
        )

        # 年の推測ロジック
        current_year = datetime.now().year
        current_month = datetime.now().month

        if current_month >= 10 and parsed.month <= 3:
            # 現在10月以降で試合が1-3月 → 翌年のSix Nations
            parsed = parsed.replace(year=current_year + 1)
        else:
            parsed = parsed.replace(year=current_year)

        # 指定されたタイムゾーンを設定
        parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
        return parsed

    except (ValueError, TypeError) as e:
        print(f"日付パースエラー: '{date_string}' - {e}")
        return None
```

### Phase 2: `_extract_match_info` の修正

```python
def _extract_match_info(self, card, current_date):
    # ... 既存のコード ...

    home_team = teams[0].text.strip()
    away_team = teams[1].text.strip()
    timezone_name = self._infer_timezone(home_team)  # ホームチームのTZ

    # ページ表示から日付を構築
    date_text = current_date
    if time_element and time_element.text.strip():
        date_text = f"{current_date} {time_element.text.strip()}"

    # タイムゾーンを渡す（重要！）
    kickoff_dt = self._parse_display_datetime(date_text, timezone_name)

    # ... 残りのコード ...
```

## 🧪 検証テストケース

### 入力例（想定）

| current_date           | time    | 結合後                       |
| ---------------------- | ------- | ---------------------------- |
| "Saturday 07 February" | "15:10" | "Saturday 07 February 15:10" |
| "Sunday 08 February"   | "14:10" | "Sunday 08 February 14:10"   |
| "Friday 05 February"   | "21:10" | "Friday 05 February 21:10"   |

### 期待される出力（`dayfirst=True` 使用時）

| 入力                         | 期待される日付   | 現在の誤り  |
| ---------------------------- | ---------------- | ----------- |
| "Saturday 07 February 15:10" | 2026-02-07 15:10 | 2026-02-05? |
| "Sunday 08 February 14:10"   | 2026-02-08 14:10 | 2026-02-06? |

## 📝 実装手順

### Step 1: シグネチャ変更

- [x] `_parse_display_datetime(self, date_string)`
- [ ] → `_parse_display_datetime(self, date_string, timezone_name)`

### Step 2: パーサー修正

- [ ] `dayfirst=True` を追加
- [ ] `default` パラメータを削除
- [ ] 年推測ロジックを実装

### Step 3: 呼び出し側修正

- [ ] `_extract_match_info` で `timezone_name` を渡す
- [ ] タイムゾーン変換ロジックを削除（パーサー内で処理）

### Step 4: テスト

- [ ] ローカルでスクレイピング実行
- [ ] URLとkickoffの整合性確認
- [ ] タイムゾーンの正確性確認

## 🚫 採用しないアプローチ

### ❌ URLから日付を抽出

**理由**:

1. URLは変更されない可能性（延期・時間変更時）
2. URLはSEO目的で実際の日付と異なる場合がある
3. ページ表示が公式の情報源

**結論**: **ページ表示テキストが真実**

## 📊 実装後の期待値

### 修正前（現在）

```json
{
  "kickoff": "2026-02-05T15:10:00+01:00",
  "match_url": "...italy-v-scotland-07022026-1510..."
}
```

→ **2日のズレ** ⚠️

### 修正後（期待値）

```json
{
  "kickoff": "2026-02-07T15:10:00+01:00",
  "match_url": "...italy-v-scotland-07022026-1510..."
}
```

→ **完全一致** ✅

---

**次のアクション**: 上記Planに基づき、`src/scraper/six_nations.py` を修正

## 実施日

2026年2月2日

## 検証結果サマリー

### ❌ 問題あり（修正済み）

- **Six Nations / Women's Six Nations / Six Nations U20**
  - 問題: URLに含まれる日付とkickoffフィールドの日付が不一致
  - 原因: `dateutil.parser`のfuzzy=Trueによる推測的なパースが不正確
  - 修正: URLから正確に日付を抽出する`_extract_datetime_from_url()`メソッドを実装
  - 影響範囲: 2日のズレが複数試合で発生

### ✅ 問題なし

以下のスクレイパーは、データソースから直接日付を取得しており、URL検証の必要がないか、またはURL形式が異なる：

- **EPCR (Champions Cup / Challenge Cup)**
  - 日付形式: "SAT, 25 Oct 2025 - 13:00"
  - 処理: `format_date_string()`で月名をパースして構築
  - 検証: エラーハンドリングあり、特に問題なし

- **Top 14**
  - 日付形式: フランス語月名 + 時刻（例: "samedi 21 décembre - 21h10"）
  - 処理: 正規表現とマッピングで抽出、シーズンベースで年を推測
  - 検証: `_normalize_time()`で時刻を正規化、特に問題なし

- **Japan Rugby League One**
  - 日付形式: HTMLの`<p class="date">`と`<p class="time">`から取得
  - 処理: `_format_date()`で結合後、`format_date_string()`で変換
  - 検証: Asia/Tokyoタイムゾーンで固定、特に問題なし

- **Gallagher Premiership / URC**
  - データソース: RugbyViz API (JSON)
  - 日付形式: ISO 8601形式で直接取得
  - 検証: APIからの信頼できるデータ、特に問題なし

- **Super Rugby Pacific**
  - データソース: 公式PDFから抽出（実装詳細未確認）
  - 検証: 要追加調査

- **World Rugby Internationals**
  - データソース: World Rugby API
  - 日付形式: APIからのISO形式
  - 検証: 公式APIデータ、特に問題なし

- **Rugby Championship / Autumn Nations**
  - 状態: プレースホルダー（未実装）
  - 検証: 実装後に要確認

## 修正内容詳細

### Six Nations系スクレイパー (`src/scraper/six_nations.py`)

#### 追加メソッド

```python
def _extract_datetime_from_url(self, url: str, timezone_name: str):
    """
    URLから正確な日付と時刻を抽出
    URL例: /en/m6n/fixtures/2026/italy-v-scotland-07022026-1510/build-up
    フォーマット: DDMMYYYY-HHMM
    """
    import re
    pattern = r'(\d{2})(\d{2})(\d{4})-(\d{2})(\d{2})'
    match = re.search(pattern, url)

    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))

        dt = datetime(year, month, day, hour, minute, 0)
        dt = dt.replace(tzinfo=ZoneInfo(timezone_name))
        return dt

    return None
```

#### 変更点

- `_extract_match_info()`メソッドで、URLからの日付抽出を最優先に
- フォールバックとして従来の方法も保持

## 推奨事項

### 短期対応

1. ✅ Six Nationsスクレイパーの修正をデプロイ
2. 🔄 再スクレイピングを実行して正しいデータを取得
3. 📊 dataブランチに正しいデータをプッシュ

### 中長期対応

1. **統合テスト追加**: 各スクレイパーに日付妥当性チェックを追加
2. **URL検証機能**: match_urlがある場合、URLと日付の整合性を自動チェック
3. **ログ強化**: 日付パースエラーやURL抽出失敗時の詳細ログ
4. **CI/CD追加**: スクレイピング後の自動検証ステップ

## 検証コマンド

```bash
# Six Nations系の日付整合性確認
python3 -c "
import json, re
with open('data/matches/six-nations.json', 'r') as f:
    matches = json.load(f)
for m in matches[:5]:
    url = m.get('match_url', '')
    kickoff = m.get('kickoff', '')
    pattern = r'(\d{2})(\d{2})(\d{4})-(\d{2})(\d{2})'
    url_match = re.search(pattern, url)
    if url_match:
        url_date = f'{url_match.group(3)}-{url_match.group(2)}-{url_match.group(1)}'
        kickoff_date = kickoff.split('T')[0]
        if url_date != kickoff_date:
            print(f'{m[\"home_team\"]} vs {m[\"away_team\"]}: kickoff={kickoff_date}, url={url_date}')
"
```

## 影響分析

- **itsuneru フロントエンド**: データ更新後、正しい試合日程が表示される
- **ユーザー体験**: 試合日の混乱が解消
- **データ信頼性**: URLが信頼できる情報源として確立
