"""ORM models for MLB The Show API sync artifacts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utcnow

from .domain import Card, TimestampMixin


class MarketListing(TimestampMixin, Base):
    __tablename__ = "market_listings"
    __table_args__ = (UniqueConstraint("item_id", name="uq_market_listings_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String(128), ForeignKey("cards.item_id"), index=True, nullable=False)
    listing_name: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    best_sell_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    best_buy_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    spread: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_profit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    roi_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)

    card: Mapped[Card] = relationship()


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(128), ForeignKey("cards.item_id"), index=True, nullable=False)
    buy_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sell_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)

    card: Mapped[Optional[Card]] = relationship()


class ShowMetadataSnapshot(Base):
    __tablename__ = "show_metadata_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    series_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    brands_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    sets_json: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)


class ShowPlayerProfile(TimestampMixin, Base):
    __tablename__ = "show_player_profiles"
    __table_args__ = (UniqueConstraint("username", name="uq_show_player_profiles_username"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    display_level: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    games_played: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vanity_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    most_played_modes_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    lifetime_hitting_stats_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    lifetime_defensive_stats_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    online_data_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)


class ShowRosterUpdate(TimestampMixin, Base):
    __tablename__ = "show_roster_updates"
    __table_args__ = (UniqueConstraint("remote_id", name="uq_show_roster_updates_remote_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    remote_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)
