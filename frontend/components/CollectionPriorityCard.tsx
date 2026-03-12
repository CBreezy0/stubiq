import { EmptyState } from '@/components/EmptyState';
import type { CollectionPriorityResponse, CollectionTarget } from '@/lib/types';
import { formatNumber, formatStubs } from '@/lib/utils';

function TargetList({ title, items }: { title: string; items: CollectionTarget[] }) {
  if (items.length === 0) {
    return <EmptyState title={`No ${title.toLowerCase()} yet`} description="Collection priorities will appear once your portfolio and Live Series costs are available." />;
  }

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold uppercase tracking-[0.25em] text-slate-500">{title}</h4>
      {items.map((target) => (
        <div key={`${title}-${target.name}`} className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="font-medium text-white">{target.name}</div>
              <div className="mt-1 text-sm text-slate-400">{target.rationale}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-500">Priority</div>
              <div className="text-lg font-semibold text-sky-200">{formatNumber(target.priority_score, 1)}</div>
            </div>
          </div>
          <div className="mt-4 grid gap-3 text-sm text-slate-300 sm:grid-cols-3">
            <div>
              <div className="text-slate-500">Completion</div>
              <div className="mt-1 font-medium text-white">{formatNumber(target.completion_pct, 0)}%</div>
            </div>
            <div>
              <div className="text-slate-500">Remaining cost</div>
              <div className="mt-1 font-medium text-white">{formatStubs(target.remaining_cost)}</div>
            </div>
            <div>
              <div className="text-slate-500">Owned gatekeeper value</div>
              <div className="mt-1 font-medium text-white">{formatStubs(target.owned_gatekeeper_value)}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function CollectionPriorityCard({ data, error }: { data?: CollectionPriorityResponse; error?: Error }) {
  if (error) {
    return <EmptyState title="Collection priorities unavailable" description="The backend could not build collection planning data yet. Check portfolio inventory and Live Series pricing." />;
  }
  if (!data) {
    return <EmptyState title="No collection priorities yet" description="Once Live Series prices and your owned gatekeepers sync, the engine will rank the best path to completion." />;
  }

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
      <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Collection Priorities</h3>
          <p className="text-sm text-slate-400">Divisions are ranked by owned gatekeepers, remaining cost, reward value, and locking opportunity cost.</p>
        </div>
        <div className="text-sm text-slate-400">Projected cost: <span className="font-medium text-white">{formatStubs(data.projected_completion_cost)}</span></div>
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        <TargetList title="Top Divisions" items={data.ranked_division_targets.slice(0, 3)} />
        <TargetList title="Top Teams" items={data.ranked_team_targets.slice(0, 3)} />
      </div>
    </div>
  );
}
