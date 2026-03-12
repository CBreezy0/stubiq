from __future__ import annotations

from app.config import get_settings
from app.strategies.collection_engine import CollectionEngine, CollectionInput
from app.utils.enums import MarketPhase


def test_owned_gatekeeper_boosts_division_priority():
    engine = CollectionEngine(get_settings().engine_thresholds)
    result = engine.evaluate(
        MarketPhase.STABILIZATION,
        [
            CollectionInput("a", "Gatekeeper A", "Dodgers", "NL West", "NL", 180000, 10000, 92, True, False, 1),
            CollectionInput("b", "Cheap A", "Dodgers", "NL West", "NL", 1500, 100, 71, False, False, 0),
            CollectionInput("c", "Cheap B", "Dodgers", "NL West", "NL", 1200, 100, 70, False, False, 0),
            CollectionInput("d", "Expensive B", "Phillies", "NL East", "NL", 90000, 10000, 90, False, False, 0),
            CollectionInput("e", "Cheap C", "Phillies", "NL East", "NL", 2200, 100, 70, False, False, 0),
        ],
    )
    assert result.ranked_division_targets[0].name == "NL West"
    assert "gatekeeper" in result.ranked_division_targets[0].rationale.lower()
    assert "remaining" in result.ranked_division_targets[0].rationale.lower()
