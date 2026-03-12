"""Console connection routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.connection import (
    ConnectionCallbackRequest,
    ConnectionCompleteRequest,
    ConnectionListResponse,
    ConnectionStartResponse,
    UserConnectionResponse,
)
from app.security.deps import get_connection_service, require_active_user
from app.services.connection_service import ConnectionServiceError
from app.utils.enums import ConnectionProvider

router = APIRouter(prefix="/connections", tags=["connections"])


@router.get("", response_model=ConnectionListResponse)
def get_connections(
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    connection_service=Depends(get_connection_service),
):
    return ConnectionListResponse(items=connection_service.list_connections(db, current_user))


@router.post("/xbox/start", response_model=ConnectionStartResponse)
def start_xbox_connection(current_user=Depends(require_active_user), connection_service=Depends(get_connection_service)):
    try:
        return connection_service.start_connection(current_user, ConnectionProvider.XBOX)
    except ConnectionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/playstation/start", response_model=ConnectionStartResponse)
def start_playstation_connection(current_user=Depends(require_active_user), connection_service=Depends(get_connection_service)):
    try:
        return connection_service.start_connection(current_user, ConnectionProvider.PLAYSTATION)
    except ConnectionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/xbox/complete", response_model=UserConnectionResponse)
def complete_xbox_connection(
    payload: ConnectionCompleteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    connection_service=Depends(get_connection_service),
):
    try:
        response = connection_service.complete_connection(
            db,
            current_user,
            ConnectionProvider.XBOX,
            session_token=payload.session_token,
            provider_account_id=payload.provider_account_id,
            display_name=payload.display_name,
            gamertag_or_psn=payload.gamertag_or_psn,
            status=payload.status,
            metadata_json=payload.metadata_json,
        )
        db.commit()
        return response
    except ConnectionServiceError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/playstation/complete", response_model=UserConnectionResponse)
def complete_playstation_connection(
    payload: ConnectionCompleteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    connection_service=Depends(get_connection_service),
):
    try:
        response = connection_service.complete_connection(
            db,
            current_user,
            ConnectionProvider.PLAYSTATION,
            session_token=payload.session_token,
            provider_account_id=payload.provider_account_id,
            display_name=payload.display_name,
            gamertag_or_psn=payload.gamertag_or_psn,
            status=payload.status,
            metadata_json=payload.metadata_json,
        )
        db.commit()
        return response
    except ConnectionServiceError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/xbox/callback", response_model=UserConnectionResponse)
def xbox_callback(
    payload: ConnectionCallbackRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    connection_service=Depends(get_connection_service),
):
    try:
        response = connection_service.handle_callback(
            db,
            current_user,
            ConnectionProvider.XBOX,
            code=payload.code,
            session_token=payload.session_token,
            redirect_uri=payload.redirect_uri,
            metadata_json=payload.metadata_json,
        )
        db.commit()
        return response
    except ConnectionServiceError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/playstation/callback", response_model=UserConnectionResponse)
def playstation_callback(
    payload: ConnectionCallbackRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    connection_service=Depends(get_connection_service),
):
    try:
        response = connection_service.handle_callback(
            db,
            current_user,
            ConnectionProvider.PLAYSTATION,
            code=payload.code,
            session_token=payload.session_token,
            redirect_uri=payload.redirect_uri,
            metadata_json=payload.metadata_json,
        )
        db.commit()
        return response
    except ConnectionServiceError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete("/{provider}", response_model=UserConnectionResponse)
def disconnect_connection(
    provider: ConnectionProvider,
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    connection_service=Depends(get_connection_service),
):
    try:
        response = connection_service.disconnect_connection(db, current_user, provider)
        db.commit()
        return response
    except ConnectionServiceError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
