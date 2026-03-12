"""Console account connection models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.domain import TimestampMixin
from app.utils.enums import ConnectionProvider, ConnectionStatus


class UserConnection(TimestampMixin, Base):
    __tablename__ = "user_connections"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_connection_user_provider"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    provider: Mapped[ConnectionProvider] = mapped_column(Enum(ConnectionProvider), index=True, nullable=False)
    provider_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gamertag_or_psn: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[ConnectionStatus] = mapped_column(Enum(ConnectionStatus), index=True, nullable=False, default=ConnectionStatus.NOT_CONNECTED)
    access_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    user: Mapped["User"] = relationship(back_populates="connections")
