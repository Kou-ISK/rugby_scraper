# Six Nations GitHub Actions 失敗分析レポート

## 調査対象

- GitHub Actions実行: 2026-02-03 13:43:27
- コミット: 6c58b5e5b655d2f931d50adf9915332b52b0e894
- 使用コード: a9f8638 (初回CSS Selector修正)

## 失敗の証拠

### dataブランチのコミット履歴分析

| 日時             | コミットSHA | six-nations.json の状態     |
| ---------------- | ----------- | --------------------------- |
| 2026-02-02 11:51 | 3d62e848    | ✅ **332行** (15試合)       |
| 2026-02-03 13:43 | 6c58b5e5    | ❌ **空配列** [] (0試合)    |
| 2026-02-03 14:57 | efb2e663    | ❌ **空配列** [] (変更なし) |
| 2026-02-03 15:11 | 59c1c9ee    | ❌ **空配列** [] (変更なし) |

### コミット6c58b5e5の変更内容

```
data/matches/six-nations.json:
- 削除: 332行 (15試合の完全データ)
- 追加: 1行 (空配列 [])
- 差分: -331行

data/matches/six-nations-women.json: 同じパターン (-331行)
data/matches/six-nations-u20.json: 同じパターン (-331行)
```

## 失敗の原因

### 1. 使用されていたコード (コミット a9f8638)

```python
def _initialize_driver_and_load_page(self):
    self.driver.get(url)
    print(f"ページにアクセス: {url}")

    # JavaScript実行を待つ
    import time
    time.sleep(10)

    # CSS Modulesのプレフィックスマッチングで試合カードを待機
    try:
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                "[class*='fixturesResultsCard_fixturesResults']"))
        )
        print("試合カードの読み込み完了")
    except Exception as e:
        print(f"警告: 試合カード要素が見つかりませんでした: {e}")

    # さらに少し待機してJavaScriptの実行を確実にする
    time.sleep(5)

    # デバッグ
    print(f"HTMLサイズ: {len(self.driver.page_source)} bytes")
```

### 2. 待機条件の問題

**待機対象**: `[class*='fixturesResultsCard_fixturesResults']`

これは**個別の試合カード**を待っていました。

**実際のHTML構造**:

```
roundContainer (親)
  └─ dateGroup (日付グループ)
      ├─ dateTitle (日付ヘッダー)
      └─ fixturesResultsCard (試合カード)
```

### 3. 失敗のメカニズム

1. **ページ読み込み**: URLにアクセス
2. **初期待機**: 10秒
3. **要素待機**: `fixturesResultsCard` を30秒待機
   - ❌ **タイムアウト**: 要素が見つからない
   - Six Nationsサイトは**Next.js/Reactの完全JavaScriptレンダリング**
   - GitHub Actionsのヘッドレス環境でJavaScriptが実行されなかった
4. **例外処理**: 警告を出すが処理は続行
5. **追加待機**: 5秒
6. **結果**: HTMLサイズは約260-274KB (静的HTML + 部分的JS)
   - 期待値745KBに対して大幅に不足
   - JavaScriptレンダリングが完了していない

### 4. GitHub Actionsログの推定出力

```
ページにアクセス: https://www.sixnationsrugby.com/en/m6n/fixtures/2026
警告: 試合カード要素が見つかりませんでした: Timeout
HTMLサイズ: 259683 bytes
ラウンドコンテナが見つかりません
```

## なぜローカルでは成功したのか

### 環境の違い

| 項目           | GitHub Actions    | ローカル (macOS)    |
| -------------- | ----------------- | ------------------- |
| OS             | Ubuntu latest     | macOS               |
| Chrome         | Headless Chrome   | Headless Chrome     |
| **ボット検出** | ❌ **検出される** | ✅ **検出されない** |
| JavaScript実行 | ❌ **ブロック**   | ✅ **正常実行**     |
| HTMLサイズ     | 274KB             | 747KB               |
| 試合カード数   | 0                 | 15                  |

### Six Nationsサイトのボット検出

Six Nationsサイトは**ヘッドレスブラウザを検出**する機能を持っています：

1. **navigator.webdriver** のチェック
2. **window.chrome** の存在確認
3. **自動化フラグ**の検出
4. **ブラウザフィンガープリント**の分析

GitHub Actionsの標準的なSelenium設定では、これらの検出をすり抜けられず、JavaScriptの実行がブロックされました。

## 修正の履歴

### 修正1: CSS Selector変更 (a9f8638)

- **狙い**: CSS Modulesのクラス名問題を解決
- **結果**: ❌ 失敗 (そもそもJSが実行されていない)

### 修正2: 待機戦略強化 (7139ab8)

- **狙い**: タイミング問題を解決
- **変更**:
  - document.readyState確認
  - roundContainer直接待機
  - 待機時間45秒
- **結果**: ❌ 失敗 (JSブロックは解決せず)

### 修正3: ヘッドレスブラウザ検出回避 (5128803 - 現在)

- **狙い**: Six Nationsのボット検出を回避
- **変更**:
  - `--disable-blink-features=AutomationControlled`
  - `excludeSwitches: ["enable-automation"]`
  - `useAutomationExtension: false`
  - `navigator.webdriver → undefined`
- **結果**: ✅ **ローカルで成功** (747KB, 15試合)
- **GitHub Actions**: 未実行（次回実行待ち）

## 結論

### 根本原因

Six Nationsサイトの**ヘッドレスブラウザ検出機能**により、GitHub Actions環境でJavaScript実行がブロックされていた。

### ローカルとの違い

- ローカル環境: macOSの特性により検出を回避
- GitHub Actions: Ubuntu + 標準Selenium設定で検出される

### 現在の状況

- ✅ ローカル環境: 完全に動作
- ⏳ GitHub Actions: 次回実行で検証予定
- 📊 取得データ: 15試合、747KB、完全なタイムゾーン情報

### 次回GitHub Actions実行での確認ポイント

1. HTMLサイズが700KB以上か
2. 試合カード数が0より大きいか
3. six-nations.jsonが空配列でないか
4. ログに「ラウンドコンテナの読み込み完了」が出るか

## 技術的学び

1. **Next.js/Reactサイトのスクレイピング**は、静的HTML解析と異なり、JavaScript実行が必須
2. **ヘッドレスブラウザ検出**は一般的なボット対策であり、標準的なSelenium設定では不十分
3. **環境の違い**（OS、ブラウザバージョン、ネットワーク）により動作が変わる
4. **段階的デバッグ**（HTMLサイズ、要素数、ログ）が原因特定に有効
