"""Card detail routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_recommendation_service, get_show_sync_service
from app.database import get_db
from app.schemas.cards import CardDetailResponse
from app.schemas.show_sync import CardPriceHistoryResponse, CardSearchResponse
from app.security.deps import get_optional_user

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/search", response_model=CardSearchResponse)
def card_search(
    q: str,
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    return show_sync_service.get_card_search_response(db, q, limit=50)


@router.get("/{item_id}", response_model=CardDetailResponse)
def card_detail(
    item_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
    recommendation_service=Depends(get_recommendation_service),
):
    card = recommendation_service.get_card_detail(db, item_id, user=current_user)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return card


@router.get("/{item_id}/history", response_model=CardPriceHistoryResponse)
def card_price_history(
    item_id: str,
    db: Session = Depends(get_db),
    show_sync_service=Depends(get_show_sync_service),
):
    response = show_sync_service.get_card_price_history_response(db, item_id)
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return response
