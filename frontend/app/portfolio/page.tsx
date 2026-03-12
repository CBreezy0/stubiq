'use client';

import { FormEvent, useMemo, useState } from 'react';

import { EmptyState } from '@/components/EmptyState';
import { LoadingState } from '@/components/LoadingState';
import { MarketPhaseBanner } from '@/components/MarketPhaseBanner';
import { MetricCard } from '@/components/MetricCard';
import { PortfolioHoldingsTable } from '@/components/PortfolioHoldingsTable';
import { PortfolioTrendChart } from '@/components/PortfolioTrendChart';
import { RarityDistributionChart } from '@/components/RarityDistributionChart';
import { useToast } from '@/components/ToastProvider';
import { usePortfolio } from '@/hooks/usePortfolio';
import { useDashboard } from '@/hooks/useDashboard';
import { formatStubs } from '@/lib/utils';

export default function PortfolioPage() {
  const { portfolio, recommendations, addCard, removeCard } = usePortfolio();
  const { phase } = useDashboard();
  const { push } = useToast();

  const [addForm, setAddForm] = useState({
    item_id: '',
    card_name: '',
    quantity: 1,
    avg_acquisition_cost: 0,
    locked_for_collection: false,
  });
  const [removeForm, setRemoveForm] = useState({ item_id: '', quantity: 1, remove_all: false });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const recommendationMap = useMemo(
    () => new Map((recommendations.data ?? []).map((item) => [item.item_id, item])),
    [recommendations.data],
  );

  if (portfolio.isLoading && !portfolio.data) {
    return <LoadingState label="Loading portfolio..." />;
  }

  if (portfolio.error && !portfolio.data) {
    return <EmptyState title="Portfolio unavailable" description="Could not load portfolio data from the backend. Verify the API and try again." />;
  }

  const handleAdd = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      await addCard(addForm);
      push({ tone: 'success', title: 'Card added', description: `${addForm.card_name} is now tracked in your portfolio.` });
      setAddForm({ item_id: '', card_name: '', quantity: 1, avg_acquisition_cost: 0, locked_for_collection: false });
    } catch (error) {
      push({ tone: 'error', title: 'Add failed', description: error instanceof Error ? error.message : 'Could not add the card.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRemove = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      await removeCard(removeForm);
      push({ tone: 'success', title: 'Card removed', description: `Updated holdings for item ${removeForm.item_id}.` });
      setRemoveForm({ item_id: '', quantity: 1, remove_all: false });
    } catch (error) {
      push({ tone: 'error', title: 'Remove failed', description: error instanceof Error ? error.message : 'Could not remove the card.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const positions = portfolio.data?.items ?? [];

  return (
    <div className="space-y-6">
      <MarketPhaseBanner phase={phase.data?.current} />

      <section className="grid gap-4 xl:grid-cols-4 md:grid-cols-2">
        <MetricCard title="Total Portfolio Value" value={formatStubs(portfolio.data?.total_market_value ?? 0)} hint="Current marked-to-market stub value" />
        <MetricCard title="Total Invested" value={formatStubs(portfolio.data?.total_cost_basis ?? 0)} hint="Tracked acquisition cost basis" />
        <MetricCard title="Unrealized P/L" value={formatStubs(portfolio.data?.total_unrealized_profit ?? 0)} hint="Live mark-to-market profit or loss" />
        <MetricCard title="Realized P/L" value="Pending" hint="Add a transaction summary endpoint to unlock realized performance." />
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <PortfolioTrendChart positions={positions} />
        <RarityDistributionChart positions={positions} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <PortfolioHoldingsTable positions={positions} recommendations={recommendationMap} />
        <div className="space-y-6">
          <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
            <h2 className="text-lg font-semibold text-white">Portfolio Actions</h2>
            <p className="mt-1 text-sm text-slate-400">Add or remove cards while you play. CSV import is scaffolded for a future pass.</p>
            <form className="mt-5 space-y-3" onSubmit={handleAdd}>
              <div className="grid gap-3 sm:grid-cols-2">
                <input value={addForm.item_id} onChange={(event) => setAddForm((current) => ({ ...current, item_id: event.target.value }))} placeholder="Item ID" className="rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
                <input value={addForm.card_name} onChange={(event) => setAddForm((current) => ({ ...current, card_name: event.target.value }))} placeholder="Card name" className="rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
                <input type="number" min="1" value={addForm.quantity} onChange={(event) => setAddForm((current) => ({ ...current, quantity: Number(event.target.value) }))} placeholder="Quantity" className="rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
                <input type="number" min="0" value={addForm.avg_acquisition_cost} onChange={(event) => setAddForm((current) => ({ ...current, avg_acquisition_cost: Number(event.target.value) }))} placeholder="Avg acquisition cost" className="rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
              </div>
              <label className="flex items-center gap-2 text-sm text-slate-300">
                <input type="checkbox" checked={addForm.locked_for_collection} onChange={(event) => setAddForm((current) => ({ ...current, locked_for_collection: event.target.checked }))} />
                Locked for collection
              </label>
              <button type="submit" disabled={isSubmitting} className="rounded-2xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:opacity-60">{isSubmitting ? 'Saving...' : 'Add Card'}</button>
            </form>
          </div>

          <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
            <h2 className="text-lg font-semibold text-white">Remove Card</h2>
            <form className="mt-5 space-y-3" onSubmit={handleRemove}>
              <input value={removeForm.item_id} onChange={(event) => setRemoveForm((current) => ({ ...current, item_id: event.target.value }))} placeholder="Item ID" className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
              <div className="grid gap-3 sm:grid-cols-2">
                <input type="number" min="1" value={removeForm.quantity} onChange={(event) => setRemoveForm((current) => ({ ...current, quantity: Number(event.target.value) }))} placeholder="Quantity" className="rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
                <label className="flex items-center gap-2 rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-300">
                  <input type="checkbox" checked={removeForm.remove_all} onChange={(event) => setRemoveForm((current) => ({ ...current, remove_all: event.target.checked }))} />
                  Remove all copies
                </label>
              </div>
              <button type="submit" disabled={isSubmitting} className="rounded-2xl bg-rose-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-400 disabled:opacity-60">{isSubmitting ? 'Updating...' : 'Remove Card'}</button>
            </form>
          </div>

          <div className="rounded-3xl border border-dashed border-slate-700 bg-slate-900/40 p-5 text-sm text-slate-400 shadow-inner">
            <div className="font-semibold text-white">Import CSV</div>
            <p className="mt-2">CSV import UI is reserved here. Wire it to the backend import route when you want bulk portfolio ingestion exposed.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
