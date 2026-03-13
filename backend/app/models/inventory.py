"""User inventory models for manual and future SDS-backed syncs."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utcnow

from .domain import Card


class UserInventory(Base):
    __tablename__ = "user_inventory"
    __table_args__ = (UniqueConstraint("user_id", "item_uuid", name="uq_user_inventory_user_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    item_uuid: Mapped[str] = mapped_column(String(128), ForeignKey("cards.item_id"), index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_sellable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="inventory_items")
    card: Mapped[Optional[Card]] = relationship()
