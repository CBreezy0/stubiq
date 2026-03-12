"""Roster update investment routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_recommendation_service
from app.database import get_db
from app.schemas.investments import (
    RosterUpdatePlayerAnalysisResponse,
    RosterUpdateRecommendationListResponse,
)
from app.security.deps import get_optional_user

router = APIRouter(prefix="/investments", tags=["investments"])


@router.get("/roster-update", response_model=RosterUpdateRecommendationListResponse)
def roster_update_investments(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
    recommendation_service=Depends(get_recommendation_service),
):
    return recommendation_service.get_roster_update_targets(db, limit=limit, user=current_user)


@router.get("/player/{name}", response_model=RosterUpdatePlayerAnalysisResponse)
def roster_update_player_analysis(
    name: str,
    db: Session = Depends(get_db),
    recommendation_service=Depends(get_recommendation_service),
):
    result = recommendation_service.get_roster_update_player_analysis(db, name)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player analysis not found")
    return result
