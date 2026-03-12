"""Authentication dependencies for FastAPI routes."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.token_service import TokenServiceError


_optional_bearer = HTTPBearer(auto_error=False)
_required_bearer = HTTPBearer(auto_error=True)


def get_token_service(request: Request):
    return request.app.state.token_service


def get_user_service(request: Request):
    return request.app.state.user_service


def get_auth_service(request: Request):
    return request.app.state.auth_service


def get_connection_service(request: Request):
    return request.app.state.connection_service


def get_auth_rate_limiter(request: Request):
    return request.app.state.auth_rate_limiter


def auth_rate_limit(
    request: Request,
    limiter=Depends(get_auth_rate_limiter),
):
    settings = request.app.state.settings
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",", 1)[0].strip()
    elif request.client is not None:
        client_ip = request.client.host
    else:
        client_ip = "unknown"
    key = f"{request.url.path}:{client_ip}"
    allowed, retry_after = limiter.check(
        key,
        limit=settings.auth_rate_limit_max_requests,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again shortly.",
            headers={"Retry-After": str(retry_after)},
        )


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_optional_bearer),
    db: Session = Depends(get_db),
    token_service=Depends(get_token_service),
    user_service=Depends(get_user_service),
):
    if credentials is None:
        return None
    try:
        payload = token_service.decode_access_token(credentials.credentials)
    except TokenServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    user = user_service.get_user_by_id(db, payload.get("sub", ""))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated user no longer exists.")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_required_bearer),
    db: Session = Depends(get_db),
    token_service=Depends(get_token_service),
    user_service=Depends(get_user_service),
):
    try:
        payload = token_service.decode_access_token(credentials.credentials)
    except TokenServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    user = user_service.get_user_by_id(db, payload.get("sub", ""))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated user no longer exists.")
    return user


def require_active_user(current_user=Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This user account is inactive.")
    return current_user
