'use client';

import useSWR from 'swr';

import { EmptyState } from '@/components/EmptyState';
import { LoadingState } from '@/components/LoadingState';
import { RequireAuth } from '@/components/RequireAuth';
import { api } from '@/lib/api';
import { formatRelativeDate } from '@/lib/utils';

function renderName(value: unknown) {
  if (typeof value === 'string') return value;
  if (value && typeof value === 'object' && 'name' in (value as Record<string, unknown>)) {
    return String((value as Record<string, unknown>).name);
  }
  return JSON.stringify(value);
}

function MetadataPageContent() {
  const { data, error, isLoading } = useSWR('show-metadata', () => api.getMetadata(), { refreshInterval: 300_000 });

  if (isLoading && !data) {
    return <LoadingState label="Loading metadata..." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg">
        <p className="text-xs uppercase tracking-[0.35em] text-cyan-300">Reference Data</p>
        <h2 className="mt-3 text-3xl font-semibold text-white">MLB 26 Metadata</h2>
        <p className="mt-3 max-w-3xl text-sm text-slate-400">Series, brands, and set labels used to enrich card listings and future search/filter UX throughout StubIQ.</p>
        <p className="mt-4 text-xs text-slate-500">Last fetched {formatRelativeDate(data?.fetched_at)}</p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
          <div className="text-xs uppercase tracking-[0.25em] text-slate-500">Series</div>
          <div className="mt-3 text-3xl font-semibold text-white">{data?.series.length ?? 0}</div>
        </div>
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
          <div className="text-xs uppercase tracking-[0.25em] text-slate-500">Brands</div>
          <div className="mt-3 text-3xl font-semibold text-white">{data?.brands.length ?? 0}</div>
        </div>
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
          <div className="text-xs uppercase tracking-[0.25em] text-slate-500">Sets</div>
          <div className="mt-3 text-3xl font-semibold text-white">{data?.sets.length ?? 0}</div>
        </div>
      </section>

      {data ? (
        <section className="grid gap-6 xl:grid-cols-3">
          {[
            { title: 'Series', items: data.series },
            { title: 'Brands', items: data.brands },
            { title: 'Sets', items: data.sets },
          ].map((group) => (
            <div key={group.title} className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
              <h3 className="text-lg font-semibold text-white">{group.title}</h3>
              <div className="mt-4 space-y-2">
                {group.items.slice(0, 20).map((entry, index) => (
                  <div key={`${group.title}-${index}`} className="rounded-2xl border border-slate-800 bg-slate-950/50 px-4 py-3 text-sm text-slate-300">
                    {renderName(entry)}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </section>
      ) : null}

      {error ? <EmptyState title="Metadata unavailable" description="The backend could not load the cached MLB 26 metadata snapshot." /> : null}
    </div>
  );
}

export default function MetadataPage() {
  return (
    <RequireAuth>
      <MetadataPageContent />
    </RequireAuth>
  );
}
