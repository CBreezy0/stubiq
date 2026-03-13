import clsx from 'clsx';

import type { MarketPhase, MarketPhaseResponse, PortfolioPosition, PriceHistoryPoint, RecommendationAction } from '@/lib/types';

export function formatStubs(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—';
  return `${Math.round(value).toLocaleString()} stubs`;
}

export function formatSignedStubs(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—';
  const rounded = Math.round(value);
  const sign = rounded > 0 ? '+' : '';
  return `${sign}${rounded.toLocaleString()} stubs`;
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

export function formatSignedPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(Math.abs(value) >= 10 ? 0 : 1)}%`;
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

export function formatChartLabel(value: string | null | undefined): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
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
      label:
        index === sorted.length - 1
          ? 'Now'
          : new Date(position.updated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
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

export function computePriceHistoryRoi(point: PriceHistoryPoint, taxRate = 0.1) {
  if (point.buy_price == null || point.sell_price == null || point.buy_price <= 0) return null;
  const afterTax = point.sell_price * (1 - taxRate);
  return ((afterTax - point.buy_price) / point.buy_price) * 100;
}

export function buildPriceHistorySeries(points: PriceHistoryPoint[]) {
  return points.map((point) => ({
    label: formatChartLabel(point.timestamp),
    timestamp: point.timestamp,
    buyPrice: point.buy_price,
    sellPrice: point.sell_price,
    midPrice:
      point.buy_price != null && point.sell_price != null
        ? Math.round((point.buy_price + point.sell_price) / 2)
        : point.sell_price ?? point.buy_price ?? null,
    roi: computePriceHistoryRoi(point),
  }));
}

export function spreadSignal(spread: number | null | undefined) {
  if (spread == null) {
    return { label: 'No spread', tone: 'slate' as const };
  }
  if (spread >= 2000) {
    return { label: 'Wide', tone: 'emerald' as const };
  }
  if (spread >= 750) {
    return { label: 'Healthy', tone: 'sky' as const };
  }
  if (spread > 0) {
    return { label: 'Tight', tone: 'amber' as const };
  }
  return { label: 'Flat', tone: 'rose' as const };
}

export function toneClasses(tone: 'emerald' | 'sky' | 'amber' | 'rose' | 'slate') {
  return clsx(
    'inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs font-medium',
    tone === 'emerald' && 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200',
    tone === 'sky' && 'border-sky-400/30 bg-sky-400/10 text-sky-200',
    tone === 'amber' && 'border-amber-400/30 bg-amber-400/10 text-amber-200',
    tone === 'rose' && 'border-rose-400/30 bg-rose-400/10 text-rose-200',
    tone === 'slate' && 'border-slate-600/60 bg-slate-800/60 text-slate-300',
  );
}
