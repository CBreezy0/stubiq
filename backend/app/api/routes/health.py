"""Health and readiness routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_recommendation_service, get_scheduler, get_settings
from app.database import get_db
from app.schemas.common import HealthResponse, HealthzResponse, ReadinessResponse

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
        market_phase=phase,
        feature_flags=settings.feature_flags.__dict__,
    )


@router.get("/healthz", response_model=HealthzResponse)
def healthz():
    return HealthzResponse(status="ok")


@router.get(
    "/readyz",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
)
def readyz(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return ReadinessResponse(database="connected")
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"database": "error"},
        )
