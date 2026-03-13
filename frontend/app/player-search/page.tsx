'use client';

import { FormEvent, useState } from 'react';
import useSWR from 'swr';

import { EmptyState } from '@/components/EmptyState';
import { LoadingState } from '@/components/LoadingState';
import { RequireAuth } from '@/components/RequireAuth';
import { api } from '@/lib/api';
import { formatRelativeDate } from '@/lib/utils';

function PlayerSearchContent() {
  const [draftQuery, setDraftQuery] = useState('Scann');
  const [query, setQuery] = useState('Scann');

  const { data, error, isLoading } = useSWR(query ? ['player-search', query] : null, () => api.searchPlayerProfiles(query), {
    revalidateOnFocus: false,
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setQuery(draftQuery.trim());
  };

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg">
        <p className="text-xs uppercase tracking-[0.35em] text-violet-300">Community Search</p>
        <h2 className="mt-3 text-3xl font-semibold text-white">Player Search</h2>
        <p className="mt-3 max-w-3xl text-sm text-slate-400">Query MLB The Show universal profiles and cache the profile stats StubIQ can use later for account-aware features.</p>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-3 sm:flex-row">
          <input
            value={draftQuery}
            onChange={(event) => setDraftQuery(event.target.value)}
            placeholder="Search username"
            className="flex-1 rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-sky-400"
          />
          <button type="submit" className="rounded-2xl bg-sky-500 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-400">
            Search
          </button>
        </form>
      </section>

      {isLoading && !data ? <LoadingState label="Searching player profiles..." /> : null}

      {data?.items.length ? (
        <div className="grid gap-4 xl:grid-cols-2">
          {data.items.map((profile) => {
            const currentSeason = profile.online_data_json[0] as Record<string, unknown> | undefined;
            const ddTime = profile.most_played_modes_json.dd_time;
            return (
              <article key={profile.username} className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-xl font-semibold text-white">{profile.username}</h3>
                    <p className="mt-1 text-sm text-slate-400">Level {profile.display_level ?? 'Unknown'} • {profile.games_played ?? 0} games played</p>
                  </div>
                  <div className="rounded-2xl border border-slate-800 bg-slate-950/70 px-3 py-2 text-xs text-slate-400">
                    Synced {formatRelativeDate(profile.last_synced_at)}
                  </div>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
                    <div className="text-xs uppercase tracking-[0.25em] text-slate-500">Most Played</div>
                    <div className="mt-2 text-lg font-semibold text-white">Diamond Dynasty</div>
                    <div className="mt-1 text-sm text-slate-400">DD time: {String(ddTime ?? '0')}</div>
                  </div>
                  <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
                    <div className="text-xs uppercase tracking-[0.25em] text-slate-500">Current Online</div>
                    <div className="mt-2 text-lg font-semibold text-white">{String(currentSeason?.year ?? '—')}</div>
                    <div className="mt-1 text-sm text-slate-400">Wins: {String(currentSeason?.wins ?? '0')} • BA: {String(currentSeason?.batting_average ?? '—')}</div>
                  </div>
                </div>

                <div className="mt-5 grid gap-3 text-sm text-slate-300 sm:grid-cols-2">
                  <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
                    <div className="font-medium text-white">Lifetime hitting</div>
                    <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-xs text-slate-400">{JSON.stringify(profile.lifetime_hitting_stats_json, null, 2)}</pre>
                  </div>
                  <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
                    <div className="font-medium text-white">Lifetime defensive</div>
                    <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-xs text-slate-400">{JSON.stringify(profile.lifetime_defensive_stats_json, null, 2)}</pre>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      ) : null}

      {!isLoading && !error && query && !data?.items.length ? (
        <EmptyState title="No profiles found" description="Try a different MLB The Show username or refresh the search." />
      ) : null}

      {error ? <EmptyState title="Search failed" description="The backend could not query the MLB The Show player-search endpoint." /> : null}
    </div>
  );
}

export default function PlayerSearchPage() {
  return (
    <RequireAuth>
      <PlayerSearchContent />
    </RequireAuth>
  );
}
