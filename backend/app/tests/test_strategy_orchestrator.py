from __future__ import annotations

from app.config import get_settings
from app.strategies.market_engine import MarketResult
from app.strategies.orchestrator import StrategyInputs, StrategyOrchestrator
from app.strategies.portfolio_engine import PortfolioResult
from app.utils.enums import MarketPhase, RecommendationAction


def test_orchestrator_prioritizes_sell_in_early_access():
    orchestrator = StrategyOrchestrator(get_settings().strategy_weights)
    result = orchestrator.evaluate(
        StrategyInputs(
            market_phase=MarketPhase.EARLY_ACCESS,
            market_result=MarketResult("item", RecommendationAction.WATCH, 1000, 55.0, 52.0, 70.0, 15.0, 45.0, "watch", {}),
            portfolio_result=PortfolioResult("item", RecommendationAction.SELL, 88.0, 20.0, 5.0, 40.0, 55.0, 82.0, "sell", {}),
            collection_progress_score=0.30,
            lineup_utility_score=0.40,
        )
    )
    assert result.action == RecommendationAction.SELL
