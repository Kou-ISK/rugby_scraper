# スポンサー名自動除去機能

## 概要

スクレイピング時に自動的にチーム名からスポンサー名を除去し、常にベースチーム名のみを保存する機能。

## 実装内容

### 1. 動的スポンサー検知

**既存チーム名をベースにスポンサーを自動検出**

- teams.jsonに登録されているチーム名をキャッシュ化
- 新しいチーム名が「既存チーム名 + スポンサー」パターンに一致するか自動判定
- 例: teams.jsonに "CHIEFS" があれば、"CHIEFS GIO", "CHIEFS NEWCO" などを自動的に "CHIEFS" に変換

**メリット:**

- 新しいスポンサーが登場しても自動対応
- SPONSOR_PATTERNSの更新不要
- 保守性が大幅に向上

### 2. 国際試合の特別扱い

**同名チームの統一**

- Six Nations, Rugby Championship, World Rugby Internationals等の国際大会では、同名チームを同一視
- 例: w6n の "England" と wri の "England" は同じチーム名に正規化される
- チームIDは各大会で独立（w6n-1, wri-6 など）

**代表チームバリエーションの保持**

- "England A", "Italy XV", "Scotland A" などは正式な代表チームと別扱い
- Barbarians, U20なども同様に保持

### 3. BaseScraper拡張

- `INTERNATIONAL_COMPETITIONS`: 国際試合の大会IDセット
- `SPONSOR_PATTERNS`: 静的スポンサー名パターン（フォールバック用）
- `_base_team_names`: 既存チーム名キャッシュ（大会別）
- `_build_base_team_names_cache()`: キャッシュ構築
- `_is_national_team_variant()`: 代表チームバリエーション判定
- `_normalize_team_name()`: 動的スポンサー検知 + 国際試合対応
- `_resolve_team_id()`: チームID解決（大会別）
- `save_to_json()`: 保存時に自動正規化

### 4. 対応スポンサー名（静的パターン）

#### 先頭スポンサー

- DHL, ISUZU, GALLAGHER, Hollywoodbets, Vodacom

#### 末尾スポンサー

- GIO, HBF, FMG, SKY, DHL, ISUZU, GALLAGHER
- 4R / FOUR R, CHURCHILL, MCLEAN, HIF, HFC BANK

### 5. 使用例

```python
from scraper.six_nations import SixNationsScraper

scraper = SixNationsScraper()

# スクレイピング時、以下のような変換が自動実行される：

# 【動的スポンサー検知】
# teams.jsonに "CHIEFS" が登録されている場合:
# "CHIEFS GIO" → "CHIEFS"
# "CHIEFS NEWCO" → "CHIEFS"  # 未知のスポンサーでも自動検知
# "HIGHLANDERS ANY SPONSOR" → "HIGHLANDERS"

# 【国際試合の同名チーム統一】
# w6n: "England" → "England"
# wri: "England" → "England"  # 同じチーム名に統一
# チームIDは別: w6n-1, wri-6

# 【代表チームバリエーション保持】
# "England A" → "England A"  # A代表は別チーム扱い
# "Italy XV" → "Italy XV"    # XV代表も別チーム扱い

matches = scraper.scrape()
```

### 6. 動作確認

```bash
# 動的スポンサー検知と国際試合対応のテスト
python3 scripts/test_dynamic_sponsor_detection.py
```

## メリット

1. **動的対応**: 新しいスポンサーが登場しても自動検知（パターン更新不要）
2. **重複防止**: teams.jsonに同一チームが複数登録されない
3. **ID安定性**: 既存チームIDが変わらない
4. **国際試合統一**: 同名の代表チームは自動的に統一される
5. **自動化**: 手動でのチーム名統合作業が不要
6. **保守性**: teams.jsonの既存データをベースに動作

## 国際試合対応の詳細

### 国際大会の定義

以下の大会が国際試合として扱われます:

- `m6n`: Six Nations (Men)
- `w6n`: Six Nations (Women)
- `u6n`: Six Nations U20
- `trc`: The Rugby Championship
- `ans`: Autumn Nations Series
- `wri`: World Rugby Internationals

### 同名チームの扱い

**正式な代表チーム:**

- "England", "France", "Japan" など
- 全ての国際大会で同じチーム名に正規化される
- 各大会で独立したチームIDを持つ（例: w6n-1, wri-6）

**派生チーム（別チーム扱い）:**

- "England A", "Scotland A" → A代表
- "Italy XV", "Ireland XV" → XV代表
- "Barbarians", "Barbarians Women" → バーバリアンズ
- これらは正式な代表チームとは別のチームとして保持

## 既存データへの影響

- 既存の試合データ内のチーム名は`scripts/merge_duplicate_teams.py`で統合済み
- 今後の新規スクレイピングでは自動的にベースチーム名のみ保存される
- チームマスタ（teams.json）のIDは変更されない

## 更新履歴

- 2026-02-06: 初回実装（Super Rugby Pacific対応）
- 2026-02-06: 動的スポンサー検知と国際試合対応を追加
