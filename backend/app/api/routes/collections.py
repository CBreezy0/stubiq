"""Collection planning routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_recommendation_service
from app.database import get_db
from app.schemas.collections import CollectionPriorityResponse
from app.security.deps import get_optional_user

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("/priorities", response_model=CollectionPriorityResponse)
def collection_priorities(
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
    recommendation_service=Depends(get_recommendation_service),
):
    return recommendation_service.get_collection_priorities(db, user=current_user)
