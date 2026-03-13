'use client';

import { useMemo, useState } from 'react';
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

type MarketMoverSortField = 'change_percent' | 'price_change' | 'best_sell_price' | 'liquidity_score';
type SortDirection = 'asc' | 'desc';

interface MarketMoversTableProps {
  title: string;
  items: Array<MarketMover | DashboardMarketMover>;
  emptyTitle?: string;
  emptyDescription?: string;
  variant?: 'trend' | 'market';
}

function compareNullableNumber(a: number | null | undefined, b: number | null | undefined, direction: SortDirection) {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  return direction === 'desc' ? b - a : a - b;
}

export function MarketMoversTable({
  title,
  items,
  emptyTitle = 'No movers yet',
  emptyDescription = 'The current cache does not have enough price history to score movers.',
  variant = 'trend',
}: MarketMoversTableProps) {
  const [sortField, setSortField] = useState<MarketMoverSortField>('change_percent');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const trendItems = items as MarketMover[];
  const marketItems = items as DashboardMarketMover[];

  const sortedMarketItems = useMemo(() => {
    const nextItems = [...marketItems];
    nextItems.sort((left, right) => {
      const mapping = {
        change_percent: [left.change_percent, right.change_percent],
        price_change: [left.price_change, right.price_change],
        best_sell_price: [left.best_sell_price, right.best_sell_price],
        liquidity_score: [left.liquidity_score, right.liquidity_score],
      } as const;
      const [leftValue, rightValue] = mapping[sortField];
      return compareNullableNumber(leftValue, rightValue, sortDirection);
    });
    return nextItems;
  }, [marketItems, sortDirection, sortField]);

  const handleSort = (field: MarketMoverSortField) => {
    if (field === sortField) {
      setSortDirection((current) => (current === 'desc' ? 'asc' : 'desc'));
      return;
    }
    setSortField(field);
    setSortDirection('desc');
  };

  const sortIndicator = (field: MarketMoverSortField) => {
    if (field !== sortField) return '↕';
    return sortDirection === 'desc' ? '↓' : '↑';
  };

  if (items.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  if (variant === 'market') {
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
                <th className="px-5 py-3 font-medium">
                  <button type="button" onClick={() => handleSort('price_change')} className="inline-flex items-center gap-1 text-left transition hover:text-white">
                    Change <span className="text-xs">{sortIndicator('price_change')}</span>
                  </button>
                </th>
                <th className="px-5 py-3 font-medium">
                  <button type="button" onClick={() => handleSort('change_percent')} className="inline-flex items-center gap-1 text-left transition hover:text-white">
                    Change % <span className="text-xs">{sortIndicator('change_percent')}</span>
                  </button>
                </th>
                <th className="px-5 py-3 font-medium">
                  <button type="button" onClick={() => handleSort('best_sell_price')} className="inline-flex items-center gap-1 text-left transition hover:text-white">
                    Sell <span className="text-xs">{sortIndicator('best_sell_price')}</span>
                  </button>
                </th>
                <th className="px-5 py-3 font-medium">
                  <button type="button" onClick={() => handleSort('liquidity_score')} className="inline-flex items-center gap-1 text-left transition hover:text-white">
                    Liquidity <span className="text-xs">{sortIndicator('liquidity_score')}</span>
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedMarketItems.map((item) => (
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
