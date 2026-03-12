"""Grind EV schemas."""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field

from app.utils.enums import RecommendationAction


class ModeValueResponse(BaseModel):
    mode_name: str
    expected_value_per_hour: float
    rationale: str


class GrindRecommendationResponse(BaseModel):
    action: RecommendationAction
    best_mode_to_play_now: str
    expected_market_stubs_per_hour: float
    expected_value_per_hour_by_mode: List[ModeValueResponse] = Field(default_factory=list)
    pack_value_estimate: float
    rationale: str
