import { ConfidenceBar } from '@/components/ConfidenceBar';
import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import type { RosterUpdateRecommendation } from '@/lib/types';
import { formatPercent, formatStubs } from '@/lib/utils';

export function RosterTargetsTable({ items }: { items: RosterUpdateRecommendation[] }) {
  if (items.length === 0) {
    return <EmptyState title="No roster update targets yet" description="Once MLB stat snapshots and live market prices line up, the predictor will rank 79→80 and 84→85 candidates here." />;
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/70 shadow-lg">
      <div className="border-b border-slate-800 px-5 py-4">
        <h3 className="text-lg font-semibold text-white">Top Roster Update Targets</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-950/50 text-left text-slate-400">
            <tr>
              <th className="px-5 py-3 font-medium">Player</th>
              <th className="px-5 py-3 font-medium">Upgrade odds</th>
              <th className="px-5 py-3 font-medium">Current price</th>
              <th className="px-5 py-3 font-medium">Expected profit</th>
              <th className="px-5 py-3 font-medium">Action</th>
              <th className="px-5 py-3 font-medium">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.item_id} className="border-t border-slate-800/80 text-slate-200">
                <td className="px-5 py-4">
                  <div className="font-medium text-white">{item.player_name}</div>
                  <div className="text-xs text-slate-500">OVR {item.current_ovr} • {item.card.series ?? 'Live Series'}</div>
                </td>
                <td className="px-5 py-4">{formatPercent(item.upgrade_probability, 'unit')}</td>
                <td className="px-5 py-4">{formatStubs(item.current_price)}</td>
                <td className="px-5 py-4">{formatStubs(item.expected_profit)}</td>
                <td className="px-5 py-4"><StatusBadge action={item.action} /></td>
                <td className="px-5 py-4"><ConfidenceBar value={item.confidence} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
