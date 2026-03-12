'use client';

import { useMemo, useState } from 'react';

import { LoadingState } from '@/components/LoadingState';
import { useEngineThresholds } from '@/hooks/useEngineThresholds';
import { useToast } from '@/components/ToastProvider';
import type { EngineThresholdsPatchRequest } from '@/lib/types';

const fieldMeta = [
  {
    key: 'floor_buy_margin',
    label: 'Floor buy margin',
    description: 'How close a card must sit to quicksell or modeled floor before the engine calls it a low-risk buy watch.',
  },
  {
    key: 'launch_supply_crash_threshold',
    label: 'Launch crash threshold',
    description: 'How much post-launch price compression is required before full-launch supply shock logic treats the move as actionable.',
  },
  {
    key: 'flip_profit_minimum',
    label: 'Minimum flip profit',
    description: 'Smallest tax-adjusted stub profit required for a flip to enter the ranked board.',
  },
  {
    key: 'grind_market_edge',
    label: 'Grind vs market edge',
    description: 'Minimum EV/hour advantage gameplay must have before the dashboard recommends grinding instead of working the market.',
  },
  {
    key: 'collection_lock_penalty',
    label: 'Collection lock penalty',
    description: 'How much the collection engine should penalize locking stubs early when liquidity matters more than reward progress.',
  },
  {
    key: 'gatekeeper_hold_weight',
    label: 'Gatekeeper hold weight',
    description: 'Extra protection applied to elite Live Series gatekeepers so the portfolio engine avoids selling them too aggressively.',
  },
] as const;

export function ThresholdEditor() {
  const { data, error, isLoading, save } = useEngineThresholds();
  const { push } = useToast();
  const [form, setForm] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);

  const values = useMemo(() => {
    if (!data) return null;
    return fieldMeta.reduce<Record<string, string>>((accumulator, field) => {
      accumulator[field.key] = form[field.key] ?? String(data[field.key]);
      return accumulator;
    }, {});
  }, [data, form]);

  if (isLoading && !data) return <LoadingState label="Loading engine thresholds..." />;
  if (error || !data || !values) {
    return (
      <div className="rounded-3xl border border-rose-400/30 bg-rose-500/10 p-6 text-sm text-rose-100 shadow-lg">
        Failed to load threshold settings. Make sure the backend is running and the settings route is healthy.
      </div>
    );
  }

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const payload = fieldMeta.reduce<EngineThresholdsPatchRequest>((accumulator, field) => {
        const parsed = Number(values[field.key]);
        if (!Number.isNaN(parsed) && parsed !== data[field.key]) {
          accumulator[field.key] = parsed;
        }
        return accumulator;
      }, {});

      if (Object.keys(payload).length === 0) {
        push({ tone: 'success', title: 'No changes to save', description: 'Threshold values already match the live backend settings.' });
        return;
      }

      const updated = await save(payload);
      setForm({});
      push({ tone: 'success', title: 'Thresholds updated', description: `Live settings saved at ${updated.updated_at ? new Date(updated.updated_at).toLocaleTimeString() : 'just now'}.` });
    } catch (saveError) {
      push({ tone: 'error', title: 'Save failed', description: saveError instanceof Error ? saveError.message : 'Could not update thresholds.' });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg">
      <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Engine Thresholds</h2>
          <p className="mt-1 text-sm text-slate-400">Tune launch-week sensitivity and portfolio posture without restarting the API.</p>
        </div>
        <button
          type="button"
          onClick={handleSave}
          disabled={isSaving}
          className="rounded-2xl bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSaving ? 'Saving...' : 'Save thresholds'}
        </button>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {fieldMeta.map((field) => (
          <label key={field.key} className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
            <div className="text-sm font-medium text-white">{field.label}</div>
            <div className="mt-1 text-sm text-slate-400">{field.description}</div>
            <input
              type="number"
              step="0.01"
              value={values[field.key]}
              onChange={(event) => setForm((current) => ({ ...current, [field.key]: event.target.value }))}
              className="mt-4 w-full rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none ring-0 transition focus:border-sky-400"
            />
            <div className="mt-2 text-xs text-slate-500">Current live value: {String(data[field.key])}</div>
          </label>
        ))}
      </div>
    </div>
  );
}
