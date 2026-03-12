"""Settings and admin routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_config_store
from app.database import get_db
from app.models import RosterUpdateCalendar
from app.schemas.settings import (
    EngineThresholdsPatchRequest,
    EngineThresholdsResponse,
    MarketPhaseOverrideRequest,
    MarketPhaseOverrideResponse,
    UpdateCalendarRequest,
    UpdateCalendarResponse,
)
from app.security.deps import get_user_service, require_active_user

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/engine-thresholds", response_model=EngineThresholdsResponse)
def get_engine_thresholds(
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    user_service=Depends(get_user_service),
):
    payload, settings_row = user_service.get_public_engine_thresholds(db, current_user)
    db.commit()
    db.refresh(settings_row)
    return EngineThresholdsResponse(**payload, updated_at=settings_row.updated_at)


@router.patch("/engine-thresholds", response_model=EngineThresholdsResponse)
def patch_engine_thresholds(
    payload: EngineThresholdsPatchRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    user_service=Depends(get_user_service),
):
    updates = payload.model_dump(exclude_none=True)
    settings_row = user_service.update_engine_thresholds(db, current_user, updates)
    db.commit()
    db.refresh(settings_row)
    current, _ = user_service.get_public_engine_thresholds(db, current_user)
    return EngineThresholdsResponse(**current, updated_at=settings_row.updated_at)


@router.post("/market-phase", response_model=MarketPhaseOverrideResponse)
def set_market_phase_override(
    payload: MarketPhaseOverrideRequest,
    db: Session = Depends(get_db),
    config_store=Depends(get_config_store),
):
    result = config_store.set_market_phase_override(db, payload.phase, notes=payload.notes)
    db.commit()
    updated_at = datetime.fromisoformat(result["updated_at"])
    return MarketPhaseOverrideResponse(override_phase=payload.phase, notes=payload.notes, updated_at=updated_at)


@router.post("/update-calendar", response_model=UpdateCalendarResponse)
def create_update_calendar_event(
    payload: UpdateCalendarRequest,
    db: Session = Depends(get_db),
):
    row = RosterUpdateCalendar(update_type=payload.update_type, update_date=payload.update_date, notes=payload.notes)
    db.add(row)
    db.commit()
    db.refresh(row)
    return UpdateCalendarResponse(id=row.id, update_type=row.update_type, update_date=row.update_date, notes=row.notes)
