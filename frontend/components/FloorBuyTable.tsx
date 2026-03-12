import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import type { MarketOpportunity } from '@/lib/types';
import { formatNumber, formatStubs } from '@/lib/utils';

export function FloorBuyTable({ items }: { items: MarketOpportunity[] }) {
  if (items.length === 0) {
    return <EmptyState title="No floor buys detected" description="When quicksell-adjacent cards compress toward the modeled floor, they’ll show up here." />;
  }

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Top Floor Buys</h3>
        <span className="text-xs uppercase tracking-[0.25em] text-slate-500">Quicksell & trend compression</span>
      </div>
      <div className="space-y-4">
        {items.map((item) => (
          <div key={item.item_id} className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="font-medium text-white">{item.card.name}</div>
                <div className="mt-1 text-sm text-slate-400">{item.card.team ?? 'MLB'} • OVR {item.card.overall ?? '—'} • {item.card.rarity ?? 'Unknown rarity'}</div>
              </div>
              <StatusBadge action={item.action} />
            </div>
            <div className="mt-4 grid gap-3 text-sm text-slate-300 sm:grid-cols-3">
              <div>
                <div className="text-slate-500">Floor proximity</div>
                <div className="mt-1 font-medium text-white">{formatNumber(item.floor_proximity_score, 0)}</div>
              </div>
              <div>
                <div className="text-slate-500">Expected flip profit</div>
                <div className="mt-1 font-medium text-white">{formatStubs(item.expected_profit_per_flip)}</div>
              </div>
              <div>
                <div className="text-slate-500">Liquidity</div>
                <div className="mt-1 font-medium text-white">{formatNumber(item.liquidity_score, 0)}</div>
              </div>
            </div>
            <p className="mt-4 text-sm text-slate-400">{item.rationale}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
