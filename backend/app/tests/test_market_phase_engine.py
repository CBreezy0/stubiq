from __future__ import annotations

from datetime import datetime, timezone

from app.config import get_settings
from app.strategies.phase import MarketPhaseEngine, PhaseObservation
from app.utils.enums import MarketPhase


def test_early_access_window_detected():
    engine = MarketPhaseEngine(get_settings())
    result = engine.detect_phase(
        PhaseObservation(as_of=datetime(2026, 3, 14, 12, 0, tzinfo=timezone.utc))
    )
    assert result.phase == MarketPhase.EARLY_ACCESS


def test_full_launch_supply_shock_detected():
    engine = MarketPhaseEngine(get_settings())
    result = engine.detect_phase(
        PhaseObservation(as_of=datetime(2026, 3, 17, 16, 0, tzinfo=timezone.utc))
    )
    assert result.phase == MarketPhase.FULL_LAUNCH_SUPPLY_SHOCK
