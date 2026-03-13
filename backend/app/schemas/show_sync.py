"""Typed payload and response schemas for MLB The Show sync endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class ShowListingItemPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    uuid: str
    type: Optional[str] = None
    img: Optional[str] = None
    baked_img: Optional[str] = None
    sc_baked_img: Optional[str] = None
    name: str
    short_description: Optional[str] = None
    rarity: Optional[str] = None
    team: Optional[str] = None
    team_short_name: Optional[str] = None
    ovr: Optional[int] = None
    series: Optional[str] = None
    series_texture_name: Optional[str] = None
    series_year: Optional[int] = None
    display_position: Optional[str] = None
    has_augment: Optional[bool] = None
    augment_text: Optional[str] = None
    augment_end_date: Optional[str] = None
    has_matchup: Optional[bool] = None
    stars: Optional[float] = None
    trend: Optional[Union[str, int, float]] = None
    new_rank: Optional[int] = None
    has_rank_change: Optional[bool] = None
    event: Optional[str] = None
    set_name: Optional[str] = None
    is_live_set: Optional[bool] = None
    ui_anim_index: Optional[int] = None


class ShowListingPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    listing_name: Optional[str] = None
    best_sell_price: Optional[Union[int, str]] = None
    best_buy_price: Optional[Union[int, str]] = None
    item: ShowListingItemPayload


class ShowListingsPagePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    page: int = 1
    per_page: int = 0
    total_pages: int = 1
    listings: list[ShowListingPayload] = Field(default_factory=list)


class ShowSeriesPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    series_id: Optional[Union[int, str]] = None
    name: str


class ShowBrandPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    brand_id: Optional[Union[int, str]] = None
    name: str


class ShowMetadataPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    series: list[ShowSeriesPayload] = Field(default_factory=list)
    brands: list[ShowBrandPayload] = Field(default_factory=list)
    sets: list[Any] = Field(default_factory=list)


class ShowUniversalProfilePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    username: str
    display_level: Optional[str] = None
    games_played: Optional[Union[int, str]] = None
    vanity: dict[str, Any] = Field(default_factory=dict)
    most_played_modes: dict[str, Any] = Field(default_factory=dict)
    lifetime_hitting_stats: list[dict[str, Any]] = Field(default_factory=list)
    lifetime_defensive_stats: list[dict[str, Any]] = Field(default_factory=list)
    online_data: list[dict[str, Any]] = Field(default_factory=list)


class ShowPlayerSearchPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    universal_profiles: list[ShowUniversalProfilePayload] = Field(default_factory=list)


class ShowRosterUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[Union[int, str]] = None
    title: Optional[str] = None
    name: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    published_at: Optional[str] = None
    updated_at: Optional[str] = None


class ShowRosterUpdatesPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    roster_updates: list[ShowRosterUpdatePayload] = Field(default_factory=list)


class LiveMarketListingResponse(BaseModel):
    uuid: str
    name: str
    best_buy_price: Optional[int] = None
    best_sell_price: Optional[int] = None
    spread: Optional[int] = None
    profit_after_tax: Optional[int] = None
    roi: Optional[float] = None
    position: Optional[str] = None
    series: Optional[str] = None
    team: Optional[str] = None
    overall: Optional[int] = None
    rarity: Optional[str] = None
    order_volume: int = 0
    liquidity_score: Optional[float] = None
    flip_score: Optional[float] = None
    last_seen_at: datetime


class LiveMarketListingListResponse(BaseModel):
    count: int
    items: list[LiveMarketListingResponse] = Field(default_factory=list)


class PriceHistoryPointResponse(BaseModel):
    timestamp: datetime
    buy_price: Optional[int] = None
    sell_price: Optional[int] = None


class PriceHistoryResponse(BaseModel):
    uuid: str
    name: Optional[str] = None
    days: int
    points: list[PriceHistoryPointResponse] = Field(default_factory=list)


class MarketMoverResponse(BaseModel):
    uuid: str
    name: str
    current_price: Optional[int] = None
    previous_price: Optional[int] = None
    change_amount: Optional[int] = None
    change_pct: Optional[float] = None
    trend_score: float
    position: Optional[str] = None
    series: Optional[str] = None
    team: Optional[str] = None
    rarity: Optional[str] = None
    points: int = 0
    last_seen_at: Optional[datetime] = None


class MarketMoverListResponse(BaseModel):
    count: int
    items: list[MarketMoverResponse] = Field(default_factory=list)


class ShowMetadataResponse(BaseModel):
    series: list[dict[str, Any]] = Field(default_factory=list)
    brands: list[dict[str, Any]] = Field(default_factory=list)
    sets: list[Any] = Field(default_factory=list)
    fetched_at: Optional[datetime] = None


class ShowPlayerSearchResponse(BaseModel):
    count: int
    items: list["ShowPlayerProfileResponse"] = Field(default_factory=list)


class ShowRosterUpdateListResponse(BaseModel):
    count: int
    items: list["ShowRosterUpdateResponse"] = Field(default_factory=list)


class MarketListingRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: str
    listing_name: Optional[str] = None
    best_sell_price: Optional[int] = None
    best_buy_price: Optional[int] = None
    spread: Optional[int] = None
    estimated_profit: Optional[int] = None
    roi_percent: Optional[float] = None
    source_page: Optional[int] = None
    last_seen_at: datetime


class ShowMetadataSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    series_json: list[dict[str, Any]]
    brands_json: list[dict[str, Any]]
    sets_json: list[Any]
    fetched_at: datetime


class ShowPlayerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    display_level: Optional[str] = None
    games_played: Optional[int] = None
    vanity_json: dict[str, Any]
    most_played_modes_json: dict[str, Any]
    lifetime_hitting_stats_json: list[dict[str, Any]]
    lifetime_defensive_stats_json: list[dict[str, Any]]
    online_data_json: list[dict[str, Any]]
    last_synced_at: datetime


class ShowRosterUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    remote_id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    last_synced_at: datetime


ShowPlayerSearchResponse.model_rebuild()
ShowRosterUpdateListResponse.model_rebuild()
