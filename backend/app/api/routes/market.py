"""Market routes."""

from __future__ import annotations

import logging

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_recommendation_service, get_show_sync_service
from app.database import get_db
from app.models import Card, FloorOpportunity, ListingsSnapshot, MarketMoverCache, MarketPhaseCache
from app.schemas.cards import CardSummaryResponse
from app.schemas.common import MarketPhaseResponse
from app.schemas.market import MarketOpportunityListResponse, MarketOpportunityResponse
from app.schemas.show_sync import LiveMarketListingListResponse, MarketMoverItem, MarketMoverListResponse, MarketMoversResponse, PriceHistoryResponse
from app.security.deps import get_optional_user
from app.services.redis_cache import load_cached_json, load_cached_response
from app.utils.enums import MarketPhase, RecommendationAction
from app.utils.time import utcnow

router = APIRouter(prefix="/market", tags=["market"])

MARKET_LISTINGS_HARD_CAP = 50
MARKET_MOVERS_HARD_CAP = 25
MARKET_FLOORS_HARD_CAP = 25
MARKET_TRENDING_HARD_CAP = 25
CACHE_CONTROL_HEADER = "public, max-age=60"

logger = logging.getLogger(__name__)


def _latest_snapshot_subquery():
    ranked_snapshots = (
        select(
            ListingsSnapshot.item_id.label("item_id"),
            ListingsSnapshot.buy_now.label("buy_now"),
            ListingsSnapshot.sell_now.label("sell_now"),
            ListingsSnapshot.best_buy_order.label("best_buy_order"),
            ListingsSnapshot.best_sell_order.label("best_sell_order"),
            ListingsSnapshot.tax_adjusted_spread.label("tax_adjusted_spread"),
            ListingsSnapshot.observed_at.label("observed_at"),
            func.row_number().over(
                partition_by=ListingsSnapshot.item_id,
                order_by=(ListingsSnapshot.observed_at.desc(), ListingsSnapshot.id.desc()),
            ).label("rank"),
        )
        .subquery()
    )
    return (
        select(
            ranked_snapshots.c.item_id,
            ranked_snapshots.c.buy_now,
            ranked_snapshots.c.sell_now,
            ranked_snapshots.c.best_buy_order,
            ranked_snapshots.c.best_sell_order,
            ranked_snapshots.c.tax_adjusted_spread,
            ranked_snapshots.c.observed_at,
        )
        .where(ranked_snapshots.c.rank == 1)
        .subquery()
    )


def _cached_market_phase(db: Session) -> MarketPhase:
    phase = db.scalar(select(MarketPhaseCache.phase).order_by(MarketPhaseCache.updated_at.desc()).limit(1))
    return phase or MarketPhase.STABILIZATION


def _merge_cache_control(response: Response) -> None:
    existing = response.headers.get("Cache-Control")
    if not existing:
        response.headers["Cache-Control"] = CACHE_CONTROL_HEADER
        return
    if CACHE_CONTROL_HEADER not in existing:
        response.headers["Cache-Control"] = f"{existing}, {CACHE_CONTROL_HEADER}"


def _log_cache_miss(path: str) -> None:
    logger.warning("analytics cache miss for %s; returning empty payload", path)


def _cached_floor_action(row: FloorOpportunity) -> RecommendationAction:
    if row.expected_value is not None and row.floor_price not in (None, 0) and row.expected_value >= float(row.floor_price):
        return RecommendationAction.BUY
    return RecommendationAction.WATCH


def _cached_floor_response(
    row: FloorOpportunity,
    card: Card | None,
    snapshot_row,
    phase: MarketPhase,
) -> MarketOpportunityResponse:
    expected_profit = None
    if row.expected_value is not None and row.floor_price is not None:
        expected_profit = int(round(float(row.expected_value) - float(row.floor_price)))
    floor_score = max(0.0, min(float(row.roi or 0.0), 100.0))
    card_summary = CardSummaryResponse(
        item_id=row.item_id,
        name=row.name or (card.name if card else row.item_id),
        series=card.series if card else None,
        team=card.team if card else None,
        division=card.division if card else None,
        league=card.league if card else None,
        overall=card.overall if card else None,
        rarity=card.rarity if card else None,
        display_position=card.display_position if card else None,
        is_live_series=card.is_live_series if card else False,
        quicksell_value=card.quicksell_value if card else None,
        latest_buy_now=snapshot_row.buy_now if snapshot_row is not None else None,
        latest_sell_now=snapshot_row.sell_now if snapshot_row is not None else None,
        latest_best_buy_order=snapshot_row.best_buy_order if snapshot_row is not None else None,
        latest_best_sell_order=(snapshot_row.best_sell_order if snapshot_row is not None else row.floor_price),
        latest_tax_adjusted_spread=snapshot_row.tax_adjusted_spread if snapshot_row is not None else None,
        observed_at=snapshot_row.observed_at if snapshot_row is not None else row.updated_at,
    )
    return MarketOpportunityResponse(
        item_id=row.item_id,
        card=card_summary,
        action=_cached_floor_action(row),
        expected_profit_per_flip=expected_profit,
        fill_velocity_score=0.0,
        liquidity_score=0.0,
        risk_score=0.0,
        floor_proximity_score=floor_score,
        market_phase=phase,
        confidence=1.0 if row.roi is not None else 0.0,
        rationale="Served from precomputed floor opportunities cache.",
    )


def listing_query_params(
    min_roi: Optional[float] = Query(default=None),
    min_profit: Optional[int] = Query(default=None, ge=0),
    max_buy_price: Optional[int] = Query(default=None, ge=0),
    rarity: Optional[str] = Query(default=None),
    series: Optional[str] = Query(default=None),
    team: Optional[str] = Query(default=None),
    position: Optional[str] = Query(default=None),
    sort_by: str = Query(default="profit"),
    sort_order: str = Query(default="desc"),
    limit: int = Query(default=50, ge=1, le=200),
    refresh: bool = Query(default=False),
):
    return {
        "min_roi": min_roi,
        "min_profit": min_profit,
        "max_buy_price": max_buy_price,
        "rarity": rarity,
        "series": series,
        "team": team,
        "position": position,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "limit": limit,
        "force_refresh": refresh,
    }


@router.get("", response_model=LiveMarketListingListResponse)
def market_root(
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    response = show_sync_service.get_market_listings_response(db, limit=25)
    db.commit()
    return response


@router.get("/listings", response_model=LiveMarketListingListResponse)
def market_listings(
    params=Depends(listing_query_params),
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    params["limit"] = min(params["limit"], MARKET_LISTINGS_HARD_CAP)
    response = show_sync_service.get_market_listings_response(db, **params)
    db.commit()
    return response


@router.get("/flips", response_model=LiveMarketListingListResponse)
def market_flips(
    params=Depends(listing_query_params),
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    response = show_sync_service.get_flip_listings_response(db, **params)
    db.commit()
    return response


@router.get("/history/{uuid}", response_model=PriceHistoryResponse)
def market_history(
    uuid: str,
    days: int = Query(default=1, ge=1, le=30),
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    return show_sync_service.get_market_history_response(db, uuid=uuid, days=days)


@router.get("/movers", response_model=MarketMoversResponse)
def market_movers(
    response: Response,
    limit: int = Query(default=50, ge=1, le=50),
):
    _merge_cache_control(response)
    limit = min(limit, MARKET_MOVERS_HARD_CAP)
    cached_response = load_cached_response("market:movers", MarketMoversResponse)
    if cached_response is None:
        _log_cache_miss("/market/movers")
        return MarketMoversResponse(count=0, items=[])

    items = list(cached_response.items)[:limit]
    return MarketMoversResponse(count=len(items), items=items)


@router.get("/trending", response_model=MarketMoverListResponse)
def market_trending(
    response: Response,
    limit: int = Query(default=25, ge=1, le=100),
):
    _merge_cache_control(response)
    limit = min(limit, MARKET_TRENDING_HARD_CAP)
    cached_response = load_cached_response("market:trending", MarketMoverListResponse)
    if cached_response is None:
        _log_cache_miss("/market/trending")
        return MarketMoverListResponse(count=0, items=[])

    items = list(cached_response.items)[:limit]
    return MarketMoverListResponse(count=len(items), items=items)


@router.get("/biggest-movers", response_model=MarketMoverListResponse)
def market_biggest_movers(
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    return show_sync_service.get_biggest_movers_response(db, limit=limit)


@router.get("/strategy-flips", response_model=MarketOpportunityListResponse)
def market_strategy_flips(
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
    recommendation_service=Depends(get_recommendation_service),
):
    return recommendation_service.get_flips(db, limit=limit, user=current_user)


@router.get("/floors", response_model=MarketOpportunityListResponse)
def market_floors(
    response: Response,
    limit: int = Query(default=25, ge=1, le=100),
):
    _merge_cache_control(response)
    limit = min(limit, MARKET_FLOORS_HARD_CAP)
    cached_response = load_cached_response("market:floors", MarketOpportunityListResponse)
    if cached_response is None:
        _log_cache_miss("/market/floors")
        return MarketOpportunityListResponse(phase=MarketPhase.STABILIZATION, count=0, items=[])

    items = list(cached_response.items)[:limit]
    return MarketOpportunityListResponse(phase=cached_response.phase, count=len(items), items=items)


@router.get("/phases")
def market_phases(
    response: Response,
):
    _merge_cache_control(response)
    cached_payload = load_cached_json("market:phases")
    if cached_payload is not None:
        return cached_payload

    _log_cache_miss("/market/phases")
    return {
        "current": MarketPhaseResponse(
            phase=MarketPhase.STABILIZATION,
            confidence=0.0,
            rationale="Analytics cache is cold; returning empty market phase payload.",
            override_active=False,
            detected_at=utcnow(),
        ),
        "history": [],
    }
