"""Flip listing routes."""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_show_sync_service
from app.api.routes.market import listing_query_params
from app.database import get_db
from app.models import Card, TopFlip
from app.services.redis_cache import build_cache_key, load_cached_response, store_cached_response
from app.schemas.show_sync import LiveMarketListingListResponse, LiveMarketListingResponse

router = APIRouter(prefix="/flips", tags=["flips"])


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


def _top_flip_sort_column(sort_by: str):
    if sort_by == "roi":
        return TopFlip.roi
    if sort_by in {"profit", "profit_after_tax"}:
        return TopFlip.profit
    return TopFlip.profit_per_min


def _top_flip_row_to_response(row: TopFlip, card: Optional[Card]) -> LiveMarketListingResponse:
    return LiveMarketListingResponse(
        uuid=row.item_id,
        name=row.name or (card.name if card else row.item_id),
        best_buy_price=row.buy_price,
        best_sell_price=row.sell_price,
        spread=None,
        profit_after_tax=row.profit,
        roi=row.roi,
        position=card.display_position if card else None,
        series=card.series if card else None,
        team=card.team if card else None,
        overall=card.overall if card else None,
        rarity=card.rarity if card else None,
        order_volume=0,
        liquidity_score=None,
        profit_per_minute=row.profit_per_min,
        flip_score=row.profit_per_min,
        last_seen_at=row.updated_at,
    )


@router.get("/top", response_model=LiveMarketListingListResponse)
def top_flips(
    params=Depends(top_flip_query_params),
    db: Session = Depends(get_db),
):
    cache_key = build_cache_key("flips/top", params)
    cached_response = load_cached_response(cache_key, LiveMarketListingListResponse)
    if cached_response is not None:
        return cached_response

    sort_column = _top_flip_sort_column(params["sort_by"])
    query = (
        select(TopFlip, Card)
        .select_from(TopFlip)
        .outerjoin(Card, Card.item_id == TopFlip.item_id)
    )

    roi_min = params.get("roi_min")
    if roi_min is not None:
        query = query.where(TopFlip.roi.is_not(None)).where(TopFlip.roi >= roi_min)

    profit_min = params.get("profit_min")
    if profit_min is not None:
        query = query.where(TopFlip.profit.is_not(None)).where(TopFlip.profit >= profit_min)

    rarity = params.get("rarity")
    if rarity:
        query = query.where(Card.rarity.is_not(None)).where(Card.rarity.ilike(rarity.strip()))

    team = params.get("team")
    if team:
        query = query.where(Card.team.is_not(None)).where(Card.team.ilike(team.strip()))

    series = params.get("series")
    if series:
        query = query.where(Card.series.is_not(None)).where(Card.series.ilike(series.strip()))

    rows = db.execute(
        query.order_by(sort_column.desc().nullslast(), TopFlip.updated_at.desc()).limit(params["limit"])
    ).all()
    items = [_top_flip_row_to_response(top_flip, card) for top_flip, card in rows]
    response = LiveMarketListingListResponse(count=len(items), items=items)
    store_cached_response(cache_key, response)
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
