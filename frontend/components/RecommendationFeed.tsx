import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import type { PortfolioRecommendation } from '@/lib/types';

export function RecommendationFeed({ items }: { items: PortfolioRecommendation[] }) {
  if (items.length === 0) {
    return <EmptyState title="No recommendation feed yet" description="Signals from your portfolio engine will show up here once you own cards or positions are scored." />;
  }

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Recommendation Feed</h3>
        <span className="text-xs uppercase tracking-[0.25em] text-slate-500">Portfolio signals</span>
      </div>
      <div className="space-y-4">
        {items.map((item) => (
          <div key={`${item.item_id}-${item.action}`} className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-medium text-white">{item.item_id}</div>
              <StatusBadge action={item.action} />
            </div>
            <p className="mt-3 text-sm text-slate-400">{item.rationale}</p>
            <div className="mt-3 text-xs text-slate-500">Confidence {Math.round(item.confidence)}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}
