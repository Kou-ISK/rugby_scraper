# TypeScript 型定義の使い方

`rugby_scraper` の JSON 仕様に合わせた型定義は `types/rugby-scraper.d.ts` にあります。

## 1. 取り込み方法

### 方法A: プロジェクトにコピーして利用（推奨）

1. `types/rugby-scraper.d.ts` を自分のプロジェクトに配置
2. `tsconfig.json` の `include` に含める

```json
{
  "compilerOptions": {
    "strict": true
  },
  "include": ["src", "types"]
}
```

### 方法B: そのまま相対パスで import

```ts
import type {
  Match,
  Matches,
  Competition,
  Competitions,
  CompetitionId,
  MatchesUrl,
  TeamsUrl,
  CompetitionsUrl,
} from './types/rugby-scraper';
```

## 2. 代表的な型

- `Match` / `Matches`: 試合データ
- `Team` / `Teams`: チームマスタ
- `Competition` / `Competitions`: 大会メタデータ
- `CompetitionId`: 有効な大会IDのユニオン
- `MatchesUrl` / `TeamsUrl` / `CompetitionsUrl`: Raw URL の型ヘルパー

## 3. 取得例

```ts
import type { Matches, Competitions, CompetitionId, MatchesUrl } from './types/rugby-scraper';

async function fetchCompetitions(): Promise<Competitions> {
  const url = 'https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/competitions.json';
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch competitions');
  return res.json();
}

async function fetchMatches(id: CompetitionId, season: string): Promise<Matches> {
  const url: MatchesUrl<CompetitionId> =
    `https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/${id}/${season}.json`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch matches');
  return res.json();
}
```

## 4. 取り扱いの注意

- `kickoff` はオフセット付きISO8601、`timezone` は IANA 形式
- `home_team_id` / `away_team_id` は未確定の場合空文字列
- `broadcasters` は常に配列（空配列の場合あり）
- `data_paths` はディレクトリパスの場合がある（`{comp_id}/{season}.json` を選択する）

## 5. 関連ドキュメント

- JSON仕様: `docs/JSON_SCHEMA.md`
- 使用例: `docs/USAGE_EXAMPLES.md`
