'use client';

import { useEffect, useMemo, useState } from 'react';
import useSWR from 'swr';

import { EmptyState } from '@/components/EmptyState';
import { FlipTable } from '@/components/FlipTable';
import { LoadingState } from '@/components/LoadingState';
import { MarketFiltersBar, MarketFilterState, buildMarketQueryFromFilters } from '@/components/MarketFiltersBar';
import { PaginationControls } from '@/components/PaginationControls';
import { RequireAuth } from '@/components/RequireAuth';
import { api } from '@/lib/api';
import { formatPercent, formatStubs } from '@/lib/utils';

const PAGE_SIZE = 25;
const defaultFilters: MarketFilterState = {
  rarity: 'Any',
  series: '',
  team: '',
  minProfit: '',
  minRoi: '',
  sortBy: 'roi',
  sortOrder: 'desc',
};

function FlipsPageContent() {
  const [draftFilters, setDraftFilters] = useState<MarketFilterState>(defaultFilters);
  const [appliedFilters, setAppliedFilters] = useState<MarketFilterState>(defaultFilters);
  const [page, setPage] = useState(1);

  const query = useMemo(() => buildMarketQueryFromFilters(appliedFilters, 200), [appliedFilters]);
  const { data, error, isLoading } = useSWR(['live-flips-page', query], () => api.getFlips(query), { refreshInterval: 30_000 });

  const items = data?.items ?? [];
  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE));

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  const visibleItems = items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const bestProfit = items[0]?.profit_after_tax ?? null;
  const bestRoi = items[0]?.roi ?? null;

  if (isLoading && !data) {
    return <LoadingState label="Scanning live flips..." />;
  }

  return (
    <div className="space-y-6">
      <MarketFiltersBar
        title="Highest ROI Opportunities"
        description="Targets the live flip feed with backend filtering and a default ROI-first sort so you can prioritize efficient stub growth quickly."
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
          { value: 'profit', label: 'Profit after tax' },
          { value: 'spread', label: 'Spread' },
          { value: 'flip_score', label: 'Flip score' },
        ]}
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

      <FlipTable title="Top Live Flips" items={visibleItems} />
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
