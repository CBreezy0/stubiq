"""Dashboard summary schemas."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from .collections import CollectionPriorityResponse
from .common import MarketPhaseResponse
from .grind import GrindRecommendationResponse
from .investments import RosterUpdateRecommendationResponse
from .market import MarketOpportunityResponse
from .portfolio import PortfolioPositionResponse, PortfolioRecommendationResponse


class DashboardSummaryResponse(BaseModel):
    market_phase: MarketPhaseResponse
    launch_week_alerts: List[str] = Field(default_factory=list)
    top_flips: List[MarketOpportunityResponse] = Field(default_factory=list)
    top_floor_buys: List[MarketOpportunityResponse] = Field(default_factory=list)
    top_roster_update_targets: List[RosterUpdateRecommendationResponse] = Field(default_factory=list)
    collection_priorities: CollectionPriorityResponse
    portfolio: List[PortfolioPositionResponse] = Field(default_factory=list)
    top_sells: List[PortfolioRecommendationResponse] = Field(default_factory=list)
    grind_recommendation: GrindRecommendationResponse
