from __future__ import annotations

from app.config import get_settings
from app.strategies.roster_update_engine import RosterUpdateEngine, RosterUpdateInput
from app.utils.enums import RecommendationAction


def test_hot_hitter_with_stable_role_gets_buy_signal():
    engine = RosterUpdateEngine(get_settings().quicksell_tiers)
    result = engine.evaluate(
        RosterUpdateInput(
            item_id="greene",
            card_name="Riley Greene",
            current_overall=84,
            market_price=2800,
            quicksell_value=400,
            avg=0.318,
            ops=0.955,
            iso=0.244,
            hr=6,
            bb_rate=0.112,
            k_rate=0.182,
            rolling_7_ops=1.060,
            rolling_15_ops=0.998,
            rolling_30_ops=0.930,
            season_ops=0.915,
            lineup_spot=2,
            role_security=92.0,
            days_until_update=1.5,
            is_pitcher=False,
        )
    )
    assert result.action == RecommendationAction.BUY
    assert result.upgrade_probability >= 0.68


def test_hot_hitter_with_unstable_role_is_not_auto_buy():
    engine = RosterUpdateEngine(get_settings().quicksell_tiers)
    result = engine.evaluate(
        RosterUpdateInput(
            item_id="platoon-bat",
            card_name="Platoon Bat",
            current_overall=84,
            market_price=3600,
            quicksell_value=400,
            avg=0.308,
            ops=0.930,
            iso=0.210,
            hr=5,
            bb_rate=0.091,
            k_rate=0.245,
            rolling_7_ops=1.010,
            rolling_15_ops=0.955,
            rolling_30_ops=0.900,
            season_ops=0.870,
            lineup_spot=None,
            role_security=42.0,
            injury_risk=0.20,
            days_until_update=3.0,
            is_pitcher=False,
        )
    )
    assert result.action in {RecommendationAction.HOLD, RecommendationAction.AVOID}
    assert result.upgrade_probability < 0.68


def test_pitcher_with_strong_k9_spike_becomes_buy_target():
    engine = RosterUpdateEngine(get_settings().quicksell_tiers)
    result = engine.evaluate(
        RosterUpdateInput(
            item_id="spike-arm",
            card_name="Spike Arm",
            current_overall=79,
            market_price=190,
            quicksell_value=100,
            era=2.92,
            whip=1.03,
            k_per_9=11.8,
            bb_per_9=2.1,
            innings=34.0,
            rolling_7_era=1.84,
            rolling_15_era=2.42,
            season_era=3.05,
            rolling_7_whip=0.94,
            rolling_15_whip=1.04,
            rolling_7_k_rate=0.33,
            rolling_15_k_rate=0.29,
            rolling_7_bb_rate=0.06,
            rolling_15_bb_rate=0.08,
            probable_starter=True,
            role_security=88.0,
            days_until_update=2.0,
            is_pitcher=True,
        )
    )
    assert result.action == RecommendationAction.BUY
    assert result.upgrade_probability > 0.60


def test_player_near_quicksell_floor_gets_low_risk_buy_watch():
    engine = RosterUpdateEngine(get_settings().quicksell_tiers)
    result = engine.evaluate(
        RosterUpdateInput(
            item_id="floor-bat",
            card_name="Floor Bat",
            current_overall=79,
            market_price=175,
            quicksell_value=100,
            avg=0.291,
            ops=0.860,
            iso=0.175,
            hr=3,
            bb_rate=0.098,
            k_rate=0.201,
            rolling_7_ops=0.935,
            rolling_15_ops=0.890,
            rolling_30_ops=0.840,
            season_ops=0.835,
            lineup_spot=4,
            role_security=84.0,
            days_until_update=2.0,
            is_pitcher=False,
        )
    )
    assert result.action == RecommendationAction.BUY
    assert result.downside_risk <= 0.20
