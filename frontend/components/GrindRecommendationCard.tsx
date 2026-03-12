import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import type { GrindRecommendationResponse } from '@/lib/types';
import { formatStubs } from '@/lib/utils';

export function GrindRecommendationCard({ data }: { data?: GrindRecommendationResponse }) {
  if (!data) {
    return <EmptyState title="No grind recommendation yet" description="Gameplay EV will appear here after program rewards and market EV are available." />;
  }

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Grind vs Market</h3>
          <p className="mt-1 text-sm text-slate-400">During launch week, this compares gameplay EV/hour against market EV/hour.</p>
        </div>
        <StatusBadge action={data.action} />
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
          <div className="text-sm text-slate-500">Best mode now</div>
          <div className="mt-1 text-xl font-semibold text-white">{data.best_mode_to_play_now}</div>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
          <div className="text-sm text-slate-500">Market EV / hour</div>
          <div className="mt-1 text-xl font-semibold text-white">{formatStubs(data.expected_market_stubs_per_hour)}</div>
        </div>
      </div>
      <p className="mt-4 text-sm text-slate-400">{data.rationale}</p>
    </div>
  );
}
