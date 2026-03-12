"""Market endpoint schemas."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from app.utils.enums import MarketPhase, RecommendationAction

from .cards import CardSummaryResponse


class MarketOpportunityResponse(BaseModel):
    item_id: str
    card: CardSummaryResponse
    action: RecommendationAction
    expected_profit_per_flip: Optional[int] = None
    fill_velocity_score: float
    liquidity_score: float
    risk_score: float
    floor_proximity_score: float
    market_phase: MarketPhase
    confidence: float
    rationale: str


class MarketOpportunityListResponse(BaseModel):
    phase: MarketPhase
    count: int
    items: List[MarketOpportunityResponse]
