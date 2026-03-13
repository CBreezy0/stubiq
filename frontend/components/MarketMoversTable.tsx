'use client';

import Link from 'next/link';

import { EmptyState } from '@/components/EmptyState';
import type { MarketMover } from '@/lib/types';
import { formatRelativeDate, formatSignedPercent, formatSignedStubs, formatStubs } from '@/lib/utils';

type DashboardMarketMover = {
  item_id: string;
  name: string;
  best_buy_price?: number | null;
  best_sell_price?: number | null;
  price_change: number;
  change_percent: number;
  liquidity_score?: number | null;
};

interface MarketMoversTableProps {
  title: string;
  items: Array<MarketMover | DashboardMarketMover>;
  emptyTitle?: string;
  emptyDescription?: string;
  variant?: 'trend' | 'market';
}

export function MarketMoversTable({
  title,
  items,
  emptyTitle = 'No movers yet',
  emptyDescription = 'The current cache does not have enough price history to score movers.',
  variant = 'trend',
}: MarketMoversTableProps) {
  if (items.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  const trendItems = items as MarketMover[];

  if (variant === 'market') {
    const marketItems = items as DashboardMarketMover[];

    return (
      <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/70 shadow-lg">
        <div className="border-b border-slate-800 px-5 py-4">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-950/50 text-left text-slate-400">
              <tr>
                <th className="px-5 py-3 font-medium">Card</th>
                <th className="px-5 py-3 font-medium">Change</th>
                <th className="px-5 py-3 font-medium">Change %</th>
                <th className="px-5 py-3 font-medium">Sell</th>
                <th className="px-5 py-3 font-medium">Liquidity</th>
              </tr>
            </thead>
            <tbody>
              {marketItems.map((item) => (
                <tr key={item.item_id} className="border-t border-slate-800/80 text-slate-200">
                  <td className="px-5 py-4">
                    <Link href={`/cards/${item.item_id}`} className="font-medium text-white transition hover:text-sky-300">
                      {item.name}
                    </Link>
                  </td>
                  <td className="px-5 py-4">
                    <div className={item.price_change >= 0 ? 'text-emerald-300' : 'text-rose-300'}>{formatSignedStubs(item.price_change)}</div>
                  </td>
                  <td className="px-5 py-4">{formatSignedPercent(item.change_percent * 100)}</td>
                  <td className="px-5 py-4">{formatStubs(item.best_sell_price)}</td>
                  <td className="px-5 py-4">{item.liquidity_score?.toFixed(1) ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/70 shadow-lg">
      <div className="border-b border-slate-800 px-5 py-4">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-950/50 text-left text-slate-400">
            <tr>
              <th className="px-5 py-3 font-medium">Card</th>
              <th className="px-5 py-3 font-medium">Prev</th>
              <th className="px-5 py-3 font-medium">Current</th>
              <th className="px-5 py-3 font-medium">Change</th>
              <th className="px-5 py-3 font-medium">Trend</th>
              <th className="px-5 py-3 font-medium">Seen</th>
            </tr>
          </thead>
          <tbody>
            {trendItems.map((item) => (
              <tr key={item.uuid} className="border-t border-slate-800/80 text-slate-200">
                <td className="px-5 py-4">
                  <Link href={`/cards/${item.uuid}`} className="font-medium text-white transition hover:text-sky-300">
                    {item.name}
                  </Link>
                  <div className="text-xs text-slate-500">
                    {item.team ?? 'MLB'} • {item.series ?? 'Unknown series'} • {item.rarity ?? 'Unknown rarity'}
                  </div>
                </td>
                <td className="px-5 py-4">{formatStubs(item.previous_price)}</td>
                <td className="px-5 py-4">{formatStubs(item.current_price)}</td>
                <td className="px-5 py-4">
                  <div className={item.change_amount != null && item.change_amount >= 0 ? 'text-emerald-300' : 'text-rose-300'}>{formatSignedStubs(item.change_amount)}</div>
                  <div className="text-xs text-slate-400">{formatSignedPercent(item.change_pct)}</div>
                </td>
                <td className="px-5 py-4">{item.trend_score.toFixed(1)}</td>
                <td className="px-5 py-4 text-xs text-slate-400">{formatRelativeDate(item.last_seen_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
