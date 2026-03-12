"""Grind EV routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_recommendation_service
from app.database import get_db
from app.schemas.grind import GrindRecommendationResponse

router = APIRouter(prefix="/grind", tags=["grind"])


@router.get("/recommendations", response_model=GrindRecommendationResponse)
def grind_recommendations(
    db: Session = Depends(get_db),
    recommendation_service=Depends(get_recommendation_service),
):
    return recommendation_service.get_grind_recommendation(db)
