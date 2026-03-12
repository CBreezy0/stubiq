"""Dashboard summary endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_recommendation_service
from app.database import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.security.deps import get_optional_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
    recommendation_service=Depends(get_recommendation_service),
):
    return recommendation_service.get_dashboard_summary(db, user=current_user)
