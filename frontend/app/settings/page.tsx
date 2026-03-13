'use client';

import { RequireAuth } from '@/components/RequireAuth';
import { ThresholdEditor } from '@/components/ThresholdEditor';

function SettingsContent() {
  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg">
        <p className="text-xs uppercase tracking-[0.35em] text-sky-300">Runtime Controls</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Settings</h1>
        <p className="mt-3 max-w-3xl text-sm text-slate-400">
          Adjust the engine thresholds that shape launch-week floor buying, supply-shock detection, collection locking, and grind-vs-market recommendations.
        </p>
      </section>
      <ThresholdEditor />
    </div>
  );
}

export default function SettingsPage() {
  return (
    <RequireAuth>
      <SettingsContent />
    </RequireAuth>
  );
}
