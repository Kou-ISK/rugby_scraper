# 日付取得検証レポート

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
