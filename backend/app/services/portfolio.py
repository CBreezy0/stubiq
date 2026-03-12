"""Portfolio import and position management."""

from __future__ import annotations

import csv
import io
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Card, PortfolioPosition, Transaction, User
from app.utils.enums import TransactionAction
from app.utils.scoring import safe_int
from app.utils.time import utcnow


class PortfolioService:
    """Handles manual and CSV-based portfolio management."""

    def __init__(self, market_data_service):
        self.market_data_service = market_data_service

    def list_positions(self, session: Session, user: Optional[User] = None) -> List[PortfolioPosition]:
        if user is None:
            return []
        positions = session.scalars(
            select(PortfolioPosition)
            .where(PortfolioPosition.user_id == user.id)
            .order_by(PortfolioPosition.updated_at.desc())
        ).all()
        if not positions:
            return []
        snapshots = self.market_data_service.get_latest_snapshots(session)
        item_ids = [position.item_id for position in positions]
        cards = {
            card.item_id: card
            for card in session.scalars(select(Card).where(Card.item_id.in_(item_ids))).all()
        }
        for position in positions:
            snapshot = snapshots.get(position.item_id)
            card = cards.get(position.item_id)
            if snapshot and snapshot.best_sell_order is not None:
                position.current_market_value = snapshot.best_sell_order
            elif card and card.quicksell_value is not None:
                position.current_market_value = card.quicksell_value
            if card and card.quicksell_value is not None:
                position.quicksell_value = card.quicksell_value
            if position.duplicate_count < 0:
                position.duplicate_count = 0
        return positions

    def manual_add(
        self,
        session: Session,
        user: User,
        item_id: str,
        card_name: str,
        quantity: int,
        avg_acquisition_cost: int,
        locked_for_collection: bool,
        source: str,
    ) -> PortfolioPosition:
        card = session.scalar(select(Card).where(Card.item_id == item_id))
        if card is None:
            card = Card(
                item_id=item_id,
                name=card_name,
                series="Manual",
                is_live_series=False,
                quicksell_value=0,
                metadata_json={"seeded": False, "source": "manual_portfolio"},
            )
            session.add(card)
            session.flush()

        position = session.scalar(
            select(PortfolioPosition).where(
                PortfolioPosition.user_id == user.id,
                PortfolioPosition.item_id == item_id,
            )
        )
        if position is None:
            position = PortfolioPosition(
                user_id=user.id,
                item_id=item_id,
                card_name=card_name,
                quantity=quantity,
                avg_acquisition_cost=avg_acquisition_cost,
            )
        else:
            total_cost = position.quantity * position.avg_acquisition_cost + quantity * avg_acquisition_cost
            position.quantity += quantity
            position.avg_acquisition_cost = int(total_cost / position.quantity)
        snapshot = self.market_data_service.get_latest_snapshots(session).get(item_id)
        position.card_name = card_name
        position.locked_for_collection = locked_for_collection or position.locked_for_collection
        position.source = source
        position.duplicate_count = max(position.quantity - 1, 0)
        if snapshot and snapshot.best_sell_order is not None:
            position.current_market_value = snapshot.best_sell_order
        else:
            position.current_market_value = position.current_market_value or card.quicksell_value
        position.quicksell_value = card.quicksell_value
        session.add(position)
        session.add(
            Transaction(
                user_id=user.id,
                item_id=item_id,
                action=TransactionAction.IMPORT if source == "csv" else TransactionAction.BUY,
                quantity=quantity,
                unit_price=avg_acquisition_cost,
                total_value=quantity * avg_acquisition_cost,
                transaction_time=utcnow(),
                notes=f"Portfolio add via {source}",
            )
        )
        return position

    def manual_remove(
        self,
        session: Session,
        user: User,
        item_id: str,
        quantity: int,
        remove_all: bool,
    ) -> Optional[PortfolioPosition]:
        position = session.scalar(
            select(PortfolioPosition).where(
                PortfolioPosition.user_id == user.id,
                PortfolioPosition.item_id == item_id,
            )
        )
        if position is None:
            return None
        removed_quantity = position.quantity if remove_all else min(position.quantity, quantity)
        unit_price = position.current_market_value or position.avg_acquisition_cost
        session.add(
            Transaction(
                user_id=user.id,
                item_id=item_id,
                action=TransactionAction.REMOVE,
                quantity=removed_quantity,
                unit_price=unit_price,
                total_value=removed_quantity * unit_price,
                transaction_time=utcnow(),
                notes="Manual portfolio removal" if remove_all or removed_quantity >= position.quantity else "Manual partial portfolio removal",
            )
        )
        if remove_all or removed_quantity >= position.quantity:
            session.delete(position)
            return None
        position.quantity -= removed_quantity
        position.duplicate_count = max(position.quantity - 1, 0)
        session.add(position)
        return position

    def import_csv(self, session: Session, user: User, file_bytes: bytes) -> Dict[str, object]:
        imported = 0
        skipped = 0
        errors: List[str] = []
        content = file_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        if reader.fieldnames is None:
            return {"imported_count": 0, "skipped_count": 0, "errors": ["CSV header row is required."]}

        for index, row in enumerate(reader, start=2):
            item_id = (row.get("item_id") or "").strip()
            card_name = (row.get("card_name") or item_id).strip()
            quantity = safe_int(row.get("quantity"))
            avg_acquisition_cost = safe_int(row.get("avg_acquisition_cost"))
            locked_for_collection = str(row.get("locked_for_collection") or "").strip().lower() in {"1", "true", "yes", "y"}
            source = (row.get("source") or "csv").strip() or "csv"

            if not item_id:
                skipped += 1
                errors.append(f"Row {index}: item_id is required.")
                continue
            if quantity <= 0:
                skipped += 1
                errors.append(f"Row {index}: quantity must be greater than zero.")
                continue
            if avg_acquisition_cost < 0:
                skipped += 1
                errors.append(f"Row {index}: avg_acquisition_cost cannot be negative.")
                continue

            self.manual_add(
                session,
                user=user,
                item_id=item_id,
                card_name=card_name,
                quantity=quantity,
                avg_acquisition_cost=avg_acquisition_cost,
                locked_for_collection=locked_for_collection,
                source=source,
            )
            imported += 1
        return {"imported_count": imported, "skipped_count": skipped, "errors": errors}
