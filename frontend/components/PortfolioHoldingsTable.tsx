import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import type { PortfolioPosition, PortfolioRecommendation } from '@/lib/types';
import { formatStubs } from '@/lib/utils';

export function PortfolioHoldingsTable({
  positions,
  recommendations,
}: {
  positions: PortfolioPosition[];
  recommendations: Map<string, PortfolioRecommendation>;
}) {
  if (positions.length === 0) {
    return <EmptyState title="No portfolio positions yet" description="Add your first card manually to start tracking value, unrealized P/L, and strategy actions." />;
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/70 shadow-lg">
      <div className="border-b border-slate-800 px-5 py-4">
        <h3 className="text-lg font-semibold text-white">Holdings</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-950/50 text-left text-slate-400">
            <tr>
              <th className="px-5 py-3 font-medium">Card Name</th>
              <th className="px-5 py-3 font-medium">Series</th>
              <th className="px-5 py-3 font-medium">OVR</th>
              <th className="px-5 py-3 font-medium">Qty</th>
              <th className="px-5 py-3 font-medium">Avg Buy</th>
              <th className="px-5 py-3 font-medium">Market</th>
              <th className="px-5 py-3 font-medium">Unrealized P/L</th>
              <th className="px-5 py-3 font-medium">Recommendation</th>
              <th className="px-5 py-3 font-medium">Confidence</th>
              <th className="px-5 py-3 font-medium">Rationale</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((position) => {
              const recommendation = recommendations.get(position.item_id);
              return (
                <tr key={position.item_id} className="border-t border-slate-800/80 text-slate-200">
                  <td className="px-5 py-4">
                    <div className="font-medium text-white">{position.card.name}</div>
                    <div className="text-xs text-slate-500">{position.card.team ?? 'No team'} • {position.card.rarity ?? 'Unknown rarity'}</div>
                  </td>
                  <td className="px-5 py-4">{position.card.series ?? '—'}</td>
                  <td className="px-5 py-4">{position.card.overall ?? '—'}</td>
                  <td className="px-5 py-4">{position.quantity}</td>
                  <td className="px-5 py-4">{formatStubs(position.avg_acquisition_cost)}</td>
                  <td className="px-5 py-4">{formatStubs(position.current_market_value)}</td>
                  <td className={`px-5 py-4 ${(position.unrealized_profit ?? 0) >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
                    {formatStubs(position.unrealized_profit)}
                  </td>
                  <td className="px-5 py-4">{recommendation ? <StatusBadge action={recommendation.action} /> : '—'}</td>
                  <td className="px-5 py-4">{recommendation ? `${Math.round(recommendation.confidence)}%` : '—'}</td>
                  <td className="max-w-xs px-5 py-4 text-slate-400">{recommendation?.rationale ?? 'Recommendation pending.'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
