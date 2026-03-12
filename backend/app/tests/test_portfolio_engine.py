from __future__ import annotations

from app.config import get_settings
from app.strategies.portfolio_engine import PortfolioEngine, PortfolioInput
from app.utils.enums import MarketPhase, RecommendationAction


def test_non_live_default_sell_rule():
    engine = PortfolioEngine(get_settings().engine_thresholds)
    result = engine.evaluate(
        PortfolioInput(
            item_id="event",
            card_name="Event Bat",
            is_live_series=False,
            overall=95,
            quantity=1,
            avg_acquisition_cost=50000,
            current_market_value=72000,
            quicksell_value=10000,
            locked_for_collection=False,
            duplicate_count=0,
            scarcity_score=30.0,
            lineup_utility_score=40.0,
            collection_critical=False,
            phase=MarketPhase.EARLY_ACCESS,
        )
    )
    assert result.action == RecommendationAction.SELL
