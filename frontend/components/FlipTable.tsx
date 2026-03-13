'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';

import { EmptyState } from '@/components/EmptyState';
import type { FlipOpportunity } from '@/lib/types';

type SortableFlipOpportunity = FlipOpportunity & { profit_per_minute?: number | null };
type FlipSortField = 'profit_after_tax' | 'roi' | 'profit_per_minute' | 'best_sell_price';
type SortDirection = 'asc' | 'desc';

function formatStubs(value?: number | null) {
  if (value == null) return '—';
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value);
}

function formatPercent(value?: number | null) {
  if (value == null) return '—';
  return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value)}%`;
}

function compareNullableNumber(a: number | null | undefined, b: number | null | undefined, direction: SortDirection) {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  return direction === 'desc' ? b - a : a - b;
}

export function FlipTable({ title, items }: { title: string; items: FlipOpportunity[] }) {
  const [sortField, setSortField] = useState<FlipSortField>('profit_per_minute');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const sortedItems = useMemo(() => {
    const nextItems = [...(items as SortableFlipOpportunity[])];
    nextItems.sort((left, right) => {
      const mapping = {
        profit_after_tax: [left.profit_after_tax, right.profit_after_tax],
        roi: [left.roi, right.roi],
        profit_per_minute: [left.profit_per_minute, right.profit_per_minute],
        best_sell_price: [left.best_sell_price, right.best_sell_price],
      } as const;
      const [leftValue, rightValue] = mapping[sortField];
      return compareNullableNumber(leftValue, rightValue, sortDirection);
    });
    return nextItems;
  }, [items, sortDirection, sortField]);

  const handleSort = (field: FlipSortField) => {
    if (field === sortField) {
      setSortDirection((current) => (current === 'desc' ? 'asc' : 'desc'));
      return;
    }
    setSortField(field);
    setSortDirection('desc');
  };

  const sortIndicator = (field: FlipSortField) => {
    if (field !== sortField) return '↕';
    return sortDirection === 'desc' ? '↓' : '↑';
  };

  if (sortedItems.length === 0) {
    return <EmptyState title={`No ${title.toLowerCase()} yet`} description="The live listing cache has not surfaced any positive-ROI flips yet." />;
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
              <th className="px-5 py-3 font-medium">Buy</th>
              <th className="px-5 py-3 font-medium">
                <button type="button" onClick={() => handleSort('best_sell_price')} className="inline-flex items-center gap-1 text-left transition hover:text-white">
                  Sell <span className="text-xs">{sortIndicator('best_sell_price')}</span>
                </button>
              </th>
              <th className="px-5 py-3 font-medium">
                <button type="button" onClick={() => handleSort('profit_after_tax')} className="inline-flex items-center gap-1 text-left transition hover:text-white">
                  Profit <span className="text-xs">{sortIndicator('profit_after_tax')}</span>
                </button>
              </th>
              <th className="px-5 py-3 font-medium">
                <button type="button" onClick={() => handleSort('roi')} className="inline-flex items-center gap-1 text-left transition hover:text-white">
                  ROI <span className="text-xs">{sortIndicator('roi')}</span>
                </button>
              </th>
              <th className="px-5 py-3 font-medium">
                <button type="button" onClick={() => handleSort('profit_per_minute')} className="inline-flex items-center gap-1 text-left transition hover:text-white">
                  Profit / Min <span className="text-xs">{sortIndicator('profit_per_minute')}</span>
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedItems.map((item) => (
              <tr key={item.uuid} className="border-t border-slate-800/80 text-slate-200">
                <td className="px-5 py-4">
                  <Link href={`/cards/${item.uuid}`} className="font-medium text-white transition hover:text-sky-300">
                    {item.name}
                  </Link>
                </td>
                <td className="px-5 py-4">{formatStubs(item.best_buy_price)}</td>
                <td className="px-5 py-4">{formatStubs(item.best_sell_price)}</td>
                <td className="px-5 py-4 text-emerald-300">{formatStubs(item.profit_after_tax)}</td>
                <td className="px-5 py-4">{formatPercent(item.roi)}</td>
                <td className="px-5 py-4">{formatStubs(item.profit_per_minute)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
