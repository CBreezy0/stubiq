import { buildLaunchAlerts, marketPhaseLabels } from '@/lib/utils';
import type { MarketPhaseResponse } from '@/lib/types';

export function MarketPhaseBanner({ phase }: { phase: MarketPhaseResponse | null | undefined }) {
  const alerts = buildLaunchAlerts(phase);
  if (!phase) return null;

  return (
    <section className="rounded-3xl border border-sky-400/20 bg-gradient-to-br from-sky-500/10 via-slate-900/80 to-violet-500/10 p-6 shadow-xl backdrop-blur">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-sky-300">Current Market Phase</p>
          <h2 className="mt-2 text-3xl font-semibold text-white">{marketPhaseLabels[phase.phase]}</h2>
          <p className="mt-3 max-w-3xl text-sm text-slate-300">{phase.rationale}</p>
        </div>
        <div className="rounded-2xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-slate-300">
          <div className="font-medium text-white">Detection confidence</div>
          <div className="mt-1 text-2xl font-semibold text-sky-200">{Math.round(phase.confidence)}%</div>
          <div className="mt-2 text-xs text-slate-500">Updated {new Date(phase.detected_at).toLocaleString()}</div>
        </div>
      </div>
      {alerts.length > 0 ? (
        <div className="mt-5 flex flex-col gap-3">
          {alerts.map((alert) => (
            <div key={alert} className="rounded-2xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
              {alert}
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
