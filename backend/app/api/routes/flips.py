"""Flip listing routes."""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_show_sync_service
from app.api.routes.market import listing_query_params
from app.database import get_db
from app.schemas.show_sync import LiveMarketListingListResponse

router = APIRouter(prefix="/flips", tags=["flips"])


def top_flip_query_params(
    roi_min: Optional[float] = Query(default=None),
    profit_min: Optional[int] = Query(default=None, ge=0),
    liquidity_min: Optional[float] = Query(default=None, ge=0),
    rarity: Optional[str] = Query(default=None),
    team: Optional[str] = Query(default=None),
    series: Optional[str] = Query(default=None),
    sort_by: Literal["roi", "profit_after_tax", "profit_per_minute", "flip_score", "profit"] = Query(default="flip_score"),
):
    return {
        "roi_min": roi_min,
        "profit_min": profit_min,
        "liquidity_min": liquidity_min,
        "rarity": rarity,
        "team": team,
        "series": series,
        "sort_by": sort_by,
    }


@router.get("/top", response_model=LiveMarketListingListResponse)
def top_flips(
    params=Depends(top_flip_query_params),
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    response = show_sync_service.get_top_flip_listings_response(db, **params)
    db.commit()
    return response


@router.get("", response_model=LiveMarketListingListResponse)
def flips(
    params=Depends(listing_query_params),
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    response = show_sync_service.get_flip_listings_response(db, **params)
    db.commit()
    return response
