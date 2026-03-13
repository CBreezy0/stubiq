"""Primary ORM entity definitions."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.enums import MarketPhase, RecommendationAction, RecommendationType, TransactionAction, UpdateType
from app.utils.time import utcnow


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Card(TimestampMixin, Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    mlb_player_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    series: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    team: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    division: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    league: Mapped[Optional[str]] = mapped_column(String(16), index=True, nullable=True)
    overall: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    rarity: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    display_position: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_pitcher: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_live_series: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    quicksell_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_sellable: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    listings_snapshots: Mapped[list["ListingsSnapshot"]] = relationship(back_populates="card")
    market_aggregates: Mapped[list["MarketHistoryAggregate"]] = relationship(back_populates="card")
    portfolio_positions: Mapped[list["PortfolioPosition"]] = relationship(back_populates="card")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="card")
    strategy_recommendations: Mapped[list["StrategyRecommendation"]] = relationship(back_populates="card")
    roster_update_predictions: Mapped[list["RosterUpdatePrediction"]] = relationship(back_populates="card")


class ListingsSnapshot(Base):
    __tablename__ = "listings_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String(128), ForeignKey("cards.item_id"), index=True)
    buy_now: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sell_now: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    best_buy_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    best_sell_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    spread: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tax_adjusted_spread: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)

    card: Mapped[Card] = relationship(back_populates="listings_snapshots")


class MarketHistoryAggregate(TimestampMixin, Base):
    __tablename__ = "market_history_aggregates"
    __table_args__ = (UniqueConstraint("item_id", "phase", name="uq_market_history_aggregate_item_phase"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String(128), ForeignKey("cards.item_id"), index=True)
    phase: Mapped[MarketPhase] = mapped_column(Enum(MarketPhase), index=True)
    avg_price_15m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_price_1h: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_price_6h: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_price_24h: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volatility_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    liquidity_score: Mapped[Optional[float]] = mapped_column(Float, index=True, nullable=True)

    card: Mapped[Card] = relationship(back_populates="market_aggregates")


class PlayerStatsDaily(Base):
    __tablename__ = "player_stats_daily"
    __table_args__ = (UniqueConstraint("mlb_player_id", "stat_date", name="uq_player_stats_daily_player_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_name: Mapped[str] = mapped_column(String(255), index=True)
    mlb_player_id: Mapped[int] = mapped_column(Integer, index=True)
    stat_date: Mapped[date] = mapped_column(Date, index=True)
    season_year: Mapped[int] = mapped_column(Integer, index=True)
    games: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    obp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    slg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ops: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    iso: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rbi: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bb_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    k_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    era: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    whip: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    k_per_9: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bb_per_9: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    saves: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    holds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    innings: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class PlayerStatsRolling(Base):
    __tablename__ = "player_stats_rolling"
    __table_args__ = (UniqueConstraint("mlb_player_id", "window_days", "as_of_date", name="uq_player_stats_rolling_window"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mlb_player_id: Mapped[int] = mapped_column(Integer, index=True)
    window_days: Mapped[int] = mapped_column(Integer, index=True)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    obp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    slg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ops: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    iso: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bb_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    k_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    era: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    whip: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    k_per_9: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bb_per_9: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    saves: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    holds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    innings: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class LineupStatus(Base):
    __tablename__ = "lineup_status"
    __table_args__ = (UniqueConstraint("mlb_player_id", "game_date", name="uq_lineup_status_player_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mlb_player_id: Mapped[int] = mapped_column(Integer, index=True)
    game_date: Mapped[date] = mapped_column(Date, index=True)
    team: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    lineup_spot: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    starting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opponent: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    handedness_context: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class ProbableStarter(Base):
    __tablename__ = "probable_starters"
    __table_args__ = (UniqueConstraint("mlb_player_id", "game_date", name="uq_probable_starter_player_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_date: Mapped[date] = mapped_column(Date, index=True)
    team: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    mlb_player_id: Mapped[int] = mapped_column(Integer, index=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opponent: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)


class RosterUpdateCalendar(Base):
    __tablename__ = "roster_update_calendar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    update_type: Mapped[UpdateType] = mapped_column(Enum(UpdateType), index=True)
    update_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PortfolioPosition(TimestampMixin, Base):
    __tablename__ = "portfolio_positions"
    __table_args__ = (UniqueConstraint("user_id", "item_id", name="uq_portfolio_position_user_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    item_id: Mapped[str] = mapped_column(String(128), ForeignKey("cards.item_id"), index=True)
    card_name: Mapped[str] = mapped_column(String(255), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    avg_acquisition_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    current_market_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quicksell_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    locked_for_collection: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    user: Mapped["User"] = relationship(back_populates="portfolio_positions")
    card: Mapped[Card] = relationship(back_populates="portfolio_positions")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    item_id: Mapped[str] = mapped_column(String(128), ForeignKey("cards.item_id"), index=True)
    action: Mapped[TransactionAction] = mapped_column(Enum(TransactionAction), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    total_value: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="transactions")
    card: Mapped[Card] = relationship(back_populates="transactions")


class ProgramReward(Base):
    __tablename__ = "program_rewards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_name: Mapped[str] = mapped_column(String(255), index=True)
    mode_name: Mapped[str] = mapped_column(String(255), index=True)
    reward_type: Mapped[str] = mapped_column(String(128), nullable=False)
    reward_item_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    reward_stub_value_estimate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class MarketPhaseHistory(Base):
    __tablename__ = "market_phase_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phase: Mapped[MarketPhase] = mapped_column(Enum(MarketPhase), index=True)
    phase_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    phase_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RosterUpdatePrediction(Base):
    __tablename__ = "roster_update_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[Optional[str]] = mapped_column(String(128), ForeignKey("cards.item_id"), index=True, nullable=True)
    player_name: Mapped[str] = mapped_column(String(255), index=True)
    mlb_player_id: Mapped[int] = mapped_column(Integer, index=True)
    current_ovr: Mapped[int] = mapped_column(Integer, index=True)
    current_price: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_quicksell_value: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_market_price: Mapped[float] = mapped_column(Float, nullable=False)
    upgrade_probability: Mapped[float] = mapped_column(Float, nullable=False)
    expected_profit: Mapped[float] = mapped_column(Float, nullable=False)
    downside_risk: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[RecommendationAction] = mapped_column(Enum(RecommendationAction), index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rationale_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    card: Mapped[Optional[Card]] = relationship(back_populates="roster_update_predictions")


class StrategyRecommendation(Base):
    __tablename__ = "strategy_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[Optional[str]] = mapped_column(String(128), ForeignKey("cards.item_id"), index=True, nullable=True)
    recommendation_type: Mapped[RecommendationType] = mapped_column(Enum(RecommendationType), index=True)
    action: Mapped[RecommendationAction] = mapped_column(Enum(RecommendationAction), index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    expected_profit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rationale_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    card: Mapped[Optional[Card]] = relationship(back_populates="strategy_recommendations")


class SystemSetting(TimestampMixin, Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
