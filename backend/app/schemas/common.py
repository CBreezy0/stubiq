"""Shared schema models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.utils.enums import MarketPhase, RecommendationAction, RecommendationType


class RecommendationView(BaseModel):
    recommendation_type: RecommendationType
    action: RecommendationAction
    confidence: float
    expected_profit: Optional[int] = None
    expected_value: Optional[float] = None
    market_phase: MarketPhase
    rationale: str
    rationale_json: Dict[str, Any] = Field(default_factory=dict)


class MarketPhaseResponse(BaseModel):
    phase: MarketPhase
    confidence: float
    rationale: str
    override_active: bool = False
    detected_at: datetime


class HealthzResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    database: str


class HealthResponse(BaseModel):
    status: str
    app_name: str
    game_year: int
    scheduler_running: bool
    market_phase: MarketPhaseResponse
    feature_flags: Dict[str, bool]


class JobRunRequest(BaseModel):
    job_name: str = Field(description="market_refresh, stats_refresh, lineup_refresh, recommendations_refresh, all")


class JobRunResponse(BaseModel):
    requested_job: str
    accepted_jobs: List[str]
    message: str
