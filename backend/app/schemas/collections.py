"""Collection priority schemas."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.utils.enums import MarketPhase


class CollectionTarget(BaseModel):
    name: str
    level: str
    priority_score: float
    completion_pct: float
    remaining_cost: int
    owned_gatekeeper_value: int
    reward_value_proxy: int
    rationale: str


class CollectionPriorityResponse(BaseModel):
    market_phase: MarketPhase
    projected_completion_cost: int
    ranked_division_targets: List[CollectionTarget] = Field(default_factory=list)
    ranked_team_targets: List[CollectionTarget] = Field(default_factory=list)
    recommended_cards_to_lock: List[str] = Field(default_factory=list)
    recommended_cards_to_delay: List[str] = Field(default_factory=list)
