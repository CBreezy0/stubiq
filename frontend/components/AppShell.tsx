'use client';

import { usePathname } from 'next/navigation';

import { SidebarNav } from '@/components/SidebarNav';

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  if (pathname === '/login') {
    return <div className="min-h-screen">{children}</div>;
  }

  return (
    <div className="min-h-screen">
      <div className="mx-auto grid min-h-screen max-w-[1600px] grid-cols-1 gap-6 px-4 py-4 sm:px-6 lg:grid-cols-[280px_minmax(0,1fr)] lg:px-8 lg:py-8">
        <aside className="rounded-3xl border border-slate-800 bg-slate-950/70 p-4 shadow-2xl backdrop-blur lg:sticky lg:top-8 lg:h-[calc(100vh-4rem)]">
          <div className="mb-6">
            <p className="text-xs uppercase tracking-[0.35em] text-sky-300">Diamond Dynasty</p>
            <h1 className="mt-3 text-2xl font-semibold text-white">Market Intel</h1>
            <p className="mt-2 text-sm text-slate-400">Launch-week decisions, portfolio management, and strategy tuning without Swagger.</p>
          </div>
          <SidebarNav />
          <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
            <div className="font-medium text-white">Live backend</div>
            <div className="mt-1 text-slate-400">Reads data from your deployed FastAPI API and refreshes automatically while you play.</div>
          </div>
        </aside>
        <main className="min-w-0">{children}</main>
      </div>
    </div>
  );
}
