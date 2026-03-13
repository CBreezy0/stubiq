"""Collection planning routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from app.schemas.collections import CollectionPriorityResponse
from app.utils.enums import MarketPhase

router = APIRouter(prefix="/collections", tags=["collections"])
logger = logging.getLogger(__name__)


@router.get("/priorities", response_model=CollectionPriorityResponse)
def collection_priorities():
    logger.warning("Collections priorities is temporarily disabled to avoid heavy request-time computation")
    return CollectionPriorityResponse(
        market_phase=MarketPhase.STABILIZATION,
        projected_completion_cost=0,
        ranked_division_targets=[],
        ranked_team_targets=[],
        recommended_cards_to_lock=[],
        recommended_cards_to_delay=[],
    )
