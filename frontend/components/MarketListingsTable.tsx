'use client';

import Link from 'next/link';

import { EmptyState } from '@/components/EmptyState';
import type { MarketListing } from '@/lib/types';
import { formatPercent, formatRelativeDate, formatStubs, spreadSignal, toneClasses } from '@/lib/utils';

interface MarketListingsTableProps {
  title: string;
  items: MarketListing[];
  variant?: 'market' | 'flips';
  emptyTitle?: string;
  emptyDescription?: string;
}

export function MarketListingsTable({
  title,
  items,
  variant = 'market',
  emptyTitle = 'No live listings yet',
  emptyDescription = 'Run a listings sync to start filling the live listings cache.',
}: MarketListingsTableProps) {
  if (items.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
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
              <th className="px-5 py-3 font-medium">Team</th>
              <th className="px-5 py-3 font-medium">Rarity</th>
              <th className="px-5 py-3 font-medium">Buy</th>
              <th className="px-5 py-3 font-medium">Sell</th>
              <th className="px-5 py-3 font-medium">Spread</th>
              <th className="px-5 py-3 font-medium">Profit</th>
              <th className="px-5 py-3 font-medium">ROI</th>
              {variant === 'flips' ? <th className="px-5 py-3 font-medium">Flip score</th> : null}
              <th className="px-5 py-3 font-medium">Seen</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const signal = spreadSignal(item.spread);
              return (
                <tr key={item.uuid} className="border-t border-slate-800/80 text-slate-200">
                  <td className="px-5 py-4">
                    <Link href={`/cards/${item.uuid}`} className="font-medium text-white transition hover:text-sky-300">
                      {item.name}
                    </Link>
                    <div className="text-xs text-slate-500">
                      {item.series ?? 'Unknown series'} • {item.position ?? 'ATH'} • OVR {item.overall ?? '—'}
                    </div>
                  </td>
                  <td className="px-5 py-4">{item.team ?? 'MLB'}</td>
                  <td className="px-5 py-4">{item.rarity ?? '—'}</td>
                  <td className="px-5 py-4">{formatStubs(item.best_buy_price)}</td>
                  <td className="px-5 py-4">{formatStubs(item.best_sell_price)}</td>
                  <td className="px-5 py-4">
                    <div>{formatStubs(item.spread)}</div>
                    <div className="mt-1">
                      <span className={toneClasses(signal.tone)}>{signal.label}</span>
                    </div>
                  </td>
                  <td className="px-5 py-4 text-emerald-300">{formatStubs(item.profit_after_tax)}</td>
                  <td className="px-5 py-4">{formatPercent(item.roi)}</td>
                  {variant === 'flips' ? <td className="px-5 py-4">{item.flip_score?.toFixed(1) ?? '—'}</td> : null}
                  <td className="px-5 py-4 text-xs text-slate-400">{formatRelativeDate(item.last_seen_at)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
