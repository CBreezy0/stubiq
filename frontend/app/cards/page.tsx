'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import useSWR from 'swr';

import { ACCESS_TOKEN_STORAGE_KEY, API_BASE_URL } from '@/lib/api';

type CardSearchItem = {
  item_id: string;
  name: string;
  team?: string | null;
  series?: string | null;
  best_sell_price?: number | null;
};

type CardSearchResponse = {
  items: CardSearchItem[];
};

function formatStubs(value?: number | null) {
  if (value == null) return '—';
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value);
}

async function fetchCardSearch(query: string): Promise<CardSearchResponse> {
  const headers = new Headers({ Accept: 'application/json' });
  const accessToken = typeof window === 'undefined' ? null : window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);

  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}/cards/search?q=${encodeURIComponent(query)}`, {
    headers,
    cache: 'no-store',
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) message = payload.detail;
    } catch {
      const text = await response.text();
      if (text) message = text;
    }
    throw new Error(message);
  }

  return response.json() as Promise<CardSearchResponse>;
}

function CardsSearchContent() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q')?.trim() ?? '';
  const { data, error, isLoading } = useSWR(query ? ['card-search', query] : null, () => fetchCardSearch(query));

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg">
        <p className="text-xs uppercase tracking-[0.35em] text-sky-300">Card Search</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">Global Card Search</h1>
        <p className="mt-3 text-sm text-slate-400">
          {query ? `Results for “${query}”` : 'Use the sidebar search to look up cards by name, team, or series.'}
        </p>
      </section>

      {!query ? (
        <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 text-sm text-slate-400 shadow-lg">
          Enter a card query in the sidebar to search the global card index.
        </section>
      ) : null}

      {query && isLoading ? (
        <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 text-sm text-slate-400 shadow-lg">Searching cards…</section>
      ) : null}

      {query && error ? (
        <section className="rounded-3xl border border-rose-900/60 bg-rose-950/20 p-6 text-sm text-rose-200 shadow-lg">Card search is unavailable right now.</section>
      ) : null}

      {query && !isLoading && !error ? (
        <section className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/70 shadow-lg">
          <div className="border-b border-slate-800 px-5 py-4">
            <h2 className="text-lg font-semibold text-white">Search Results</h2>
          </div>
          {data?.items.length ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-950/50 text-left text-slate-400">
                  <tr>
                    <th className="px-5 py-3 font-medium">Name</th>
                    <th className="px-5 py-3 font-medium">Team</th>
                    <th className="px-5 py-3 font-medium">Series</th>
                    <th className="px-5 py-3 font-medium">Best Sell</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr key={item.item_id} className="border-t border-slate-800/80 text-slate-200">
                      <td className="px-5 py-4">
                        <Link href={`/cards/${item.item_id}`} className="font-medium text-white transition hover:text-sky-300">
                          {item.name}
                        </Link>
                      </td>
                      <td className="px-5 py-4">{item.team ?? '—'}</td>
                      <td className="px-5 py-4">{item.series ?? '—'}</td>
                      <td className="px-5 py-4">{formatStubs(item.best_sell_price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="px-5 py-6 text-sm text-slate-400">No cards matched your query.</div>
          )}
        </section>
      ) : null}
    </div>
  );
}


export default function CardsSearchPage() {
  return (
    <Suspense fallback={<div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 text-sm text-slate-400 shadow-lg">Loading card search…</div>}>
      <CardsSearchContent />
    </Suspense>
  );
}
