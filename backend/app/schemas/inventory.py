"""Schemas for user inventory foundation endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .cards import CardSummaryResponse


class InventoryImportItemRequest(BaseModel):
    item_uuid: str
    quantity: int = Field(default=1, ge=1)
    is_sellable: bool = True
    card_name: Optional[str] = None


class InventoryImportRequest(BaseModel):
    items: list[InventoryImportItemRequest] = Field(default_factory=list)
    replace_existing: bool = True


class InventoryItemResponse(BaseModel):
    item_uuid: str
    card: CardSummaryResponse
    quantity: int
    is_sellable: bool
    synced_at: datetime
    current_price: Optional[int] = None
    total_value: Optional[int] = None
    profit_loss: Optional[int] = None


class InventoryResponse(BaseModel):
    count: int
    total_quantity: int
    total_market_value: int
    total_profit_loss: int
    items: list[InventoryItemResponse] = Field(default_factory=list)


class InventoryImportResponse(BaseModel):
    imported_count: int
    replaced_existing: bool
    inventory: InventoryResponse
