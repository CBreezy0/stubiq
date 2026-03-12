"""Health and readiness routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_recommendation_service, get_scheduler, get_settings
from app.database import get_db
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    db: Session = Depends(get_db),
    settings=Depends(get_settings),
    scheduler=Depends(get_scheduler),
    recommendation_service=Depends(get_recommendation_service),
):
    phase = recommendation_service.get_phase(db)
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        game_year=settings.game_year,
        scheduler_running=scheduler.is_running(),
        database_url=settings.database_url,
        market_phase=phase,
        feature_flags=settings.feature_flags.__dict__,
    )
