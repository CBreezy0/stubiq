"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import (
    AppleAuthRequest,
    AuthTokenResponse,
    GoogleAuthRequest,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    SessionRevocationResponse,
    SignupRequest,
)
from app.schemas.user import UserResponse
from app.security.deps import auth_rate_limit, get_auth_service, require_active_user
from app.services.auth_service import AuthError, AuthRequestContext

router = APIRouter(prefix="/auth", tags=["auth"])


def _preflight_headers(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    origin = request.headers.get("origin")
    request_headers = request.headers.get("access-control-request-headers", "*")

    allowed_origin = "*"
    allowed_origins = tuple(getattr(settings, "cors_allow_origins", ()) or ())
    if origin and ("*" in allowed_origins or origin in allowed_origins):
        allowed_origin = origin
    elif not origin and "*" not in allowed_origins and allowed_origins:
        allowed_origin = allowed_origins[0]

    return {
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
        "Access-Control-Allow-Headers": request_headers or "*",
        "Access-Control-Max-Age": "600",
        "Vary": "Origin",
    }


@router.options("/{auth_path:path}", include_in_schema=False)
def auth_preflight(auth_path: str, request: Request):
    return Response(status_code=status.HTTP_200_OK, headers=_preflight_headers(request))


def _context(request: Request, *, device_name: str | None = None, platform: str | None = None) -> AuthRequestContext:
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",", 1)[0].strip()
    elif request.client is not None:
        client_ip = request.client.host
    else:
        client_ip = None
    return AuthRequestContext(
        device_name=device_name,
        platform=platform,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/signup", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(auth_rate_limit)])
def signup(
    payload: SignupRequest,
    request: Request,
    db: Session = Depends(get_db),
    auth_service=Depends(get_auth_service),
):
    try:
        response = auth_service.signup(
            db,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
            context=_context(request, device_name=payload.device_name, platform=payload.platform),
        )
        db.commit()
        return response
    except AuthError as exc:
        if exc.commit_state:
            db.commit()
        else:
            db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/login", response_model=AuthTokenResponse, dependencies=[Depends(auth_rate_limit)])
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    auth_service=Depends(get_auth_service),
):
    try:
        response = auth_service.login(
            db,
            email=payload.email,
            password=payload.password,
            context=_context(request, device_name=payload.device_name, platform=payload.platform),
        )
        db.commit()
        return response
    except AuthError as exc:
        if exc.commit_state:
            db.commit()
        else:
            db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/google", response_model=AuthTokenResponse, dependencies=[Depends(auth_rate_limit)])
def google_sign_in(
    payload: GoogleAuthRequest,
    request: Request,
    db: Session = Depends(get_db),
    auth_service=Depends(get_auth_service),
):
    try:
        response = auth_service.authenticate_google(
            db,
            raw_id_token=payload.id_token,
            context=_context(request, device_name=payload.device_name, platform=payload.platform),
        )
        db.commit()
        return response
    except AuthError as exc:
        if exc.commit_state:
            db.commit()
        else:
            db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/apple", response_model=AuthTokenResponse, dependencies=[Depends(auth_rate_limit)])
def apple_sign_in(
    payload: AppleAuthRequest,
    request: Request,
    db: Session = Depends(get_db),
    auth_service=Depends(get_auth_service),
):
    try:
        response = auth_service.authenticate_apple(
            db,
            identity_token=payload.identity_token,
            authorization_code=payload.authorization_code,
            context=_context(request, device_name=payload.device_name, platform=payload.platform),
        )
        db.commit()
        return response
    except AuthError as exc:
        if exc.commit_state:
            db.commit()
        else:
            db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/refresh", response_model=AuthTokenResponse, dependencies=[Depends(auth_rate_limit)])
def refresh(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
    auth_service=Depends(get_auth_service),
):
    try:
        response = auth_service.refresh(
            db,
            refresh_token=payload.refresh_token,
            context=_context(request, device_name=payload.device_name, platform=payload.platform),
        )
        db.commit()
        return response
    except AuthError as exc:
        if exc.commit_state:
            db.commit()
        else:
            db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/logout", response_model=LogoutResponse, dependencies=[Depends(auth_rate_limit)])
def logout(
    payload: LogoutRequest,
    request: Request,
    db: Session = Depends(get_db),
    auth_service=Depends(get_auth_service),
):
    success = auth_service.logout(db, payload.refresh_token, context=_context(request))
    db.commit()
    return LogoutResponse(success=success)


@router.post("/revoke-sessions", response_model=SessionRevocationResponse)
def revoke_sessions(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    auth_service=Depends(get_auth_service),
):
    response = auth_service.revoke_sessions(db, current_user, context=_context(request))
    db.commit()
    return response


@router.get("/me", response_model=UserResponse)
def auth_me(current_user=Depends(require_active_user), auth_service=Depends(get_auth_service)):
    return auth_service.get_me(current_user)
