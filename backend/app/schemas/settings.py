"""Settings and admin schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.utils.enums import MarketPhase, UpdateType


class MarketPhaseOverrideRequest(BaseModel):
    phase: Optional[MarketPhase] = None
    notes: Optional[str] = None


class MarketPhaseOverrideResponse(BaseModel):
    override_phase: Optional[MarketPhase] = None
    notes: Optional[str] = None
    updated_at: datetime


class UpdateCalendarRequest(BaseModel):
    update_type: UpdateType
    update_date: datetime
    notes: Optional[str] = None


class UpdateCalendarResponse(BaseModel):
    id: int
    update_type: UpdateType
    update_date: datetime
    notes: Optional[str] = None


class EngineThresholdsResponse(BaseModel):
    floor_buy_margin: float
    launch_supply_crash_threshold: float
    flip_profit_minimum: float
    grind_market_edge: float
    collection_lock_penalty: float
    gatekeeper_hold_weight: float
    updated_at: Optional[datetime] = None


class EngineThresholdsPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    floor_buy_margin: Optional[float] = Field(default=None, ge=0)
    launch_supply_crash_threshold: Optional[float] = Field(default=None, ge=0)
    flip_profit_minimum: Optional[float] = Field(default=None, ge=0)
    grind_market_edge: Optional[float] = Field(default=None, ge=0)
    collection_lock_penalty: Optional[float] = Field(default=None, ge=0)
    gatekeeper_hold_weight: Optional[float] = Field(default=None, ge=0)
