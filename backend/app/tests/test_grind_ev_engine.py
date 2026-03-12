from __future__ import annotations

from app.config import get_settings
from app.strategies.grind_ev_engine import GrindEVEngine, GrindModeInput
from app.utils.enums import MarketPhase, RecommendationAction


def test_first_48_hours_prefers_grind_when_ev_higher():
    settings = get_settings()
    engine = GrindEVEngine(settings.feature_flags, settings.engine_thresholds)
    result = engine.evaluate(
        MarketPhase.EARLY_ACCESS,
        market_stub_per_hour=9000.0,
        modes=[
            GrindModeInput("WBC Mini Seasons", 7000.0, 3500.0, 1200.0, 1000.0, False),
            GrindModeInput("Conquest", 4000.0, 1200.0, 500.0, 250.0, False),
        ],
        launch_window_active=True,
    )
    assert result.action == RecommendationAction.GRIND
    assert result.best_mode_to_play_now == "WBC Mini Seasons"
    assert "first-48-hours" in result.rationale.lower()
