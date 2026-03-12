"""Auth audit log service."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models import AuthAuditLog, User
from app.utils.enums import AuthProvider


class AuthAuditService:
    def log(
        self,
        session: Session,
        event_type: str,
        *,
        user: Optional[User] = None,
        user_id: Optional[str] = None,
        auth_provider: Optional[AuthProvider | str] = None,
        success: bool = True,
        device_name: Optional[str] = None,
        platform: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata_json: Optional[dict] = None,
    ) -> None:
        provider_value: Optional[str]
        if isinstance(auth_provider, AuthProvider):
            provider_value = auth_provider.value
        else:
            provider_value = auth_provider

        session.add(
            AuthAuditLog(
                user_id=user.id if user is not None else user_id,
                event_type=event_type,
                auth_provider=provider_value,
                success=success,
                device_name=device_name,
                platform=platform,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata_json=metadata_json or {},
            )
        )
