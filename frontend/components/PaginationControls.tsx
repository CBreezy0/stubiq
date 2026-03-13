'use client';

interface PaginationControlsProps {
  page: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export function PaginationControls({ page, totalPages, totalItems, pageSize, onPageChange }: PaginationControlsProps) {
  if (totalItems <= pageSize) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-3xl border border-slate-800 bg-slate-900/70 px-5 py-4 shadow-lg">
      <div className="text-sm text-slate-400">
        Page <span className="font-semibold text-white">{page}</span> of <span className="font-semibold text-white">{totalPages}</span>
      </div>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="rounded-2xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:border-slate-600 hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Previous
        </button>
        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="rounded-2xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:border-slate-600 hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}
