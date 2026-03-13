"""Routes for MLB The Show metadata, search, and roster update feeds."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_show_sync_service
from app.database import get_db
from app.schemas.show_sync import ShowMetadataResponse, ShowPlayerSearchResponse, ShowRosterUpdateListResponse

router = APIRouter(tags=["show-sync"])


@router.get("/metadata", response_model=ShowMetadataResponse)
def metadata(
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    response = show_sync_service.get_metadata_response(db, force_refresh=refresh)
    db.commit()
    return response


@router.get("/player-search", response_model=ShowPlayerSearchResponse)
def player_search(
    username: str = Query(..., min_length=1),
    refresh: bool = Query(default=True),
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    response = show_sync_service.get_player_search_response(db, username=username, force_refresh=refresh)
    db.commit()
    return response


@router.get("/roster-updates", response_model=ShowRosterUpdateListResponse)
def roster_updates(
    limit: int = Query(default=25, ge=1, le=100),
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    response = show_sync_service.get_roster_updates_response(db, limit=limit, force_refresh=refresh)
    db.commit()
    return response
