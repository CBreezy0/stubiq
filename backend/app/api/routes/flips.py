"""Flip listing routes."""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_show_sync_service
from app.api.routes.market import listing_query_params
from app.database import get_db
from app.services.redis_cache import load_cached_response
from app.schemas.show_sync import LiveMarketListingListResponse, LiveMarketListingResponse

router = APIRouter(prefix="/flips", tags=["flips"])

TOP_FLIPS_HARD_CAP = 25
CACHE_CONTROL_HEADER = "public, max-age=60"


def top_flip_query_params(
    roi_min: Optional[float] = Query(default=None),
    profit_min: Optional[int] = Query(default=None, ge=0),
    liquidity_min: Optional[float] = Query(default=None, ge=0),
    rarity: Optional[str] = Query(default=None),
    team: Optional[str] = Query(default=None),
    series: Optional[str] = Query(default=None),
    sort_by: Literal["roi", "profit_after_tax", "profit_per_minute", "flip_score", "profit"] = Query(default="flip_score"),
    limit: int = Query(default=50, ge=1, le=50),
):
    return {
        "roi_min": roi_min,
        "profit_min": profit_min,
        "liquidity_min": liquidity_min,
        "rarity": rarity,
        "team": team,
        "series": series,
        "sort_by": sort_by,
        "limit": limit,
    }


def _normalize_text(value: Optional[str]) -> str:
    return value.strip().lower() if value else ""


def _merge_cache_control(response: Response) -> None:
    existing = response.headers.get("Cache-Control")
    if not existing:
        response.headers["Cache-Control"] = CACHE_CONTROL_HEADER
        return
    if CACHE_CONTROL_HEADER not in existing:
        response.headers["Cache-Control"] = f"{existing}, {CACHE_CONTROL_HEADER}"


def _sort_top_flip_items(items: list[LiveMarketListingResponse], sort_by: str) -> list[LiveMarketListingResponse]:
    field_name = "profit_after_tax" if sort_by in {"profit", "profit_after_tax"} else sort_by

    def sort_value(item: LiveMarketListingResponse):
        value = getattr(item, field_name, None)
        return float("-inf") if value is None else value

    return sorted(items, key=sort_value, reverse=True)


@router.get("/top", response_model=LiveMarketListingListResponse)
def top_flips(
    response: Response,
    params=Depends(top_flip_query_params),
):
    _merge_cache_control(response)
    cached_response = load_cached_response("flips:top", LiveMarketListingListResponse)
    if cached_response is None:
        return LiveMarketListingListResponse(count=0, items=[])

    items = list(cached_response.items)

    roi_min = params.get("roi_min")
    if roi_min is not None:
        items = [item for item in items if item.roi is not None and item.roi >= roi_min]

    profit_min = params.get("profit_min")
    if profit_min is not None:
        items = [item for item in items if item.profit_after_tax is not None and item.profit_after_tax >= profit_min]

    liquidity_min = params.get("liquidity_min")
    if liquidity_min is not None:
        items = [item for item in items if item.liquidity_score is not None and item.liquidity_score >= liquidity_min]

    rarity = _normalize_text(params.get("rarity"))
    if rarity:
        items = [item for item in items if _normalize_text(item.rarity) == rarity]

    team = _normalize_text(params.get("team"))
    if team:
        items = [item for item in items if _normalize_text(item.team) == team]

    series = _normalize_text(params.get("series"))
    if series:
        items = [item for item in items if _normalize_text(item.series) == series]

    limit = min(params["limit"], TOP_FLIPS_HARD_CAP)
    items = _sort_top_flip_items(items, params["sort_by"])[:limit]
    return LiveMarketListingListResponse(count=len(items), items=items)


@router.get("", response_model=LiveMarketListingListResponse)
def flips(
    params=Depends(listing_query_params),
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    response = show_sync_service.get_flip_listings_response(db, **params)
    db.commit()
    return response
