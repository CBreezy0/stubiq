'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import clsx from 'clsx';

import { useAuth } from '@/context/AuthContext';

const items = [
  { href: '/dashboard', label: 'Dashboard', description: 'Live market view' },
  { href: '/portfolio', label: 'Portfolio', description: 'Owned cards and P/L' },
  { href: '/settings', label: 'Settings', description: 'Tune strategy thresholds' },
];

export function SidebarNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, logout, user } = useAuth();

  const handleLogout = () => {
    logout();
    router.replace('/login');
  };

  return (
    <div className="space-y-4">
      <nav className="flex gap-2 overflow-x-auto md:flex-col md:overflow-visible">
        {items.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                'min-w-[11rem] rounded-2xl border px-4 py-3 transition md:min-w-0',
                active
                  ? 'border-sky-400/40 bg-sky-400/10 text-sky-50 shadow-lg shadow-sky-900/20'
                  : 'border-slate-800 bg-slate-900/70 text-slate-300 hover:border-slate-700 hover:bg-slate-900',
              )}
            >
              <div className="text-sm font-semibold">{item.label}</div>
              <div className="mt-1 text-xs text-slate-400">{item.description}</div>
            </Link>
          );
        })}
      </nav>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
        {isAuthenticated && user ? (
          <>
            <div className="text-xs uppercase tracking-[0.25em] text-sky-300">Session</div>
            <div className="mt-2 font-medium text-white">{user.display_name || user.email}</div>
            <div className="mt-1 text-xs text-slate-400">Signed in with {user.auth_provider}</div>
            <button
              type="button"
              onClick={handleLogout}
              className="mt-4 w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:border-slate-600 hover:bg-slate-900"
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <div className="font-medium text-white">No active session</div>
            <div className="mt-1 text-xs text-slate-400">Sign in to unlock portfolio and settings data.</div>
            <Link
              href="/login"
              className="mt-4 inline-flex w-full items-center justify-center rounded-2xl bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400"
            >
              Go to login
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
