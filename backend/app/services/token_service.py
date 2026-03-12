"""Access token and refresh token service."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import RefreshToken, User
from app.security.jwt import JWTError, decode_jwt, encode_jwt
from app.services.auth_audit import AuthAuditService
from app.utils.time import utcnow


class TokenServiceError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    refresh_token_hash: str
    access_token_expires_in: int
    refresh_token_expires_in: int


def _normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class TokenService:
    def __init__(self, settings: Settings, audit_service: AuthAuditService):
        self.settings = settings
        self.audit_service = audit_service
        self.access_expiry = timedelta(minutes=settings.access_token_expire_minutes)
        self.refresh_expiry = timedelta(days=settings.refresh_token_expire_days)
        self.jwt_secret = settings.jwt_secret_key
        self.refresh_secret = settings.jwt_refresh_secret_key or settings.jwt_secret_key

    def create_access_token(self, user: User) -> str:
        return encode_jwt(
            {
                "sub": user.id,
                "email": user.email,
                "auth_provider": user.auth_provider.value,
                "type": "access",
                "jti": secrets.token_urlsafe(8),
            },
            self.jwt_secret,
            self.access_expiry,
        )

    def decode_access_token(self, token: str) -> dict:
        try:
            payload = decode_jwt(token, self.jwt_secret)
        except JWTError as exc:
            raise TokenServiceError("Invalid or expired access token.", status_code=401) from exc
        if payload.get("type") != "access":
            raise TokenServiceError("Invalid access token.", status_code=401)
        return payload

    def create_connection_session_token(self, user_id: str, provider: str) -> str:
        return encode_jwt(
            {
                "sub": user_id,
                "provider": provider,
                "type": "connection_session",
            },
            self.jwt_secret,
            timedelta(minutes=15),
        )

    def decode_connection_session_token(self, token: str) -> dict:
        try:
            payload = decode_jwt(token, self.jwt_secret)
        except JWTError as exc:
            raise TokenServiceError("Invalid or expired connection session token.", status_code=401) from exc
        if payload.get("type") != "connection_session":
            raise TokenServiceError("Invalid connection session token.", status_code=401)
        return payload

    def issue_token_pair(
        self,
        session: Session,
        user: User,
        device_name: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> TokenPair:
        raw_refresh_token = secrets.token_urlsafe(48)
        refresh_token_hash = self.hash_refresh_token(raw_refresh_token)
        refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            replaced_by_token_hash=None,
            expires_at=utcnow() + self.refresh_expiry,
            revoked_at=None,
            reuse_detected_at=None,
            created_at=utcnow(),
            device_name=device_name,
            platform=platform,
        )
        session.add(refresh_record)
        return TokenPair(
            access_token=self.create_access_token(user),
            refresh_token=raw_refresh_token,
            refresh_token_hash=refresh_token_hash,
            access_token_expires_in=int(self.access_expiry.total_seconds()),
            refresh_token_expires_in=int(self.refresh_expiry.total_seconds()),
        )

    def refresh(
        self,
        session: Session,
        raw_refresh_token: str,
        device_name: Optional[str] = None,
        platform: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[User, TokenPair]:
        token_row = self._get_refresh_token(session, raw_refresh_token)
        if token_row.revoked_at is not None:
            self._handle_reuse_attempt(session, token_row, ip_address=ip_address, user_agent=user_agent)
            raise TokenServiceError("Refresh token has already been revoked.", status_code=401)
        if _normalize_utc(token_row.expires_at) <= utcnow():
            raise TokenServiceError("Refresh token has expired.", status_code=401)
        user = token_row.user
        if user is None:
            raise TokenServiceError("Authenticated user no longer exists.", status_code=401)
        if not user.is_active:
            raise TokenServiceError("This account is inactive.", status_code=403)
        replacement = self.issue_token_pair(session, user, device_name=device_name, platform=platform)
        token_row.revoked_at = utcnow()
        token_row.replaced_by_token_hash = replacement.refresh_token_hash
        session.add(token_row)
        return user, replacement

    def revoke(self, session: Session, raw_refresh_token: str) -> bool:
        token_row = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == self.hash_refresh_token(raw_refresh_token)))
        if token_row is None:
            return False
        if token_row.revoked_at is None:
            token_row.revoked_at = utcnow()
            session.add(token_row)
        return True

    def revoke_all_for_user(self, session: Session, user: User) -> int:
        active_tokens = session.scalars(
            select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        ).all()
        now = utcnow()
        for token_row in active_tokens:
            token_row.revoked_at = now
            session.add(token_row)
        return len(active_tokens)

    def hash_refresh_token(self, raw_refresh_token: str) -> str:
        digest = hmac.new(self.refresh_secret.encode("utf-8"), raw_refresh_token.encode("utf-8"), hashlib.sha256)
        return digest.hexdigest()

    def _get_refresh_token(self, session: Session, raw_refresh_token: str) -> RefreshToken:
        token_row = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == self.hash_refresh_token(raw_refresh_token)))
        if token_row is None:
            raise TokenServiceError("Refresh token is invalid.", status_code=401)
        return token_row

    def _handle_reuse_attempt(
        self,
        session: Session,
        token_row: RefreshToken,
        *,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        if token_row.user is None:
            return
        now = utcnow()
        if token_row.reuse_detected_at is None:
            token_row.reuse_detected_at = now
            session.add(token_row)
        revoked_count = self.revoke_all_for_user(session, token_row.user)
        self.audit_service.log(
            session,
            "refresh_token_reuse_detected",
            user=token_row.user,
            auth_provider=token_row.user.auth_provider,
            success=False,
            device_name=token_row.device_name,
            platform=token_row.platform,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json={
                "revoked_active_tokens": revoked_count,
                "token_created_at": token_row.created_at.isoformat() if token_row.created_at else None,
            },
        )
