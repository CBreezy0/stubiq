from __future__ import annotations

from app.config import get_settings
from app.strategies.market_engine import MarketEngine, MarketInput
from app.utils.enums import MarketPhase, RecommendationAction


def test_market_engine_avoids_false_early_access_buy():
    engine = MarketEngine(get_settings().engine_thresholds)
    result = engine.evaluate(
        MarketInput(
            item_id="card-1",
            name="Inflated Early Card",
            best_buy_order=18000,
            best_sell_order=22000,
            buy_now=22000,
            sell_now=18000,
            quicksell_value=400,
            rarity="Gold",
            series="Live",
            is_live_series=True,
            is_collection_critical=False,
            phase=MarketPhase.EARLY_ACCESS,
            recent_price_change_pct=0.20,
            volatility_score=75.0,
            trend_compression_score=35.0,
            aggregate_liquidity_score=45.0,
        )
    )
    assert result.action != RecommendationAction.BUY
    assert "distorted" in result.rationale.lower() or "early-access" in result.rationale.lower()


def test_market_engine_flags_floor_buy_after_launch_when_trend_compresses():
    engine = MarketEngine(get_settings().engine_thresholds)
    result = engine.evaluate(
        MarketInput(
            item_id="card-2",
            name="Near Floor Card",
            best_buy_order=102,
            best_sell_order=140,
            buy_now=140,
            sell_now=102,
            quicksell_value=100,
            rarity="Silver",
            series="Live",
            is_live_series=True,
            is_collection_critical=False,
            phase=MarketPhase.FULL_LAUNCH_SUPPLY_SHOCK,
            recent_price_change_pct=-0.25,
            volatility_score=40.0,
            trend_compression_score=78.0,
            aggregate_liquidity_score=65.0,
        )
    )
    assert result.action == RecommendationAction.BUY
    assert "floor" in result.rationale.lower() or "supply shock" in result.rationale.lower()
