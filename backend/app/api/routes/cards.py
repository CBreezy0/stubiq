"""Card detail routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_recommendation_service
from app.database import get_db
from app.schemas.cards import CardDetailResponse
from app.security.deps import get_optional_user

router = APIRouter(tags=["cards"])


@router.get("/cards/{item_id}", response_model=CardDetailResponse)
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
