# itsuneru での使用例

このドキュメントは、itsuneru プロジェクトで rugby_scraper のデータを取得・利用する際の実装例を示します。

## 1. TypeScript 型定義のインポート

```typescript
// types/rugby-scraper.d.ts をプロジェクトにコピーするか、
// 以下のようにインポート

import type {
  Match,
  Matches,
  Competition,
  Competitions,
  CompetitionId,
} from './types/rugby-scraper';
```

## 2. データ取得関数

### 2.1 大会メタデータ取得

```typescript
/**
 * 全大会のメタデータを取得
 */
async function fetchCompetitions(): Promise<Competitions> {
  const url =
    'https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/competitions.json';

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch competitions: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 特定の大会メタデータを取得
 */
async function fetchCompetition(
  id: CompetitionId,
): Promise<Competition | null> {
  const competitions = await fetchCompetitions();
  return competitions.find((c) => c.id === id) || null;
}
```

### 2.2 試合データ取得

```typescript
/**
 * 特定大会の試合データを取得
 */
async function fetchMatches(
  competitionId: CompetitionId,
  season: string,
): Promise<Matches> {
  const url = `https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/${competitionId}/${season}.json`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(
      `Failed to fetch matches for ${competitionId}: ${response.statusText}`,
    );
  }

  return response.json();
}

/**
 * 複数大会の試合データを一括取得
 */
async function fetchMultipleMatches(
  competitionIds: CompetitionId[],
  season: string,
): Promise<Record<CompetitionId, Matches>> {
  const results = await Promise.allSettled(
    competitionIds.map(async (id) => ({
      id,
      matches: await fetchMatches(id, season),
    })),
  );

  return results.reduce(
    (acc, result) => {
      if (result.status === 'fulfilled') {
        acc[result.value.id] = result.value.matches;
      }
      return acc;
    },
    {} as Record<CompetitionId, Matches>,
  );
}
```

## 3. データ処理例

### 3.1 日本で視聴可能な大会を抽出

```typescript
async function getJapanBroadcastCompetitions(): Promise<Competition[]> {
  const competitions = await fetchCompetitions();

  return competitions.filter((competition) =>
    competition.coverage.broadcast_regions.some(
      (region) => region.region === 'JP',
    ),
  );
}
```

### 3.2 今後の試合を取得

```typescript
/**
 * 指定日以降の試合を取得
 */
function getUpcomingMatches(
  matches: Matches,
  fromDate: Date = new Date(),
): Matches {
  return matches.filter((match) => {
    const kickoffUtc = new Date(match.kickoff_utc);
    return kickoffUtc >= fromDate;
  });
}

/**
 * 全大会の今後の試合を取得
 */
async function getAllUpcomingMatches(): Promise<Map<string, Matches>> {
  const competitions = await fetchCompetitions();
  const result = new Map<string, Matches>();

  for (const competition of competitions) {
    if (competition.data_paths.length === 0) continue;

    try {
      // data_paths はディレクトリの場合が多いので、シーズンを明示する
      const season = '2026';
      const matches = await fetchMatches(
        competition.id as CompetitionId,
        season,
      );
      const upcoming = getUpcomingMatches(matches);

      if (upcoming.length > 0) {
        result.set(competition.name, upcoming);
      }
    } catch (error) {
      console.error(`Failed to fetch matches for ${competition.id}:`, error);
    }
  }

  return result;
}
```

### 3.3 タイムゾーン変換

```typescript
import { utcToZonedTime, format } from 'date-fns-tz';

/**
 * 試合時刻をユーザーのタイムゾーンに変換
 */
function convertMatchTime(
  match: Match,
  competition: Competition,
  userTimezone: string = 'Asia/Tokyo',
): string {
  // kickoff はオフセット付きISO8601なので Date でパース可能
  const matchDateUtc = new Date(match.kickoff);

  // ユーザーのタイムゾーンに変換
  const matchDateInUserTz = utcToZonedTime(matchDateUtc, userTimezone);

  return format(matchDateInUserTz, 'yyyy-MM-dd HH:mm:ss zzz', {
    timeZone: userTimezone,
  });
}
```

### 3.4 broadcasters の扱い

```typescript
/**
 * broadcasters は常に配列（空配列含む）
 */
function normalizeBroadcasters(broadcasters: string[]): string[] {
  return broadcasters;
}

/**
 * 試合データを正規化
 */
function normalizeMatch(match: Match): Match & { broadcasters: string[] } {
  return {
    ...match,
    broadcasters: normalizeBroadcasters(match.broadcasters),
  };
}
```

## 4. React コンポーネント例

### 4.1 大会リストコンポーネント

```tsx
import React, { useEffect, useState } from 'react';
import type { Competitions } from './types/rugby-scraper';

const CompetitionsList: React.FC = () => {
  const [competitions, setCompetitions] = useState<Competitions>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCompetitions()
      .then(setCompetitions)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>読み込み中...</div>;
  if (error) return <div>エラー: {error}</div>;

  return (
    <div>
      <h2>ラグビー大会一覧</h2>
      <ul>
        {competitions.map((comp) => (
          <li key={comp.id}>
            <h3>{comp.name}</h3>
            <p>地域: {comp.region}</p>
            <p>試合数: {comp.data_summary.match_count}</p>
            {comp.coverage.broadcast_regions.length > 0 && (
              <div>
                <strong>視聴方法:</strong>
                <ul>
                  {comp.coverage.broadcast_regions.map((br, idx) => (
                    <li key={idx}>
                      {br.region}: {br.providers.join(', ')}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};
```

### 4.2 試合スケジュールコンポーネント

```tsx
import React, { useEffect, useState } from 'react';
import type {
  Matches,
  Competition,
  CompetitionId,
} from './types/rugby-scraper';

interface MatchScheduleProps {
  competitionId: CompetitionId;
}

const MatchSchedule: React.FC<MatchScheduleProps> = ({ competitionId }) => {
  const [matches, setMatches] = useState<Matches>([]);
  const [competition, setCompetition] = useState<Competition | null>(null);
  const [loading, setLoading] = useState(true);
  const season = '2026';

  useEffect(() => {
    Promise.all([
      fetchMatches(competitionId, season),
      fetchCompetition(competitionId),
    ])
      .then(([matchesData, competitionData]) => {
        setMatches(matchesData);
        setCompetition(competitionData);
      })
      .finally(() => setLoading(false));
  }, [competitionId]);

  if (loading) return <div>読み込み中...</div>;
  if (!competition) return <div>大会が見つかりません</div>;

  const upcomingMatches = getUpcomingMatches(matches);

  return (
    <div>
      <h2>{competition.name} 試合スケジュール</h2>
      <p>タイムゾーン: {competition.timezone_default}</p>

      <table>
        <thead>
          <tr>
            <th>日時</th>
            <th>会場</th>
            <th>対戦カード</th>
            <th>放送</th>
          </tr>
        </thead>
        <tbody>
          {upcomingMatches.map((match, idx) => (
            <tr key={idx}>
              <td>{match.kickoff}</td>
              <td>{match.venue}</td>
              <td>
                {match.home_team} vs {match.away_team}
              </td>
              <td>
                {match.broadcasters.length > 0
                  ? match.broadcasters.join(', ')
                  : 'なし'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

## 5. キャッシング戦略

### 5.1 ローカルストレージキャッシュ

```typescript
const CACHE_DURATION = 1000 * 60 * 60; // 1時間

interface CachedData<T> {
  data: T;
  timestamp: number;
}

function getCachedData<T>(key: string): T | null {
  const cached = localStorage.getItem(key);
  if (!cached) return null;

  const { data, timestamp }: CachedData<T> = JSON.parse(cached);
  const age = Date.now() - timestamp;

  if (age > CACHE_DURATION) {
    localStorage.removeItem(key);
    return null;
  }

  return data;
}

function setCachedData<T>(key: string, data: T): void {
  const cacheData: CachedData<T> = {
    data,
    timestamp: Date.now(),
  };
  localStorage.setItem(key, JSON.stringify(cacheData));
}

async function fetchCompetitionsWithCache(): Promise<Competitions> {
  const cached = getCachedData<Competitions>('competitions');
  if (cached) return cached;

  const competitions = await fetchCompetitions();
  setCachedData('competitions', competitions);
  return competitions;
}
```

## 6. エラーハンドリング

```typescript
class RugbyScraperError extends Error {
  constructor(
    message: string,
    public readonly competitionId?: CompetitionId,
    public readonly originalError?: Error,
  ) {
    super(message);
    this.name = 'RugbyScraperError';
  }
}

async function safelyFetchMatches(
  competitionId: CompetitionId,
): Promise<Matches | null> {
  try {
    return await fetchMatches(competitionId, '2026');
  } catch (error) {
    console.error(
      new RugbyScraperError(
        `Failed to fetch matches for ${competitionId}`,
        competitionId,
        error as Error,
      ),
    );
    return null;
  }
}
```

## 7. テストコード例

```typescript
import { describe, it, expect } from 'vitest';

describe('Rugby Scraper API', () => {
  it('should fetch competitions', async () => {
    const competitions = await fetchCompetitions();

    expect(competitions).toBeInstanceOf(Array);
    expect(competitions.length).toBeGreaterThan(0);

    const firstComp = competitions[0];
    expect(firstComp).toHaveProperty('id');
    expect(firstComp).toHaveProperty('name');
    expect(firstComp).toHaveProperty('coverage');
  });

  it('should fetch League One matches', async () => {
    const matches = await fetchMatches('jrlo-div1', '2026');

    expect(matches).toBeInstanceOf(Array);

    if (matches.length > 0) {
      const firstMatch = matches[0];
      expect(firstMatch).toHaveProperty('kickoff');
      expect(firstMatch).toHaveProperty('venue');
      expect(firstMatch).toHaveProperty('home_team');
      expect(firstMatch).toHaveProperty('away_team');
    }
  });

  it('should handle invalid competition ID', async () => {
    await expect(
      fetchMatches('invalid-id' as CompetitionId, '2026'),
    ).rejects.toThrow();
  });
});
```

## 8. パフォーマンス最適化

### 8.1 並列読み込み

```typescript
async function preloadAllData(): Promise<{
  competitions: Competitions;
  matches: Record<CompetitionId, Matches>;
}> {
  // 大会メタデータを先に取得
  const competitions = await fetchCompetitions();

  // データが存在する大会のIDを抽出
  const competitionIds = competitions
    .filter((c) => c.data_paths.length > 0)
    .map((c) => c.id as CompetitionId);

  // 全試合データを並列取得
  const matches = await fetchMultipleMatches(competitionIds, '2026');

  return { competitions, matches };
}
```

### 8.2 遅延読み込み

```typescript
const useMatches = (competitionId: CompetitionId | null) => {
  const [matches, setMatches] = useState<Matches | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!competitionId) return;

    setLoading(true);
    fetchMatches(competitionId, '2026')
      .then(setMatches)
      .finally(() => setLoading(false));
  }, [competitionId]);

  return { matches, loading };
};
```

## 9. 注意事項

1. **タイムゾーン処理**: `kickoff` はオフセット付きISO8601、`timezone` は IANA 形式です
2. **broadcasters の型**: 常に `string[]`（空配列の場合あり）
3. **空データ**: `teams`, `seasons`, `data_paths` が空配列の場合があります
4. **キャッシング**: 頻繁なアクセスを避けるため、適切にキャッシュしてください
5. **エラー処理**: ネットワークエラーに備えて適切なエラーハンドリングを実装してください

## 10. サポート

問題が発生した場合:

- GitHub Issues: https://github.com/Kou-ISK/rugby_scraper/issues
- スキーマ仕様: [JSON_SCHEMA.md](../docs/JSON_SCHEMA.md)
