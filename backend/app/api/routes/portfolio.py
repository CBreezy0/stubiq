"""Portfolio routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_portfolio_service, get_recommendation_service
from app.database import get_db
from app.schemas.portfolio import (
    PortfolioImportResponse,
    PortfolioManualAddRequest,
    PortfolioManualRemoveRequest,
    PortfolioRecommendationResponse,
    PortfolioResponse,
)
from app.security.deps import require_active_user

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioResponse)
def portfolio_view(
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    recommendation_service=Depends(get_recommendation_service),
):
    return recommendation_service.get_portfolio(db, user=current_user)


@router.get("/recommendations", response_model=list[PortfolioRecommendationResponse])
def portfolio_recommendations(
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    recommendation_service=Depends(get_recommendation_service),
):
    return recommendation_service.get_portfolio_recommendations(db, user=current_user)


@router.post("/import", response_model=PortfolioImportResponse)
async def import_portfolio_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    portfolio_service=Depends(get_portfolio_service),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV upload required")
    result = portfolio_service.import_csv(db, current_user, await file.read())
    db.commit()
    return PortfolioImportResponse(**result)


@router.post("/manual-add", response_model=PortfolioResponse)
def manual_add_portfolio(
    payload: PortfolioManualAddRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    portfolio_service=Depends(get_portfolio_service),
    recommendation_service=Depends(get_recommendation_service),
):
    portfolio_service.manual_add(
        db,
        user=current_user,
        item_id=payload.item_id,
        card_name=payload.card_name,
        quantity=payload.quantity,
        avg_acquisition_cost=payload.avg_acquisition_cost,
        locked_for_collection=payload.locked_for_collection,
        source=payload.source,
    )
    db.commit()
    return recommendation_service.get_portfolio(db, user=current_user)


@router.post("/manual-remove", response_model=PortfolioResponse)
def manual_remove_portfolio(
    payload: PortfolioManualRemoveRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_active_user),
    portfolio_service=Depends(get_portfolio_service),
    recommendation_service=Depends(get_recommendation_service),
):
    portfolio_service.manual_remove(db, current_user, payload.item_id, payload.quantity, payload.remove_all)
    db.commit()
    return recommendation_service.get_portfolio(db, user=current_user)
