import type { RecommendationAction } from '@/lib/types';
import { actionBadgeClass } from '@/lib/utils';

export function StatusBadge({ action }: { action: RecommendationAction }) {
  return <span className={actionBadgeClass(action)}>{action}</span>;
}
