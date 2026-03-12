import { ConfidenceBar } from '@/components/ConfidenceBar';
import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import type { MarketOpportunity } from '@/lib/types';
import { formatNumber, formatStubs } from '@/lib/utils';

export function FlipTable({ title, items }: { title: string; items: MarketOpportunity[] }) {
  if (items.length === 0) {
    return <EmptyState title={`No ${title.toLowerCase()} yet`} description="The market engine has not surfaced any strong opportunities from the current snapshots." />;
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
              <th className="px-5 py-3 font-medium">Profit</th>
              <th className="px-5 py-3 font-medium">Liquidity</th>
              <th className="px-5 py-3 font-medium">Risk</th>
              <th className="px-5 py-3 font-medium">Decision</th>
              <th className="px-5 py-3 font-medium">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.item_id} className="border-t border-slate-800/80 text-slate-200">
                <td className="px-5 py-4">
                  <div className="font-medium text-white">{item.card.name}</div>
                  <div className="text-xs text-slate-500">{item.card.series ?? 'Unknown series'} • OVR {item.card.overall ?? '—'}</div>
                </td>
                <td className="px-5 py-4">{formatStubs(item.expected_profit_per_flip)}</td>
                <td className="px-5 py-4">{formatNumber(item.liquidity_score, 0)}</td>
                <td className="px-5 py-4">{formatNumber(item.risk_score, 0)}</td>
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
