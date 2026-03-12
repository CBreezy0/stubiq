"""Portfolio schemas."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.utils.enums import RecommendationAction

from .cards import CardSummaryResponse


class PortfolioManualAddRequest(BaseModel):
    item_id: str
    card_name: str
    quantity: int = Field(gt=0)
    avg_acquisition_cost: int = Field(ge=0)
    locked_for_collection: bool = False
    source: str = "manual"


class PortfolioManualRemoveRequest(BaseModel):
    item_id: str
    quantity: int = Field(default=1, gt=0)
    remove_all: bool = False


class PortfolioPositionResponse(BaseModel):
    item_id: str
    card: CardSummaryResponse
    quantity: int
    avg_acquisition_cost: int
    current_market_value: Optional[int] = None
    quicksell_value: Optional[int] = None
    locked_for_collection: bool
    duplicate_count: int
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    total_cost_basis: int
    unrealized_profit: Optional[int] = None
    quicksell_floor_total: Optional[int] = None


class PortfolioRecommendationResponse(BaseModel):
    item_id: str
    action: RecommendationAction
    confidence: float
    sell_now_score: float
    hold_score: float
    lock_score: float
    flip_out_score: float
    portfolio_risk_score: float
    rationale: str


class PortfolioResponse(BaseModel):
    total_positions: int
    total_market_value: int
    total_cost_basis: int
    total_unrealized_profit: int
    items: List[PortfolioPositionResponse]


class PortfolioImportResponse(BaseModel):
    imported_count: int
    skipped_count: int
    errors: List[str] = Field(default_factory=list)
