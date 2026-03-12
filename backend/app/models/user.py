"""User and user settings models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.domain import TimestampMixin
from app.utils.enums import AuthProvider


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    auth_provider: Mapped[AuthProvider] = mapped_column(Enum(AuthProvider), index=True, nullable=False, default=AuthProvider.EMAIL)
    google_sub: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    apple_sub: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    settings: Mapped["UserSettings"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    connections: Mapped[list["UserConnection"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    portfolio_positions: Mapped[list["PortfolioPosition"]] = relationship(back_populates="user")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")


class UserSettings(TimestampMixin, Base):
    __tablename__ = "user_settings"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_settings_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    floor_buy_margin: Mapped[float] = mapped_column(Float, nullable=False, default=0.08)
    launch_supply_crash_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.18)
    flip_profit_minimum: Mapped[float] = mapped_column(Float, nullable=False, default=250.0)
    grind_market_edge: Mapped[float] = mapped_column(Float, nullable=False, default=0.05)
    collection_lock_penalty: Mapped[float] = mapped_column(Float, nullable=False, default=15.0)
    gatekeeper_hold_weight: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)

    user: Mapped[User] = relationship(back_populates="settings")
