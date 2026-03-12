"""Roster update investment schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.utils.enums import RecommendationAction

from .cards import CardSummaryResponse


class RosterUpdateRecommendationResponse(BaseModel):
    item_id: str
    player_name: str
    mlb_player_id: int
    card: CardSummaryResponse
    action: RecommendationAction
    current_ovr: int
    current_price: int
    upgrade_probability: float
    downgrade_probability: float
    expected_quicksell_value: int
    expected_market_value: float
    expected_profit: float
    downside_risk: float
    confidence: float
    rationale: str
    rationale_json: Dict[str, Any] = Field(default_factory=dict)
    generated_at: Optional[datetime] = None


class RosterUpdateRecommendationListResponse(BaseModel):
    count: int
    items: List[RosterUpdateRecommendationResponse]


class RosterUpdatePlayerAnalysisResponse(RosterUpdateRecommendationResponse):
    matching_name: str
