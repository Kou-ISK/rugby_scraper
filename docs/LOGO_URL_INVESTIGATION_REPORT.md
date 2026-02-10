# 公式ソースからのロゴURL取得調査レポート

調査日: 2026年2月8日

## エグゼクティブサマリー

各大会の公式サイトから、チームロゴURLを取得できることを確認しました。RugbyViz API（GP/URC）とTop 14は、CDNから配信される高品質なロゴ画像を提供しており、実装が容易です。Six Nationsは専用のContentful CDNを使用しています。

---

## 1. RugbyViz API（Gallagher Premiership, URC）

### エンドポイント

- **ベースURL**: `https://rugby-union-feeds.incrowdsports.com`
- **試合データ**: `/v1/matches` (既存実装で使用中)
- **チームデータ**: `/v1/teams` (推測 - 未検証、要認証ヘッダー)

### チーム情報の取得方法

現在のスクレイパー実装では、`/v1/matches` エンドポイントから試合データを取得していますが、レスポンスにはチーム情報が含まれていません。しかし、**公式Webサイト**（`https://www.premiershiprugby.com/fixtures-results/`）のHTMLには、チームロゴURLが埋め込まれています。

### ロゴURLフィールド

公式サイトのHTMLから抽出できるロゴURL例：

```
https://media-cdn.incrowdsports.com/f4d9a293-9086-41bf-aa1b-c98d1c62fe3b.png?format=webp&width=320
https://media-cdn.cortextech.io/17733469-fa47-4bee-bb7e-2e8c36a26e8b.png?format=webp&width=320
```

**CDN**: `media-cdn.incrowdsports.com` および `media-cdn.cortextech.io`

### サンプルレスポンス (Webページから抽出)

```html
<img
  alt="Bath Rugby"
  src="https://media-cdn.incrowdsports.com/f4d9a293-9086-41bf-aa1b-c98d1c62fe3b.png?format=webp&width=320"
/>
<img
  alt="Saracens"
  src="https://media-cdn.cortextech.io/17733469-fa47-4bee-bb7e-2e8c36a26e8b.png?format=webp&width=320"
/>
<img
  alt="Bristol Bears"
  src="https://media-cdn.incrowdsports.com/714ab764-0396-4c96-80df-4013a723d172.png?format=webp&width=320"
/>
```

### 実装状況

- ✅ `/v1/matches` エンドポイントを使用して試合データを取得（[rugbyviz.py](../src/collectors/european/rugbyviz.py)）
- ❌ チームロゴURLの取得は未実装
- ⚠️ ロゴURLはWebページのHTMLに埋め込まれているが、API認証が必要なため直接的なチームエンドポイントアクセスは未確認

---

## 2. Six Nations

### 公式サイト

- **URL**: `https://www.sixnationsrugby.com/en/m6n/fixtures/`
- **データソース**: Contentful CMS (Stadion.io proxy経由)

### ロゴURL取得方法

Six Nations公式サイトでは、各国のロゴURLが**Contentful CDN**経由で配信されています。

```
https://contentfulproxy.stadion.io/uiu4umqyl5b5/4CehwFgG4EaTucC1mpUMJf/9e5ca4684da6d74df8fd0dc353170965/Ireland.png?fm=webp&fit=pad&f=center&w=160&h=160&q=100
```

**国別ロゴURL例**:

- England: `https://contentfulproxy.stadion.io/uiu4umqyl5b5/4etLl8n9qTU6ANndtkdKzK/34be66d8edd37e28bff9ca59e177a6d3/England.png?fm=webp&fit=pad&f=center&w=160&h=160&q=100`
- France: `https://contentfulproxy.stadion.io/uiu4umqyl5b5/1WsL0VK10CEmbAGIswsO83/c25b9d4055d149be15a2149085ed4767/France.png?fm=webp&fit=pad&f=center&w=160&h=160&q=100`
- Ireland: `https://contentfulproxy.stadion.io/uiu4umqyl5b5/4CehwFgG4EaTucC1mpUMJf/9e5ca4684da6d74df8fd0dc353170965/Ireland.png?fm=webp&fit=pad&f=center&w=160&h=160&q=100`
- Italy: `https://contentfulproxy.stadion.io/uiu4umqyl5b5/4H5riEnkPSH1bfTtuUPlm6/2e4f7f6426b4fff1403c3574412f9906/Italy.png?fm=webp&fit=pad&f=center&w=160&h=160&q=100`
- Scotland: `https://contentfulproxy.stadion.io/uiu4umqyl5b5/5dFjvz9hlMLZuErj8WaedF/77358159a12301fede9e140f394c31d5/Scotland.png?fm=webp&fit=pad&f=center&w=160&h=160&q=100`
- Wales: `https://contentfulproxy.stadion.io/uiu4umqyl5b5/k15AFgATkLWZSUSfTdiFj/fb934604e70f18954c30ff957948e206/Wales.png?fm=webp&fit=pad&f=center&w=160&h=160&q=100`

### 実装状況

- ✅ Seleniumを使用してページをレンダリング（[six_nations.py](../src/collectors/international/six_nations.py)）
- ❌ チームロゴURLの取得は未実装
- 💡 既存のSeleniumドライバーで、ロゴURLをHTMLから抽出可能

### 実装推奨アプローチ

1. `_extract_matches()` メソッド内で、試合カード要素からチームロゴURLを抽出
2. `<img>` タグの `src` 属性を取得（`soup.find('img', alt=team_name)`）
3. チーム名とロゴURLのマッピング辞書を作成し、`teams.json` に反映

---

## 3. League One（日本リーグワン）

### 公式サイト

- **URL**: `https://league-one.jp/schedule/`

### ロゴURL取得方法

⚠️ **調査不可**: League Oneサイトはリダイレクト保護（Doubleclick広告トラッキング）があり、`fetch_webpage` ツールでは内容を取得できませんでした。

### 実装状況

- ✅ BeautifulSoupでHTMLを解析（[league_one_divisions.py](../src/collectors/domestic/league_one_divisions.py)）
- ❌ チームロゴURLの取得は未実装
- ⚠️ 手動ブラウザ確認が必要

### 実装推奨アプローチ

1. 実際のHTMLソースを手動で確認
2. チームロゴが `<img>` タグで提供されている場合は抽出可能
3. CDNパターンを特定して、`_extract_matches()` メソッドに追加

---

## 4. EPCR（Champions Cup, Challenge Cup）

### 公式サイト

- **URL**: `https://www.epcrugby.com/champions-cup/matches`
- **URL**: `https://www.epcrugby.com/challenge-cup/matches`

### ロゴURL取得方法

現在の実装ではSeleniumを使用していますが、HTMLからロゴURLを抽出するロジックは未実装です。EPCRサイトのソースコードを確認する必要があります。

### 実装状況

- ✅ Seleniumでページを取得（[epcr.py](../src/collectors/european/epcr.py)）
- ❌ チームロゴURLの取得は未実装
- 💡 `_extract_matches()` メソッドで、チーム名のみ抽出中

### 実装推奨アプローチ

1. BeautifulSoupで試合カード内の `<img>` タグを探索
2. チーム名とロゴURLを紐付け
3. `teams.json` に反映

---

## 5. Top 14

### 公式サイト

- **URL**: `https://top14.lnr.fr/calendrier-et-resultats`

### ロゴURL取得方法

Top 14公式サイトでは、各クラブのロゴが**LNR CDN**から配信されています。

```
https://cdn.lnr.fr/club/{club-slug}/photo/logo-thumbnail-2x.{hash}.webp
```

**クラブ別ロゴURL例**:

- ASM Clermont: `https://cdn.lnr.fr/club/clermont/photo/logo-thumbnail-2x.9b691fc28a2bcf36d2324c361632900433fe9c97`
- Castres Olympique: `https://cdn.lnr.fr/club/castres/photo/logo-thumbnail-2x.ad3367d5839569c9a98bd9795e6e6aa8843d72a1`
- Racing 92: `https://cdn.lnr.fr/club/racing-92/photo/logo-thumbnail-2x.b6dd7d05b33fb251839480bae3856e38031cc740`
- Stade Toulousain: `https://cdn.lnr.fr/club/toulouse/photo/logo-thumbnail-2x.5c6d7eebbc76deac4dfe34cc3ce8bc7a1459bd96`
- Union Bordeaux-Bègles: `https://cdn.lnr.fr/club/bordeaux-begles/photo/logo-thumbnail-2x.f3cfc037a8f5948055f49befe64ab0a12bec1429`

### 実装状況

- ✅ Seleniumでページを取得（[top14.py](../src/collectors/european/top14.py)）
- ❌ チームロゴURLの取得は未実装
- 💡 HTMLから `<img>` タグを抽出可能

### 実装推奨アプローチ

1. `_extract_matches()` メソッド内で、試合カード要素からロゴURLを抽出
2. BeautifulSoupで `soup.select('img[src*="cdn.lnr.fr/club"]')` を使用
3. チーム名とロゴURLのマッピング辞書を作成

---

## 実装推奨アプローチ（全体）

### 1. 即座に実装可能な大会

以下の大会は、**既存のスクレイパーコード**に少しの修正を加えるだけでロゴURLを取得できます：

| 大会                      | CDN                                                      | 実装難易度 | 推奨優先度 |
| ------------------------- | -------------------------------------------------------- | ---------- | ---------- |
| **Gallagher Premiership** | `media-cdn.incrowdsports.com`, `media-cdn.cortextech.io` | ⭐ 低      | 🔥 高      |
| **URC**                   | 同上                                                     | ⭐ 低      | 🔥 高      |
| **Top 14**                | `cdn.lnr.fr`                                             | ⭐ 低      | 🔥 高      |
| **Six Nations**           | `contentfulproxy.stadion.io`                             | ⭐⭐ 中    | 🔥 高      |
| **EPCR**                  | 未確認                                                   | ⭐⭐ 中    | 🔶 中      |
| **League One**            | 未確認                                                   | ⭐⭐⭐ 高  | 🔶 中      |

### 2. 実装ステップ（RugbyViz例）

#### Step 1: Seleniumでページをレンダリング（既存）

RugbyVizスクレイパーは現在APIベースですが、ロゴURLはWebページからのみ取得可能です。以下の2つのアプローチがあります：

**アプローチA**: 公式ページをSeleniumで取得（推奨）

```python
# rugbyviz.pyに追加
def _fetch_team_logos_from_webpage(self):
    """公式サイトからチームロゴURLを取得"""
    driver = self._setup_driver()
    driver.get(self.config_url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    team_logos = {}

    # チームロゴ画像を全て取得
    for img in soup.find_all('img', alt=True):
        team_name = img.get('alt')
        logo_url = img.get('src')

        # チームロゴのみフィルタリング
        if logo_url and ('media-cdn.incrowdsports.com' in logo_url or
                         'media-cdn.cortextech.io' in logo_url):
            # クエリパラメータを除去（高解像度版）
            clean_url = logo_url.split('?')[0]
            team_logos[team_name] = clean_url

    driver.quit()
    return team_logos
```

**アプローチB**: APIから直接取得（要調査）

`/v1/teams` エンドポイントが存在する可能性がありますが、認証ヘッダー（X-API-KEY等）が必要です。現在の実装では未確認のため、**アプローチA（Webスクレイピング）を推奨**します。

#### Step 2: teams.jsonに反映

```python
# 取得したロゴURLをチームマスターに登録
for team_name, logo_url in team_logos.items():
    team_id = self._resolve_team_id(team_name, self.competition_slug)
    if team_id in self._team_master:
        self._team_master[team_id]['logo_url'] = logo_url

# ファイル保存
self._save_team_master()
```

### 3. Top 14の実装例

```python
# top14.py の _extract_matches() に追加
def _extract_matches(self, soup):
    matches = []
    team_logos = {}  # チームロゴURLキャッシュ

    calendar_inner = soup.find('div', class_='calendar-results__inner')
    if not calendar_inner:
        return matches

    # チームロゴを全て取得
    for img in soup.select('img[src*="cdn.lnr.fr/club"]'):
        team_name = img.get('alt', '')
        logo_url = img.get('src', '')
        if team_name and logo_url:
            team_logos[team_name] = logo_url

    # 後で teams.json に反映
    for team_name, logo_url in team_logos.items():
        team_id = self._resolve_team_id(team_name, "t14")
        if team_id in self._team_master:
            self._team_master[team_id]['logo_url'] = logo_url

    # 既存の試合データ抽出処理...
    # ...
```

### 4. Six Nationsの実装例

```python
# six_nations.py の _extract_matches() に追加
def _extract_matches(self, soup):
    matches = []
    team_logos = {}

    # ContentfulプロキシのロゴURLを全て取得
    for img in soup.find_all('img', src=lambda s: s and 'contentfulproxy.stadion.io' in s):
        team_name = img.get('alt', '')
        logo_url = img.get('src', '')
        if team_name and logo_url:
            team_logos[team_name] = logo_url

    # teams.jsonに反映
    for team_name, logo_url in team_logos.items():
        team_id = self._resolve_team_id(team_name, self._competition_id)
        if team_id in self._team_master:
            self._team_master[team_id]['logo_url'] = logo_url

    # 既存の試合データ抽出処理...
    # ...
```

---

## 現在のロゴURL管理方式（TheSportsDB API）

### 既存実装

- **ソース**: TheSportsDB API (`https://www.thesportsdb.com/api/v1/json/3/searchteams.php`)
- **キャッシュ**: `data/team_logos_cache.json`
- **ワークフロー**:
  1. スクレイピング時はロゴURL空で登録
  2. `python -m src.main update-logos` で一括取得
- **問題点**:
  - チーム名の完全一致が必要（"Bath Rugby" vs "Bath"）
  - 国際チームは取得可能だが、クラブチームの精度が低い
  - API Rate Limit（1秒1リクエスト）

### 公式ソース vs TheSportsDB

| 項目             | 公式ソース            | TheSportsDB             |
| ---------------- | --------------------- | ----------------------- |
| **精度**         | ⭐⭐⭐⭐⭐ 完璧       | ⭐⭐⭐ 良好             |
| **カバレッジ**   | ⭐⭐⭐⭐ 高（大会内） | ⭐⭐⭐⭐⭐ 高（世界中） |
| **メンテナンス** | ⭐⭐⭐⭐⭐ 不要       | ⭐⭐ 要（チーム名変更） |
| **実装難易度**   | ⭐⭐ 中               | ⭐ 低                   |
| **API制限**      | ⭐⭐⭐⭐⭐ なし       | ⭐⭐⭐ あり             |

---

## 推奨実装計画

### フェーズ1: 高優先度大会（即実装可能）

1. **Gallagher Premiership** - RugbyViz Webスクレイピング
2. **URC** - RugbyViz Webスクレイピング
3. **Top 14** - LNR CDNから取得

### フェーズ2: 中優先度大会

4. **Six Nations** - Contentful CDNから取得
5. **EPCR** - HTML調査後に実装

### フェーズ3: 調査が必要な大会

6. **League One** - サイト構造調査
7. **その他国際大会** - TheSportsDB APIで補完

---

## 補足: ロゴURL取得のベストプラクティス

### 1. URLクリーニング

クエリパラメータ（`?format=webp&width=320`）を除去して、元のURLを保存：

```python
logo_url = "https://media-cdn.incrowdsports.com/f4d9a293-9086-41bf-aa1b-c98d1c62fe3b.png?format=webp&width=320"
clean_url = logo_url.split('?')[0]
# -> "https://media-cdn.incrowdsports.com/f4d9a293-9086-41bf-aa1b-c98d1c62fe3b.png"
```

### 2. キャッシュ戦略

- 初回スクレイピング時にロゴURLを取得
- `teams.json` に永続化
- 再スクレイピング時は既存のロゴURLを保持（上書きしない）

### 3. フォールバック戦略

```python
# 優先順位: 公式ソース > キャッシュ > TheSportsDB
if official_logo_url:
    team_logo = official_logo_url
elif team_id in logo_cache:
    team_logo = logo_cache[team_id]
else:
    team_logo = fetch_from_thesportsdb(team_name)
```

---

## 結論

**✅ 実装可能**: 各大会の公式ソースからチームロゴURLを取得できることを確認しました。

**推奨アプローチ**:

1. **即座に実装**: Gallagher Premiership, URC, Top 14（優先度: 高）
2. **短期実装**: Six Nations, EPCR（優先度: 中）
3. **調査後に実装**: League One（優先度: 中）

**技術的課題**:

- RugbyViz APIは認証が必要なため、チームエンドポイントへの直接アクセスは未確認
- 代替手段として、公式Webページからのスクレイピングを推奨
- League Oneサイトはリダイレクト保護があり、手動確認が必要

**次のステップ**:

1. 各スクレイパーに `_extract_team_logos()` メソッドを追加
2. `teams.json` にロゴURL反映ロジックを実装
3. テスト実行とデバッグ
