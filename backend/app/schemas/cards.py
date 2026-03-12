"""Card response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .common import RecommendationView


class CardSummaryResponse(BaseModel):
    item_id: str
    name: str
    series: Optional[str] = None
    team: Optional[str] = None
    division: Optional[str] = None
    league: Optional[str] = None
    overall: Optional[int] = None
    rarity: Optional[str] = None
    display_position: Optional[str] = None
    is_live_series: bool
    quicksell_value: Optional[int] = None
    latest_buy_now: Optional[int] = None
    latest_sell_now: Optional[int] = None
    latest_best_buy_order: Optional[int] = None
    latest_best_sell_order: Optional[int] = None
    latest_tax_adjusted_spread: Optional[int] = None
    observed_at: Optional[datetime] = None


class CardDetailResponse(CardSummaryResponse):
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    aggregate_phase: Optional[str] = None
    avg_price_15m: Optional[float] = None
    avg_price_1h: Optional[float] = None
    avg_price_6h: Optional[float] = None
    avg_price_24h: Optional[float] = None
    volatility_score: Optional[float] = None
    liquidity_score: Optional[float] = None
    recommendations: List[RecommendationView] = Field(default_factory=list)
