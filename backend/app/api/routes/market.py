"""Market routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_recommendation_service, get_show_sync_service
from app.database import get_db
from app.schemas.market import MarketOpportunityListResponse
from app.schemas.show_sync import LiveMarketListingListResponse, MarketMoverListResponse, MarketPriceMoverListResponse, PriceHistoryResponse
from app.security.deps import get_optional_user

router = APIRouter(prefix="/market", tags=["market"])


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


@router.get("/listings", response_model=LiveMarketListingListResponse)
def market_listings(
    params=Depends(listing_query_params),
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
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


@router.get("/movers", response_model=MarketPriceMoverListResponse)
def market_movers(
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    return show_sync_service.get_market_movers_response(db, limit=50)


@router.get("/trending", response_model=MarketMoverListResponse)
def market_trending(
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    return show_sync_service.get_trending_response(db, limit=limit)


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
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
    recommendation_service=Depends(get_recommendation_service),
):
    return recommendation_service.get_floor_buys(db, limit=limit, user=current_user)


@router.get("/phases")
def market_phases(
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
    recommendation_service=Depends(get_recommendation_service),
):
    return {
        "current": recommendation_service.get_phase(db, user=current_user),
        "history": recommendation_service.get_phase_history(db),
    }
