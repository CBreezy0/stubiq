'use client';

import type { MarketListingsQuery, MarketSortField, SortOrder } from '@/lib/types';

export type MarketScannerSortField = MarketSortField | 'profit_after_tax' | 'profit_per_minute' | 'flip_score' | 'roi';

export interface MarketFilterState {
  rarity: string;
  series: string;
  team: string;
  minProfit: string;
  minRoi: string;
  minLiquidity?: string;
  sortBy: MarketScannerSortField;
  sortOrder: SortOrder;
}

interface MarketFiltersBarProps {
  title: string;
  description: string;
  value: MarketFilterState;
  onChange: (next: MarketFilterState) => void;
  onApply: () => void;
  onReset: () => void;
  sortOptions: Array<{ value: MarketScannerSortField; label: string }>;
  isApplying?: boolean;
  showSortOrder?: boolean;
}

const rarityOptions = ['Any', 'Common', 'Bronze', 'Silver', 'Gold', 'Diamond'];

export function buildMarketQueryFromFilters(filters: MarketFilterState, limit = 200): MarketListingsQuery {
  return {
    rarity: filters.rarity === 'Any' ? undefined : filters.rarity,
    series: filters.series || undefined,
    team: filters.team || undefined,
    min_profit: filters.minProfit ? Number(filters.minProfit) : undefined,
    min_roi: filters.minRoi ? Number(filters.minRoi) : undefined,
    sort_by: filters.sortBy as MarketSortField,
    sort_order: filters.sortOrder,
    limit,
  };
}

export function MarketFiltersBar({
  title,
  description,
  value,
  onChange,
  onApply,
  onReset,
  sortOptions,
  isApplying = false,
  showSortOrder = true,
}: MarketFiltersBarProps) {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg">
      <p className="text-xs uppercase tracking-[0.35em] text-sky-300">Market Scanner</p>
      <h2 className="mt-3 text-3xl font-semibold text-white">{title}</h2>
      <p className="mt-3 max-w-3xl text-sm text-slate-400">{description}</p>

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <label className="block text-sm text-slate-300">
          <span className="mb-2 block">Rarity</span>
          <select
            value={value.rarity}
            onChange={(event) => onChange({ ...value, rarity: event.target.value })}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-sky-400"
          >
            {rarityOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm text-slate-300">
          <span className="mb-2 block">Series</span>
          <input
            value={value.series}
            onChange={(event) => onChange({ ...value, series: event.target.value })}
            placeholder="Live, Awards, 2nd Half..."
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-sky-400"
          />
        </label>

        <label className="block text-sm text-slate-300">
          <span className="mb-2 block">Team</span>
          <input
            value={value.team}
            onChange={(event) => onChange({ ...value, team: event.target.value })}
            placeholder="Yankees, Dodgers..."
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-sky-400"
          />
        </label>

        <label className="block text-sm text-slate-300">
          <span className="mb-2 block">Min profit</span>
          <input
            type="number"
            min={0}
            value={value.minProfit}
            onChange={(event) => onChange({ ...value, minProfit: event.target.value })}
            placeholder="200"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-sky-400"
          />
        </label>

        <label className="block text-sm text-slate-300">
          <span className="mb-2 block">Min ROI (%)</span>
          <input
            type="number"
            min={0}
            step="0.1"
            value={value.minRoi}
            onChange={(event) => onChange({ ...value, minRoi: event.target.value })}
            placeholder="5"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-sky-400"
          />
        </label>

        <label className="block text-sm text-slate-300">
          <span className="mb-2 block">Min liquidity</span>
          <input
            type="number"
            min={0}
            step="0.1"
            value={value.minLiquidity ?? ''}
            onChange={(event) => onChange({ ...value, minLiquidity: event.target.value })}
            placeholder="50"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-sky-400"
          />
        </label>

        <label className="block text-sm text-slate-300">
          <span className="mb-2 block">Sort by</span>
          <select
            value={value.sortBy}
            onChange={(event) => onChange({ ...value, sortBy: event.target.value as MarketScannerSortField })}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-sky-400"
          >
            {sortOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        {showSortOrder ? (
          <label className="block text-sm text-slate-300">
            <span className="mb-2 block">Order</span>
            <select
              value={value.sortOrder}
              onChange={(event) => onChange({ ...value, sortOrder: event.target.value as SortOrder })}
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-sky-400"
            >
              <option value="desc">High to low</option>
              <option value="asc">Low to high</option>
            </select>
          </label>
        ) : null}
      </div>

      <div className="mt-5 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onApply}
          disabled={isApplying}
          className="rounded-2xl bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isApplying ? 'Applying...' : 'Apply filters'}
        </button>
        <button
          type="button"
          onClick={onReset}
          className="rounded-2xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:border-slate-600 hover:bg-slate-900"
        >
          Reset
        </button>
      </div>
    </section>
  );
}
