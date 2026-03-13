'use client';

import Link from 'next/link';

import { EmptyState } from '@/components/EmptyState';
import type { InventoryItem } from '@/lib/types';
import { formatRelativeDate, formatSignedStubs, formatStubs, toneClasses } from '@/lib/utils';

export function InventoryTable({ items }: { items: InventoryItem[] }) {
  if (items.length === 0) {
    return <EmptyState title="No imported inventory" description="Use manual inventory import until SDS authentication automation is wired in." />;
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/70 shadow-lg">
      <div className="border-b border-slate-800 px-5 py-4">
        <h3 className="text-lg font-semibold text-white">Imported Inventory</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-950/50 text-left text-slate-400">
            <tr>
              <th className="px-5 py-3 font-medium">Card</th>
              <th className="px-5 py-3 font-medium">Qty</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium">Current price</th>
              <th className="px-5 py-3 font-medium">Total value</th>
              <th className="px-5 py-3 font-medium">P/L</th>
              <th className="px-5 py-3 font-medium">Synced</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={`${item.item_uuid}-${item.synced_at}`} className="border-t border-slate-800/80 text-slate-200">
                <td className="px-5 py-4">
                  <Link href={`/cards/${item.item_uuid}`} className="font-medium text-white transition hover:text-sky-300">
                    {item.card.name}
                  </Link>
                  <div className="text-xs text-slate-500">
                    {item.card.team ?? 'MLB'} • {item.card.series ?? 'Unknown series'} • {item.card.rarity ?? 'Unknown rarity'}
                  </div>
                </td>
                <td className="px-5 py-4">{item.quantity}</td>
                <td className="px-5 py-4">
                  <span className={toneClasses(item.is_sellable ? 'emerald' : 'amber')}>{item.is_sellable ? 'Sellable' : 'No-sell'}</span>
                </td>
                <td className="px-5 py-4">{formatStubs(item.current_price)}</td>
                <td className="px-5 py-4">{formatStubs(item.total_value)}</td>
                <td className={`px-5 py-4 ${item.profit_loss != null && item.profit_loss >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
                  {formatSignedStubs(item.profit_loss)}
                </td>
                <td className="px-5 py-4 text-xs text-slate-400">{formatRelativeDate(item.synced_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
