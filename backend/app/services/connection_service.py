"""Console account connection service."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import User, UserConnection
from app.schemas.connection import ConnectionStartResponse, UserConnectionResponse
from app.services.token_service import TokenService, TokenServiceError
from app.utils.enums import ConnectionProvider, ConnectionStatus
from app.utils.time import utcnow


class ConnectionServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass
class ProviderTokens:
    provider_account_id: str
    display_name: str
    gamertag_or_psn: str
    access_token: str
    refresh_token: Optional[str]
    expires_at: Optional[object]
    mode: str
    metadata_json: dict


class ConnectionService:
    def __init__(self, settings: Settings, token_service: TokenService):
        self.settings = settings
        self.token_service = token_service
        key_material = hashlib.sha256(settings.jwt_secret_key.encode("utf-8")).digest()
        self.fernet = Fernet(base64.urlsafe_b64encode(key_material))

    def list_connections(self, session: Session, user: User) -> list[UserConnectionResponse]:
        rows = {
            row.provider: row
            for row in session.scalars(select(UserConnection).where(UserConnection.user_id == user.id)).all()
        }
        items: list[UserConnectionResponse] = []
        for provider in (ConnectionProvider.XBOX, ConnectionProvider.PLAYSTATION):
            row = rows.get(provider)
            if row is None:
                items.append(
                    UserConnectionResponse(
                        provider=provider,
                        status=ConnectionStatus.NOT_CONNECTED,
                        display_name=None,
                        gamertag_or_psn=None,
                        provider_account_id=None,
                        expires_at=None,
                        metadata_json={"mode": self._default_mode(provider)},
                    )
                )
            else:
                items.append(UserConnectionResponse.from_model(row))
        return items

    def start_connection(self, user: User, provider: ConnectionProvider) -> ConnectionStartResponse:
        mode = self._default_mode(provider)
        if mode == "unconfigured":
            raise ConnectionServiceError(
                f"{provider.value.capitalize()} connection is not configured yet and mock mode is disabled.",
                status_code=503,
            )
        return ConnectionStartResponse(
            provider=provider,
            mode=mode,
            session_token=self.token_service.create_connection_session_token(user.id, provider.value),
            auth_url=None,
            message=(
                f"{provider.value.capitalize()} OAuth scaffold is ready. Submit the provider callback code to the callback endpoint."
                if mode == "oauth_scaffold"
                else f"Mock {provider.value} connection session created. Complete the flow to persist connected state."
            ),
        )

    def complete_connection(
        self,
        session: Session,
        user: User,
        provider: ConnectionProvider,
        session_token: str,
        provider_account_id: Optional[str] = None,
        display_name: Optional[str] = None,
        gamertag_or_psn: Optional[str] = None,
        status: Optional[ConnectionStatus] = None,
        metadata_json: Optional[dict] = None,
    ) -> UserConnectionResponse:
        self._validate_session_token(user, provider, session_token)
        row = self._get_or_create_row(session, user, provider)
        row.provider_account_id = provider_account_id or row.provider_account_id or f"mock-{provider.value}-{user.id[:8]}"
        row.display_name = display_name or row.display_name or user.display_name or user.email.split("@", 1)[0]
        row.gamertag_or_psn = gamertag_or_psn or row.gamertag_or_psn or row.display_name
        row.status = status or ConnectionStatus.CONNECTED
        row.metadata_json = {**(row.metadata_json or {}), **(metadata_json or {}), "mode": "mock"}
        session.add(row)
        session.flush()
        return UserConnectionResponse.from_model(row)

    def handle_callback(
        self,
        session: Session,
        user: User,
        provider: ConnectionProvider,
        code: str,
        session_token: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        metadata_json: Optional[dict] = None,
    ) -> UserConnectionResponse:
        if session_token:
            self._validate_session_token(user, provider, session_token)
        provider_tokens = self._exchange_callback_code(provider, user, code, redirect_uri=redirect_uri)
        row = self._get_or_create_row(session, user, provider)
        row.provider_account_id = provider_tokens.provider_account_id
        row.display_name = provider_tokens.display_name
        row.gamertag_or_psn = provider_tokens.gamertag_or_psn
        row.status = ConnectionStatus.CONNECTED
        row.access_token_encrypted = self._encrypt(provider_tokens.access_token)
        row.refresh_token_encrypted = self._encrypt(provider_tokens.refresh_token) if provider_tokens.refresh_token else None
        row.expires_at = provider_tokens.expires_at
        row.metadata_json = {
            **(row.metadata_json or {}),
            **provider_tokens.metadata_json,
            **(metadata_json or {}),
            "mode": provider_tokens.mode,
        }
        session.add(row)
        session.flush()
        return UserConnectionResponse.from_model(row)

    def disconnect_connection(self, session: Session, user: User, provider: ConnectionProvider) -> UserConnectionResponse:
        row = self._get_or_create_row(session, user, provider)
        row.provider_account_id = None
        row.display_name = None
        row.gamertag_or_psn = None
        row.status = ConnectionStatus.NOT_CONNECTED
        row.access_token_encrypted = None
        row.refresh_token_encrypted = None
        row.expires_at = None
        row.metadata_json = {"disconnected": True, "mode": self._default_mode(provider)}
        session.add(row)
        session.flush()
        return UserConnectionResponse.from_model(row)

    def _get_or_create_row(self, session: Session, user: User, provider: ConnectionProvider) -> UserConnection:
        row = session.scalar(
            select(UserConnection).where(UserConnection.user_id == user.id, UserConnection.provider == provider)
        )
        if row is None:
            row = UserConnection(user_id=user.id, provider=provider, status=ConnectionStatus.NOT_CONNECTED, metadata_json={})
            session.add(row)
            session.flush()
        return row

    def _validate_session_token(self, user: User, provider: ConnectionProvider, session_token: str) -> None:
        try:
            payload = self.token_service.decode_connection_session_token(session_token)
        except TokenServiceError as exc:
            raise ConnectionServiceError(exc.message, status_code=exc.status_code) from exc
        if payload.get("sub") != user.id or payload.get("provider") != provider.value:
            raise ConnectionServiceError("Connection session token does not match the current user or provider.", status_code=401)

    def _exchange_callback_code(
        self,
        provider: ConnectionProvider,
        user: User,
        code: str,
        *,
        redirect_uri: Optional[str] = None,
    ) -> ProviderTokens:
        client_id, client_secret = self._provider_credentials(provider)
        digest = hashlib.sha256(f"{provider.value}:{code}:{user.id}".encode("utf-8")).hexdigest()[:12]
        expires_at = utcnow() + timedelta(days=30)
        if client_id and client_secret:
            return ProviderTokens(
                provider_account_id=f"{provider.value}-acct-{digest}",
                display_name=user.display_name or f"{provider.value.capitalize()} Trader",
                gamertag_or_psn=user.display_name or user.email.split("@", 1)[0],
                access_token=f"{provider.value}-oauth-access-{digest}",
                refresh_token=f"{provider.value}-oauth-refresh-{digest}",
                expires_at=expires_at,
                mode="oauth_scaffold",
                metadata_json={
                    "oauth_exchange": "placeholder",
                    "code_received": True,
                    "redirect_uri": redirect_uri,
                },
            )
        if self.settings.enable_mock_console_connections:
            return ProviderTokens(
                provider_account_id=f"mock-{provider.value}-{digest}",
                display_name=user.display_name or f"{provider.value.capitalize()} Trader",
                gamertag_or_psn=user.display_name or user.email.split("@", 1)[0],
                access_token=f"mock-{provider.value}-access-{digest}",
                refresh_token=f"mock-{provider.value}-refresh-{digest}",
                expires_at=expires_at,
                mode="mock",
                metadata_json={"oauth_exchange": "mock_fallback", "code_received": True},
            )
        raise ConnectionServiceError(f"{provider.value.capitalize()} callback handling is not configured.", status_code=503)

    def _provider_credentials(self, provider: ConnectionProvider) -> tuple[Optional[str], Optional[str]]:
        if provider == ConnectionProvider.XBOX:
            return self.settings.xbox_client_id, self.settings.xbox_client_secret
        return self.settings.playstation_client_id, self.settings.playstation_client_secret

    def _default_mode(self, provider: ConnectionProvider) -> str:
        client_id, client_secret = self._provider_credentials(provider)
        if client_id and client_secret:
            return "oauth_scaffold"
        if self.settings.enable_mock_console_connections:
            return "mock"
        return "unconfigured"

    def _encrypt(self, raw_value: str) -> str:
        return self.fernet.encrypt(raw_value.encode("utf-8")).decode("utf-8")
