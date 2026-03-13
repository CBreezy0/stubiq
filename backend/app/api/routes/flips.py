"""Flip listing routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_show_sync_service
from app.api.routes.market import listing_query_params
from app.database import get_db
from app.schemas.show_sync import LiveMarketListingListResponse

router = APIRouter(prefix="/flips", tags=["flips"])


@router.get("", response_model=LiveMarketListingListResponse)
def flips(
    params=Depends(listing_query_params),
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    response = show_sync_service.get_flip_listings_response(db, **params)
    db.commit()
    return response
