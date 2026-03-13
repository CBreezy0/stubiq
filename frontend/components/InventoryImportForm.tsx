'use client';

import { useMemo, useState } from 'react';

import { useToast } from '@/components/ToastProvider';
import { api } from '@/lib/api';
import type { InventoryImportItem, InventorySummary } from '@/lib/types';

interface InventoryImportFormProps {
  onImported?: (inventory: InventorySummary) => void;
}

const emptyDraft: InventoryImportItem = {
  item_uuid: '',
  quantity: 1,
  is_sellable: true,
  card_name: '',
};

export function InventoryImportForm({ onImported }: InventoryImportFormProps) {
  const [draft, setDraft] = useState<InventoryImportItem>(emptyDraft);
  const [items, setItems] = useState<InventoryImportItem[]>([]);
  const [replaceExisting, setReplaceExisting] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { push } = useToast();

  const canAdd = useMemo(() => draft.item_uuid.trim().length > 0 && draft.quantity > 0, [draft.item_uuid, draft.quantity]);

  const addItem = () => {
    if (!canAdd) return;
    setItems((current) => [
      ...current,
      {
        item_uuid: draft.item_uuid.trim(),
        quantity: draft.quantity,
        is_sellable: draft.is_sellable,
        card_name: draft.card_name?.trim() || undefined,
      },
    ]);
    setDraft(emptyDraft);
  };

  const removeItem = (itemUuid: string) => {
    setItems((current) => current.filter((item) => item.item_uuid !== itemUuid));
  };

  const submit = async () => {
    if (items.length === 0) {
      push({ tone: 'error', title: 'Add at least one card', description: 'Manual import needs one or more inventory rows.' });
      return;
    }
    setIsSubmitting(true);
    try {
      const result = await api.importInventory({ items, replace_existing: replaceExisting });
      push({ tone: 'success', title: 'Inventory imported', description: `${result.imported_count} cards synced into StubIQ.` });
      setItems([]);
      onImported?.(result.inventory);
    } catch (error) {
      push({ tone: 'error', title: 'Import failed', description: error instanceof Error ? error.message : 'Inventory import did not complete.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-amber-300">Manual Import</p>
        <h2 className="mt-3 text-2xl font-semibold text-white">Import inventory</h2>
        <p className="mt-3 text-sm text-slate-400">Use UUIDs from the market scanner until MLB account session automation is connected.</p>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <label className="block text-sm text-slate-300">
          <span className="mb-2 block">Item UUID</span>
          <input
            value={draft.item_uuid}
            onChange={(event) => setDraft({ ...draft, item_uuid: event.target.value })}
            placeholder="live-riley-greene-26"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-sky-400"
          />
        </label>

        <label className="block text-sm text-slate-300">
          <span className="mb-2 block">Card name (optional)</span>
          <input
            value={draft.card_name ?? ''}
            onChange={(event) => setDraft({ ...draft, card_name: event.target.value })}
            placeholder="Riley Greene"
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-sky-400"
          />
        </label>

        <label className="block text-sm text-slate-300">
          <span className="mb-2 block">Quantity</span>
          <input
            type="number"
            min={1}
            value={draft.quantity}
            onChange={(event) => setDraft({ ...draft, quantity: Number(event.target.value) || 1 })}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-sky-400"
          />
        </label>

        <label className="flex items-center gap-3 rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-300">
          <input
            type="checkbox"
            checked={draft.is_sellable}
            onChange={(event) => setDraft({ ...draft, is_sellable: event.target.checked })}
            className="h-4 w-4 rounded border-slate-600 bg-slate-900 text-sky-400"
          />
          Mark as sellable
        </label>
      </div>

      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={addItem}
          disabled={!canAdd}
          className="rounded-2xl bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Add row
        </button>
        <label className="flex items-center gap-3 rounded-2xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-300">
          <input
            type="checkbox"
            checked={replaceExisting}
            onChange={(event) => setReplaceExisting(event.target.checked)}
            className="h-4 w-4 rounded border-slate-600 bg-slate-900 text-sky-400"
          />
          Replace existing inventory
        </label>
      </div>

      <div className="mt-6 space-y-3">
        {items.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-950/40 p-5 text-sm text-slate-400">
            No rows staged yet. Add cards from the market table or your binder notes.
          </div>
        ) : (
          items.map((item) => (
            <div key={item.item_uuid} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-800 bg-slate-950/50 px-4 py-3 text-sm text-slate-300">
              <div>
                <div className="font-medium text-white">{item.card_name || item.item_uuid}</div>
                <div className="text-xs text-slate-500">{item.item_uuid} • Qty {item.quantity} • {item.is_sellable ? 'Sellable' : 'No-sell'}</div>
              </div>
              <button
                type="button"
                onClick={() => removeItem(item.item_uuid)}
                className="rounded-2xl border border-slate-700 px-3 py-1.5 text-xs font-semibold text-white transition hover:border-slate-600 hover:bg-slate-900"
              >
                Remove
              </button>
            </div>
          ))
        )}
      </div>

      <div className="mt-6">
        <button
          type="button"
          onClick={submit}
          disabled={isSubmitting || items.length === 0}
          className="rounded-2xl bg-emerald-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? 'Importing...' : 'Import Inventory'}
        </button>
      </div>
    </div>
  );
}
