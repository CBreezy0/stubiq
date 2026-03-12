import clsx from 'clsx';

import type { MarketPhase, RecommendationAction, MarketPhaseResponse, PortfolioPosition } from '@/lib/types';

export function formatStubs(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—';
  return `${Math.round(value).toLocaleString()} stubs`;
}

export function formatNumber(value: number | null | undefined, maximumFractionDigits = 0): string {
  if (value == null || Number.isNaN(value)) return '—';
  return value.toLocaleString(undefined, { maximumFractionDigits });
}

export function formatPercent(value: number | null | undefined, scale: 'unit' | 'percent' = 'percent'): string {
  if (value == null || Number.isNaN(value)) return '—';
  const normalized = scale === 'unit' ? value * 100 : value;
  return `${normalized.toFixed(normalized >= 10 ? 0 : 1)}%`;
}

export function formatRelativeDate(value: string | null | undefined): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date);
}

export const marketPhaseLabels: Record<MarketPhase, string> = {
  EARLY_ACCESS: 'Early Access',
  FULL_LAUNCH_SUPPLY_SHOCK: 'Launch Supply Shock',
  STABILIZATION: 'Stabilization',
  PRE_ATTRIBUTE_UPDATE: 'Pre-Update',
  POST_ATTRIBUTE_UPDATE: 'Post-Update',
  CONTENT_DROP: 'Content Drop',
  STUB_SALE: 'Stub Sale',
  LATE_CYCLE: 'Late Cycle',
};

export function actionBadgeClass(action: RecommendationAction): string {
  return clsx(
    'border px-2.5 py-1 text-xs font-semibold uppercase tracking-wide',
    action === 'BUY' && 'border-emerald-400/40 bg-emerald-400/15 text-emerald-200',
    action === 'SELL' && 'border-rose-400/40 bg-rose-400/15 text-rose-200',
    action === 'HOLD' && 'border-sky-400/40 bg-sky-400/15 text-sky-200',
    action === 'LOCK' && 'border-violet-400/40 bg-violet-400/15 text-violet-200',
    action === 'FLIP' && 'border-amber-400/40 bg-amber-400/15 text-amber-200',
    action === 'WATCH' && 'border-cyan-400/40 bg-cyan-400/15 text-cyan-200',
    action === 'GRIND' && 'border-indigo-400/40 bg-indigo-400/15 text-indigo-200',
    action === 'AVOID' && 'border-slate-400/40 bg-slate-400/15 text-slate-200',
    action === 'IGNORE' && 'border-slate-500/40 bg-slate-500/10 text-slate-300',
  );
}

export function buildLaunchAlerts(phase: MarketPhaseResponse | null | undefined): string[] {
  if (!phase) return [];
  switch (phase.phase) {
    case 'EARLY_ACCESS':
      return ['Prices are inflated in early access. Prioritize liquidity and avoid treating March 13–16 prices as fair value baselines.'];
    case 'FULL_LAUNCH_SUPPLY_SHOCK':
      return ['Full launch supply is hitting the market. Expect crash velocity on pack-pulled cards and buy only near floor compression.'];
    case 'PRE_ATTRIBUTE_UPDATE':
      return ['Roster update window is approaching. Re-check 79→80 and 84→85 watches before prices move.'];
    default:
      return [];
  }
}

export function summarizePortfolioTrend(positions: PortfolioPosition[]) {
  const sorted = [...positions].sort((left, right) => left.updated_at.localeCompare(right.updated_at));
  if (sorted.length === 0) {
    return [{ label: 'Now', value: 0 }];
  }
  let runningValue = 0;
  return sorted.map((position, index) => {
    runningValue += (position.current_market_value ?? position.avg_acquisition_cost) * position.quantity;
    return {
      label: index === sorted.length - 1 ? 'Now' : new Date(position.updated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      value: runningValue,
    };
  });
}

export function summarizeRarityDistribution(positions: PortfolioPosition[]) {
  const buckets = new Map<string, number>();
  for (const position of positions) {
    const label = position.card.rarity ?? 'Unknown';
    const current = buckets.get(label) ?? 0;
    buckets.set(label, current + position.quantity);
  }
  return Array.from(buckets.entries()).map(([name, value]) => ({ name, value }));
}
