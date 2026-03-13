"""Precomputed analytics cache tables for read-heavy market endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.enums import MarketPhase
from app.utils.time import utcnow

from .domain import Card


class TopFlip(Base):
    __tablename__ = "top_flips"
    __table_args__ = (UniqueConstraint("item_id", name="uq_top_flips_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String(128), ForeignKey("cards.item_id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    buy_price: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    sell_price: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    profit: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    roi: Mapped[Optional[float]] = mapped_column(Float, index=True, nullable=True)
    profit_per_min: Mapped[Optional[float]] = mapped_column(Float, index=True, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, index=True, nullable=False)

    card: Mapped[Optional[Card]] = relationship()


class MarketMoverCache(Base):
    __tablename__ = "market_movers"
    __table_args__ = (UniqueConstraint("item_id", name="uq_market_movers_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String(128), ForeignKey("cards.item_id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    current_price: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    previous_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    change_percent: Mapped[Optional[float]] = mapped_column(Float, index=True, nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, index=True, nullable=False)

    card: Mapped[Optional[Card]] = relationship()


class FloorOpportunity(Base):
    __tablename__ = "floor_opportunities"
    __table_args__ = (UniqueConstraint("item_id", name="uq_floor_opportunities_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String(128), ForeignKey("cards.item_id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    floor_price: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    expected_value: Mapped[Optional[float]] = mapped_column(Float, index=True, nullable=True)
    roi: Mapped[Optional[float]] = mapped_column(Float, index=True, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, index=True, nullable=False)

    card: Mapped[Optional[Card]] = relationship()


class MarketPhaseCache(Base):
    __tablename__ = "market_phase"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phase: Mapped[MarketPhase] = mapped_column(Enum(MarketPhase), index=True, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, index=True, nullable=False)
