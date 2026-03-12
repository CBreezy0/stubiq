"""Console connection schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.utils.enums import ConnectionProvider, ConnectionStatus


class UserConnectionResponse(BaseModel):
    provider: ConnectionProvider
    status: ConnectionStatus
    display_name: Optional[str] = None
    gamertag_or_psn: Optional[str] = None
    provider_account_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    metadata_json: dict = Field(default_factory=dict)

    @classmethod
    def from_model(cls, connection) -> "UserConnectionResponse":
        return cls(
            provider=connection.provider,
            status=connection.status,
            display_name=connection.display_name,
            gamertag_or_psn=connection.gamertag_or_psn,
            provider_account_id=connection.provider_account_id,
            expires_at=connection.expires_at,
            metadata_json=connection.metadata_json or {},
        )


class ConnectionListResponse(BaseModel):
    items: list[UserConnectionResponse]


class ConnectionStartResponse(BaseModel):
    provider: ConnectionProvider
    mode: str
    session_token: str
    auth_url: Optional[str] = None
    message: str


class ConnectionCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_token: str = Field(min_length=1)
    provider_account_id: Optional[str] = Field(default=None, max_length=255)
    display_name: Optional[str] = Field(default=None, max_length=255)
    gamertag_or_psn: Optional[str] = Field(default=None, max_length=255)
    status: Optional[ConnectionStatus] = None
    metadata_json: dict = Field(default_factory=dict)


class ConnectionCallbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    session_token: Optional[str] = Field(default=None, min_length=1)
    redirect_uri: Optional[str] = Field(default=None, max_length=2048)
    metadata_json: dict = Field(default_factory=dict)
