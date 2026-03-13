'use client';

import Link from 'next/link';
import useSWR from 'swr';

import { EmptyState } from '@/components/EmptyState';
import { InventoryTable } from '@/components/InventoryTable';
import { LoadingState } from '@/components/LoadingState';
import { MetricCard } from '@/components/MetricCard';
import { RequireAuth } from '@/components/RequireAuth';
import { api } from '@/lib/api';
import { formatSignedStubs, formatStubs } from '@/lib/utils';

function InventoryPageContent() {
  const { data, error, isLoading } = useSWR('inventory-page', () => api.getInventory(), { refreshInterval: 60_000 });

  if (isLoading && !data) {
    return <LoadingState label="Loading imported inventory..." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-emerald-300">Inventory</p>
            <h2 className="mt-3 text-3xl font-semibold text-white">Imported Binder Snapshot</h2>
            <p className="mt-3 max-w-3xl text-sm text-slate-400">Current card holdings valued against the live market cache, with manual import until SDS authentication is automated.</p>
          </div>
          <Link
            href="/inventory/import"
            className="rounded-2xl bg-sky-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-400"
          >
            Import Inventory
          </Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Unique Cards" value={String(data?.count ?? 0)} hint="Distinct card rows in the import" />
        <MetricCard title="Total Quantity" value={String(data?.total_quantity ?? 0)} hint="All imported copies combined" />
        <MetricCard title="Market Value" value={formatStubs(data?.total_market_value ?? 0)} hint="Live sell-side marked-to-market value" />
        <MetricCard title="Estimated P/L" value={formatSignedStubs(data?.total_profit_loss ?? 0)} hint="Compared to tracked portfolio cost basis when available" />
      </section>

      {data ? <InventoryTable items={data.items} /> : null}
      {error ? <EmptyState title="Inventory unavailable" description="The backend could not load inventory data for this account." /> : null}
    </div>
  );
}

export default function InventoryPage() {
  return (
    <RequireAuth>
      <InventoryPageContent />
    </RequireAuth>
  );
}
