export function LoadingState({ label = 'Loading dashboard...' }: { label?: string }) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 text-sm text-slate-300 shadow-lg">
      <div className="flex items-center gap-3">
        <div className="h-3 w-3 animate-pulse rounded-full bg-sky-400" />
        <span>{label}</span>
      </div>
    </div>
  );
}
