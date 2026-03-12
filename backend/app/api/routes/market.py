"""Market routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_recommendation_service
from app.database import get_db
from app.schemas.market import MarketOpportunityListResponse
from app.security.deps import get_optional_user

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/flips", response_model=MarketOpportunityListResponse)
def market_flips(
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
