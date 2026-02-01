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
async function fetchMatches(competitionId: CompetitionId): Promise<Matches> {
  const url = `https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/matches/${competitionId}.json`;

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
): Promise<Record<CompetitionId, Matches>> {
  const results = await Promise.allSettled(
    competitionIds.map(async (id) => ({
      id,
      matches: await fetchMatches(id),
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
    const matchDate = new Date(match.date);
    return matchDate >= fromDate;
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
      const matches = await fetchMatches(competition.id as CompetitionId);
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
import { zonedTimeToUtc, utcToZonedTime, format } from 'date-fns-tz';

/**
 * 試合時刻をユーザーのタイムゾーンに変換
 */
function convertMatchTime(
  match: Match,
  competition: Competition,
  userTimezone: string = 'Asia/Tokyo',
): string {
  // 試合時刻を大会のタイムゾーンでパース
  const matchDateInCompetitionTz = zonedTimeToUtc(
    match.date,
    competition.timezone_default,
  );

  // ユーザーのタイムゾーンに変換
  const matchDateInUserTz = utcToZonedTime(
    matchDateInCompetitionTz,
    userTimezone,
  );

  return format(matchDateInUserTz, 'yyyy-MM-dd HH:mm:ss zzz', {
    timeZone: userTimezone,
  });
}
```

### 3.4 broadcasters の正規化

```typescript
/**
 * broadcasters を配列形式に正規化
 */
function normalizeBroadcasters(broadcasters: string[] | string): string[] {
  if (Array.isArray(broadcasters)) {
    return broadcasters;
  }
  if (broadcasters === '' || broadcasters === null) {
    return [];
  }
  return [broadcasters];
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

  useEffect(() => {
    Promise.all([fetchMatches(competitionId), fetchCompetition(competitionId)])
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
              <td>{match.date}</td>
              <td>{match.venue}</td>
              <td>
                {match.home_team} vs {match.away_team}
              </td>
              <td>
                {Array.isArray(match.broadcasters)
                  ? match.broadcasters.join(', ')
                  : match.broadcasters || 'なし'}
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
    return await fetchMatches(competitionId);
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
    const matches = await fetchMatches('league-one');

    expect(matches).toBeInstanceOf(Array);

    if (matches.length > 0) {
      const firstMatch = matches[0];
      expect(firstMatch).toHaveProperty('date');
      expect(firstMatch).toHaveProperty('venue');
      expect(firstMatch).toHaveProperty('home_team');
      expect(firstMatch).toHaveProperty('away_team');
    }
  });

  it('should handle invalid competition ID', async () => {
    await expect(fetchMatches('invalid-id' as CompetitionId)).rejects.toThrow();
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
  const matches = await fetchMultipleMatches(competitionIds);

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
    fetchMatches(competitionId)
      .then(setMatches)
      .finally(() => setLoading(false));
  }, [competitionId]);

  return { matches, loading };
};
```

## 9. 注意事項

1. **タイムゾーン処理**: 試合時刻は大会の `timezone_default` で解釈する必要があります
2. **broadcasters の型**: `string[]` または `string` の両方に対応してください
3. **空データ**: `teams`, `seasons`, `data_paths` が空配列の場合があります
4. **キャッシング**: 頻繁なアクセスを避けるため、適切にキャッシュしてください
5. **エラー処理**: ネットワークエラーに備えて適切なエラーハンドリングを実装してください

## 10. サポート

問題が発生した場合:

- GitHub Issues: https://github.com/Kou-ISK/rugby_scraper/issues
- スキーマ仕様: [JSON_SCHEMA.md](../docs/JSON_SCHEMA.md)
