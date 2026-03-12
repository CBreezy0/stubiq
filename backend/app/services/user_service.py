"""User profile and per-user settings service."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import User, UserSettings
from app.services.config_store import ConfigStore
from app.utils.enums import AuthProvider
from app.utils.time import utcnow


class UserService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._public_defaults = {
            public_key: float(settings.engine_thresholds[internal_key])
            for public_key, internal_key in ConfigStore.ENGINE_THRESHOLD_PUBLIC_TO_INTERNAL.items()
        }

    def normalize_email(self, email: str) -> str:
        return email.strip().lower()

    def get_user_by_id(self, session: Session, user_id: str) -> Optional[User]:
        return session.get(User, user_id)

    def get_user_by_email(self, session: Session, email: str) -> Optional[User]:
        normalized = self.normalize_email(email)
        return session.scalar(select(User).where(User.email == normalized))

    def get_user_by_google_sub(self, session: Session, google_sub: str) -> Optional[User]:
        return session.scalar(select(User).where(User.google_sub == google_sub))

    def get_user_by_apple_sub(self, session: Session, apple_sub: str) -> Optional[User]:
        return session.scalar(select(User).where(User.apple_sub == apple_sub))

    def create_user(
        self,
        session: Session,
        email: str,
        auth_provider: AuthProvider,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        google_sub: Optional[str] = None,
        apple_sub: Optional[str] = None,
        password_hash: Optional[str] = None,
        is_verified: bool = False,
    ) -> User:
        user = User(
            email=self.normalize_email(email),
            display_name=(display_name or self._default_display_name(email)).strip() or self._default_display_name(email),
            avatar_url=avatar_url,
            auth_provider=auth_provider,
            google_sub=google_sub,
            apple_sub=apple_sub,
            password_hash=password_hash,
            is_active=True,
            is_verified=is_verified,
            last_login_at=utcnow(),
        )
        session.add(user)
        session.flush()
        self.ensure_user_settings(session, user)
        return user

    def ensure_user_settings(self, session: Session, user: User) -> UserSettings:
        settings_row = session.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
        if settings_row is None:
            settings_row = UserSettings(user_id=user.id, **self._public_defaults)
            session.add(settings_row)
            session.flush()
        return settings_row

    def get_public_engine_thresholds(self, session: Session, user: User) -> tuple[dict[str, float], UserSettings]:
        settings_row = self.ensure_user_settings(session, user)
        payload = {
            "floor_buy_margin": float(settings_row.floor_buy_margin),
            "launch_supply_crash_threshold": float(settings_row.launch_supply_crash_threshold),
            "flip_profit_minimum": float(settings_row.flip_profit_minimum),
            "grind_market_edge": float(settings_row.grind_market_edge),
            "collection_lock_penalty": float(settings_row.collection_lock_penalty),
            "gatekeeper_hold_weight": float(settings_row.gatekeeper_hold_weight),
        }
        return payload, settings_row

    def get_engine_thresholds(self, session: Session, user: User) -> dict[str, float]:
        public_payload, _ = self.get_public_engine_thresholds(session, user)
        merged = dict(self.settings.engine_thresholds)
        for public_key, internal_key in ConfigStore.ENGINE_THRESHOLD_PUBLIC_TO_INTERNAL.items():
            merged[internal_key] = float(public_payload[public_key])
        return merged

    def update_engine_thresholds(self, session: Session, user: User, updates: dict[str, float]) -> UserSettings:
        settings_row = self.ensure_user_settings(session, user)
        for field_name, value in updates.items():
            if hasattr(settings_row, field_name):
                setattr(settings_row, field_name, value)
        session.add(settings_row)
        session.flush()
        return settings_row

    def update_profile(self, session: Session, user: User, updates: dict) -> User:
        for field_name, value in updates.items():
            if field_name in {"display_name", "avatar_url"}:
                setattr(user, field_name, value)
        user.updated_at = utcnow()
        session.add(user)
        session.flush()
        return user

    def synthetic_apple_email(self, apple_sub: str) -> str:
        return f"apple-{apple_sub}@users.local"

    def _default_display_name(self, email: str) -> str:
        local_part = email.split("@", 1)[0].replace(".", " ").replace("_", " ").strip()
        return local_part.title() or "Trader"
