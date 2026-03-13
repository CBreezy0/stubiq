import { MarketListingsTable } from '@/components/MarketListingsTable';
import type { FlipOpportunity } from '@/lib/types';

export function FlipTable({ title, items }: { title: string; items: FlipOpportunity[] }) {
  return (
    <MarketListingsTable
      title={title}
      items={items}
      variant="flips"
      emptyTitle={`No ${title.toLowerCase()} yet`}
      emptyDescription="The live listing cache has not surfaced any positive-ROI flips yet."
    />
  );
}
