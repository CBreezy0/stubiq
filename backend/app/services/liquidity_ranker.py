"""Liquidity ranking helpers for prioritizing active marketplace cards."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import ListingsSnapshot
from app.utils.time import utcnow


class LiquidityRanker:
    """Ranks cards by recent market activity using recorded snapshot frequency."""

    @staticmethod
    def get_top_liquid_cards(session: Session, limit: int = 200) -> list[str]:
        """Return item ids with the most snapshot activity in the last hour."""

        one_hour_ago = utcnow() - timedelta(hours=1)
        rows = session.execute(
            select(
                ListingsSnapshot.item_id,
                func.count(ListingsSnapshot.id).label("activity"),
            )
            .where(ListingsSnapshot.observed_at >= one_hour_ago)
            .group_by(ListingsSnapshot.item_id)
            .order_by(desc("activity"), ListingsSnapshot.item_id.asc())
            .limit(limit)
        ).all()
        return [str(row.item_id) for row in rows]
