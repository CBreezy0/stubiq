'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useMemo, useState } from 'react';
import useSWR from 'swr';

import { EmptyState } from '@/components/EmptyState';
import { LoadingState } from '@/components/LoadingState';
import { PriceHistoryChart } from '@/components/PriceHistoryChart';
import { RequireAuth } from '@/components/RequireAuth';
import { api } from '@/lib/api';
import { formatPercent, formatRelativeDate, formatStubs } from '@/lib/utils';

async function fetchCardContext(itemId: string) {
  const [card, history7, history1] = await Promise.all([
    api.getCardDetail(itemId),
    api.getMarketHistory(itemId, 7),
    api.getMarketHistory(itemId, 1),
  ]);
  return { card, history7, history1 };
}

function CardDetailContent() {
  const params = useParams<{ uuid: string }>();
  const itemId = params.uuid;
  const [range, setRange] = useState<1 | 7>(7);

  const { data, error, isLoading } = useSWR(itemId ? ['card-detail', itemId] : null, () => fetchCardContext(itemId));

  const activeHistory = range === 1 ? data?.history1 : data?.history7;
  const card = data?.card ?? null;
  const latestPoint = activeHistory?.points.at(-1) ?? data?.history7.points.at(-1) ?? null;
  const latestSellPrice = card?.latest_best_sell_order ?? latestPoint?.sell_price ?? card?.latest_sell_now ?? null;
  const latestBuyPrice = card?.latest_best_buy_order ?? latestPoint?.buy_price ?? card?.latest_buy_now ?? null;
  const estimatedProfit = latestBuyPrice != null && latestSellPrice != null ? Math.round(latestSellPrice * 0.9 - latestBuyPrice) : card?.latest_tax_adjusted_spread ?? null;
  const estimatedRoi = latestBuyPrice != null && latestBuyPrice > 0 && latestSellPrice != null ? ((latestSellPrice * 0.9 - latestBuyPrice) / latestBuyPrice) * 100 : null;
  const title = card?.name ?? data?.history7.name ?? itemId;

  const metadata = useMemo(
    () => [
      { label: 'Team', value: card?.team ?? '—' },
      { label: 'Series', value: card?.series ?? '—' },
      { label: 'Position', value: card?.display_position ?? '—' },
      { label: 'Overall', value: card?.overall != null ? String(card.overall) : '—' },
      { label: 'Rarity', value: card?.rarity ?? '—' },
      { label: 'Item ID', value: card?.item_id ?? itemId },
    ],
    [card, itemId],
  );

  if (isLoading && !data) {
    return <LoadingState label="Loading card detail..." />;
  }

  if (error || !data) {
    return <EmptyState title="Card detail unavailable" description="The selected card could not be loaded from the current market cache." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link href="/market" className="text-sm text-sky-300 transition hover:text-sky-200">
              ← Back to market
            </Link>
            <p className="mt-3 text-xs uppercase tracking-[0.35em] text-sky-300">Card Detail</p>
            <h2 className="mt-3 text-3xl font-semibold text-white">{title}</h2>
            <p className="mt-3 max-w-3xl text-sm text-slate-400">Live market pricing, recent history, and after-tax ROI context for the selected card.</p>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-3 text-sm text-slate-300">
            Last seen <span className="font-semibold text-white">{formatRelativeDate(card?.observed_at ?? activeHistory?.points.at(-1)?.timestamp)}</span>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
            <div className="text-xs uppercase tracking-[0.25em] text-slate-500">Best buy</div>
            <div className="mt-2 text-2xl font-semibold text-white">{formatStubs(latestBuyPrice)}</div>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
            <div className="text-xs uppercase tracking-[0.25em] text-slate-500">Best sell</div>
            <div className="mt-2 text-2xl font-semibold text-white">{formatStubs(latestSellPrice)}</div>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
            <div className="text-xs uppercase tracking-[0.25em] text-slate-500">Spread</div>
            <div className="mt-2 text-2xl font-semibold text-white">{formatStubs(card?.latest_tax_adjusted_spread)}</div>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
            <div className="text-xs uppercase tracking-[0.25em] text-slate-500">Profit after tax</div>
            <div className="mt-2 text-2xl font-semibold text-emerald-300">{formatStubs(estimatedProfit)}</div>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
            <div className="text-xs uppercase tracking-[0.25em] text-slate-500">ROI</div>
            <div className="mt-2 text-2xl font-semibold text-white">{formatPercent(estimatedRoi)}</div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
          <h3 className="text-lg font-semibold text-white">Card metadata</h3>
          <div className="mt-4 grid gap-3 text-sm text-slate-300">
            {metadata.map((item) => (
              <div key={item.label} className="rounded-2xl border border-slate-800 bg-slate-950/50 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500">{item.label}</div>
                <div className="mt-1 font-medium text-white">{item.value}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-950/50 p-4 text-sm text-slate-400">
            Liquidity score <span className="font-semibold text-white">{card?.liquidity_score?.toFixed(1) ?? '—'}</span> • Volatility score{' '}
            <span className="font-semibold text-white">{card?.volatility_score?.toFixed(1) ?? '—'}</span>
          </div>
        </div>

        <div className="space-y-6">
          <div className="flex flex-wrap gap-3">
            {[1, 7].map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setRange(value as 1 | 7)}
                className={`rounded-2xl px-4 py-2 text-sm font-semibold transition ${
                  range === value ? 'bg-sky-500 text-slate-950' : 'border border-slate-700 bg-slate-950 text-white hover:border-slate-600 hover:bg-slate-900'
                }`}
              >
                {value === 1 ? '24h' : '7d'}
              </button>
            ))}
          </div>

          {activeHistory && activeHistory.points.length > 0 ? (
            <>
              <PriceHistoryChart title={`Price history (${range === 1 ? '24h' : '7d'})`} points={activeHistory.points} metric="price" />
              <PriceHistoryChart title="ROI trend" points={activeHistory.points} metric="roi" />
            </>
          ) : (
            <EmptyState title="No history yet" description="Price history will populate after enough listing snapshots or price-history sync rows exist." />
          )}
        </div>
      </section>
    </div>
  );
}

export default function CardDetailPage() {
  return (
    <RequireAuth>
      <CardDetailContent />
    </RequireAuth>
  );
}
