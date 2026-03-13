'use client';

import { useEffect, useMemo, useState } from 'react';
import useSWR from 'swr';

import { EmptyState } from '@/components/EmptyState';
import { FlipTable } from '@/components/FlipTable';
import { LoadingState } from '@/components/LoadingState';
import { MarketFiltersBar, MarketFilterState } from '@/components/MarketFiltersBar';
import { PaginationControls } from '@/components/PaginationControls';
import { RequireAuth } from '@/components/RequireAuth';
import { ACCESS_TOKEN_STORAGE_KEY, API_BASE_URL, api } from '@/lib/api';
import { formatPercent, formatStubs } from '@/lib/utils';

const PAGE_SIZE = 25;
type TopFlipsResponse = Awaited<ReturnType<(typeof api)['getFlips']>>;

function buildTopFlipsQuery(filters: MarketFilterState) {
  const params = new URLSearchParams();

  if (filters.minRoi) params.set('roi_min', filters.minRoi);
  if (filters.minProfit) params.set('profit_min', filters.minProfit);
  if (filters.minLiquidity) params.set('liquidity_min', filters.minLiquidity);
  if (filters.team.trim()) params.set('team', filters.team.trim());
  if (filters.series.trim()) params.set('series', filters.series.trim());
  if (filters.rarity !== 'Any') params.set('rarity', filters.rarity);
  params.set('sort_by', filters.sortBy);
  params.set('limit', '50');

  const query = params.toString();
  return query ? `?${query}` : '';
}

async function getTopFlips(query: string): Promise<TopFlipsResponse> {
  const headers = new Headers({ Accept: 'application/json' });
  const accessToken = typeof window === 'undefined' ? null : window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);

  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}/flips/top${query}`, {
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

  return response.json() as Promise<TopFlipsResponse>;
}
const defaultFilters: MarketFilterState = {
  rarity: 'Any',
  series: '',
  team: '',
  minProfit: '',
  minRoi: '',
  minLiquidity: '',
  sortBy: 'flip_score',
  sortOrder: 'desc',
};

function FlipsPageContent() {
  const [draftFilters, setDraftFilters] = useState<MarketFilterState>(defaultFilters);
  const [appliedFilters, setAppliedFilters] = useState<MarketFilterState>(defaultFilters);
  const [page, setPage] = useState(1);

  const query = useMemo(() => buildTopFlipsQuery(appliedFilters), [appliedFilters]);
  const { data, error, isLoading } = useSWR(['top-flips-page', query], () => getTopFlips(query), { refreshInterval: 30_000 });

  const items = data?.items ?? [];
  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE));

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  const visibleItems = items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const bestProfit = items.reduce<number | null>((best, item) => {
    const profit = item.profit_after_tax ?? null;
    if (profit == null) return best;
    return best == null ? profit : Math.max(best, profit);
  }, null);
  const bestRoi = items.reduce<number | null>((best, item) => {
    const roi = item.roi ?? null;
    if (roi == null) return best;
    return best == null ? roi : Math.max(best, roi);
  }, null);

  if (isLoading && !data) {
    return <LoadingState label="Scanning live flips..." />;
  }

  return (
    <div className="space-y-6">
      <MarketFiltersBar
        title="Advanced Flip Scanner"
        description="Scans the ranked top-flips endpoint with ROI, profit, liquidity, team, and series filters so you can surface the best live opportunities quickly."
        value={draftFilters}
        onChange={setDraftFilters}
        onApply={() => {
          setAppliedFilters(draftFilters);
          setPage(1);
        }}
        onReset={() => {
          setDraftFilters(defaultFilters);
          setAppliedFilters(defaultFilters);
          setPage(1);
        }}
        sortOptions={[
          { value: 'roi', label: 'ROI' },
          { value: 'profit_after_tax', label: 'Profit after tax' },
          { value: 'profit_per_minute', label: 'Profit per minute' },
          { value: 'flip_score', label: 'Flip score' },
        ]}
        showSortOrder={false}
        isApplying={isLoading}
      />

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
          <div className="text-sm text-slate-400">Flip opportunities</div>
          <div className="mt-3 text-3xl font-semibold text-white">{items.length}</div>
          <div className="mt-2 text-sm text-slate-500">Positive after-tax edges in the cache</div>
        </div>
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
          <div className="text-sm text-slate-400">Best profit</div>
          <div className="mt-3 text-3xl font-semibold text-white">{formatStubs(bestProfit)}</div>
          <div className="mt-2 text-sm text-slate-500">Highest raw profit right now</div>
        </div>
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
          <div className="text-sm text-slate-400">Best ROI</div>
          <div className="mt-3 text-3xl font-semibold text-white">{formatPercent(bestRoi)}</div>
          <div className="mt-2 text-sm text-slate-500">Best percent return after tax</div>
        </div>
      </section>

      <FlipTable title="Top Flip Opportunities" items={visibleItems} />
      <PaginationControls page={page} totalPages={totalPages} totalItems={items.length} pageSize={PAGE_SIZE} onPageChange={setPage} />

      {error ? <EmptyState title="Flip feed unavailable" description="The backend could not compute live listing flips from the current cache." /> : null}
    </div>
  );
}

export default function FlipsPage() {
  return (
    <RequireAuth>
      <FlipsPageContent />
    </RequireAuth>
  );
}
