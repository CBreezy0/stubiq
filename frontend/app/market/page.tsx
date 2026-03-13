'use client';

import { useEffect, useMemo, useState } from 'react';
import useSWR from 'swr';

import { EmptyState } from '@/components/EmptyState';
import { LoadingState } from '@/components/LoadingState';
import { MarketFiltersBar, MarketFilterState, buildMarketQueryFromFilters } from '@/components/MarketFiltersBar';
import { MarketListingsTable } from '@/components/MarketListingsTable';
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
  sortBy: 'profit',
  sortOrder: 'desc',
};

function MarketPageContent() {
  const [draftFilters, setDraftFilters] = useState<MarketFilterState>(defaultFilters);
  const [appliedFilters, setAppliedFilters] = useState<MarketFilterState>(defaultFilters);
  const [page, setPage] = useState(1);

  const query = useMemo(() => buildMarketQueryFromFilters(appliedFilters, 200), [appliedFilters]);
  const { data, error, isLoading } = useSWR(['market-listings-page', query], () => api.getMarketListings(query), { refreshInterval: 30_000 });

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
    return <LoadingState label="Loading live listings..." />;
  }

  return (
    <div className="space-y-6">
      <MarketFiltersBar
        title="Live Listings"
        description="Current best buy and sell orders with backend sorting, plus client-side pagination for quick browsing through the live cache."
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
          { value: 'profit', label: 'Profit after tax' },
          { value: 'roi', label: 'ROI' },
          { value: 'spread', label: 'Spread' },
        ]}
        isApplying={isLoading}
      />

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
          <div className="text-sm text-slate-400">Results</div>
          <div className="mt-3 text-3xl font-semibold text-white">{items.length}</div>
          <div className="mt-2 text-sm text-slate-500">Filtered listings ready to scan</div>
        </div>
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
          <div className="text-sm text-slate-400">Best profit</div>
          <div className="mt-3 text-3xl font-semibold text-white">{formatStubs(bestProfit)}</div>
          <div className="mt-2 text-sm text-slate-500">Current top result after filters</div>
        </div>
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
          <div className="text-sm text-slate-400">Best ROI</div>
          <div className="mt-3 text-3xl font-semibold text-white">{formatPercent(bestRoi)}</div>
          <div className="mt-2 text-sm text-slate-500">Best listing edge by after-tax return</div>
        </div>
      </section>

      <MarketListingsTable title="Market Listings" items={visibleItems} />
      <PaginationControls page={page} totalPages={totalPages} totalItems={items.length} pageSize={PAGE_SIZE} onPageChange={setPage} />

      {error ? <EmptyState title="Listings unavailable" description="The backend could not load market listings from the current cache." /> : null}
    </div>
  );
}

export default function MarketPage() {
  return (
    <RequireAuth>
      <MarketPageContent />
    </RequireAuth>
  );
}
