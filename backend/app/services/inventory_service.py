"""User inventory read/import service."""

from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models import Card, MarketListing, PortfolioPosition, User, UserInventory
from app.schemas.cards import CardSummaryResponse
from app.schemas.inventory import InventoryImportItemRequest, InventoryResponse, InventoryItemResponse
from app.services.market_data import MarketDataService
from app.utils.time import utcnow


class InventoryService:
    """Stores user inventory holdings and maps them to live market prices."""

    def __init__(self, market_data_service: MarketDataService):
        self.market_data_service = market_data_service

    def get_inventory(self, session: Session, user: User) -> InventoryResponse:
        rows = session.scalars(
            select(UserInventory)
            .where(UserInventory.user_id == user.id)
            .options(selectinload(UserInventory.card))
            .order_by(UserInventory.synced_at.desc(), UserInventory.item_uuid.asc())
        ).all()
        item_ids = [row.item_uuid for row in rows]
        listing_map = self._current_listing_map(session, item_ids)
        snapshot_map = self.market_data_service.get_latest_snapshots(session)
        position_map = {
            position.item_id: position
            for position in session.scalars(
                select(PortfolioPosition).where(PortfolioPosition.user_id == user.id).where(PortfolioPosition.item_id.in_(item_ids))
            ).all()
        } if item_ids else {}

        items: list[InventoryItemResponse] = []
        total_value = 0
        total_profit_loss = 0
        total_quantity = 0

        for row in rows:
            card = row.card or self._placeholder_card(row.item_uuid)
            listing = listing_map.get(row.item_uuid)
            snapshot = snapshot_map.get(row.item_uuid)
            current_price = None
            if listing is not None and listing.best_sell_price is not None:
                current_price = listing.best_sell_price
            elif snapshot is not None:
                current_price = snapshot.best_sell_order or snapshot.buy_now
            total_item_value = (current_price * row.quantity) if current_price is not None else None

            cost_basis = None
            position = position_map.get(row.item_uuid)
            if position is not None:
                cost_basis = position.avg_acquisition_cost * row.quantity
            profit_loss = (total_item_value - cost_basis) if total_item_value is not None and cost_basis is not None else None

            total_quantity += row.quantity
            total_value += total_item_value or 0
            total_profit_loss += profit_loss or 0
            items.append(
                InventoryItemResponse(
                    item_uuid=row.item_uuid,
                    card=self._card_summary(card, snapshot),
                    quantity=row.quantity,
                    is_sellable=row.is_sellable,
                    synced_at=row.synced_at,
                    current_price=current_price,
                    total_value=total_item_value,
                    profit_loss=profit_loss,
                )
            )

        return InventoryResponse(
            count=len(items),
            total_quantity=total_quantity,
            total_market_value=total_value,
            total_profit_loss=total_profit_loss,
            items=items,
        )

    def import_inventory(
        self,
        session: Session,
        user: User,
        items: Iterable[InventoryImportItemRequest],
        replace_existing: bool = True,
    ) -> dict:
        normalized_items = list(items)
        if replace_existing:
            session.execute(delete(UserInventory).where(UserInventory.user_id == user.id))

        now = utcnow()
        imported_count = 0
        for entry in normalized_items:
            card = session.scalar(select(Card).where(Card.item_id == entry.item_uuid))
            if card is None:
                card = Card(
                    item_id=entry.item_uuid,
                    name=entry.card_name or entry.item_uuid,
                    is_live_series=False,
                    quicksell_value=0,
                    metadata_json={"source": "manual_inventory_import"},
                )
                session.add(card)
                session.flush()

            row = session.scalar(
                select(UserInventory)
                .where(UserInventory.user_id == user.id)
                .where(UserInventory.item_uuid == entry.item_uuid)
            )
            if row is None:
                row = UserInventory(user_id=user.id, item_uuid=entry.item_uuid)
            row.quantity = entry.quantity
            row.is_sellable = entry.is_sellable
            row.synced_at = now
            session.add(row)
            imported_count += 1

        session.flush()
        return {
            "imported_count": imported_count,
            "replaced_existing": replace_existing,
            "inventory": self.get_inventory(session, user),
        }

    def _current_listing_map(self, session: Session, item_ids: list[str]) -> dict[str, MarketListing]:
        if not item_ids:
            return {}
        rows = session.scalars(select(MarketListing).where(MarketListing.item_id.in_(item_ids))).all()
        return {row.item_id: row for row in rows}

    def _card_summary(self, card: Card, snapshot) -> CardSummaryResponse:
        return CardSummaryResponse(
            item_id=card.item_id,
            name=card.name,
            series=card.series,
            team=card.team,
            division=card.division,
            league=card.league,
            overall=card.overall,
            rarity=card.rarity,
            display_position=card.display_position,
            is_live_series=card.is_live_series,
            quicksell_value=card.quicksell_value,
            latest_buy_now=snapshot.buy_now if snapshot is not None else None,
            latest_sell_now=snapshot.sell_now if snapshot is not None else None,
            latest_best_buy_order=snapshot.best_buy_order if snapshot is not None else None,
            latest_best_sell_order=snapshot.best_sell_order if snapshot is not None else None,
            latest_tax_adjusted_spread=snapshot.tax_adjusted_spread if snapshot is not None else None,
            observed_at=snapshot.observed_at if snapshot is not None else None,
        )

    def _placeholder_card(self, item_uuid: str) -> Card:
        return Card(
            item_id=item_uuid,
            name=item_uuid,
            is_live_series=False,
            quicksell_value=0,
            metadata_json={},
        )
