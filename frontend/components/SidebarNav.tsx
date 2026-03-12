'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';

const items = [
  { href: '/dashboard', label: 'Dashboard', description: 'Live market view' },
  { href: '/portfolio', label: 'Portfolio', description: 'Owned cards and P/L' },
  { href: '/settings', label: 'Settings', description: 'Tune strategy thresholds' },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
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
  );
}
