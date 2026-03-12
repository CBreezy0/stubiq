"""Grind versus market expected value engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from app.config import FeatureFlags
from app.utils.enums import MarketPhase, RecommendationAction


@dataclass
class GrindModeInput:
    mode_name: str
    base_stub_value_per_hour: float
    pack_value_per_hour: float
    pxp_value_per_hour: float
    collection_progress_bonus: float = 0.0
    expires_soon: bool = False


@dataclass
class ModeResult:
    mode_name: str
    expected_value_per_hour: float
    rationale: str


@dataclass
class GrindResult:
    action: RecommendationAction
    best_mode_to_play_now: str
    expected_market_stubs_per_hour: float
    pack_value_estimate: float
    expected_value_per_hour_by_mode: List[ModeResult] = field(default_factory=list)
    rationale: str = ""


class GrindEVEngine:
    """Compares gameplay EV/hour against flipping EV/hour."""

    def __init__(self, feature_flags: FeatureFlags, thresholds: Dict[str, float]):
        self.feature_flags = feature_flags
        self.thresholds = thresholds

    def evaluate(
        self,
        phase: MarketPhase,
        market_stub_per_hour: float,
        modes: List[GrindModeInput],
        launch_window_active: bool = False,
    ) -> GrindResult:
        mode_results: List[ModeResult] = []
        for mode in modes:
            modifier = 1.0
            reasons = []
            if self.feature_flags.wbc_content_enabled and "WBC" in mode.mode_name.upper():
                modifier += 0.12
                reasons.append("WBC feature flag boost")
            if self.feature_flags.mini_seasons_9_inning_enabled and "MINI SEASONS" in mode.mode_name.upper():
                modifier += 0.08
                reasons.append("9-inning Mini Seasons boost")
            if self.feature_flags.pxp2_enabled:
                modifier += 0.05
                reasons.append("PXP2 enabled")
            if phase in {MarketPhase.EARLY_ACCESS, MarketPhase.FULL_LAUNCH_SUPPLY_SHOCK}:
                modifier += 0.10
                reasons.append("launch-week bundled reward premium")
            if mode.expires_soon:
                modifier += 0.05
                reasons.append("time-sensitive reward window")
            ev = (mode.base_stub_value_per_hour + mode.pack_value_per_hour + mode.pxp_value_per_hour + mode.collection_progress_bonus) * modifier
            mode_results.append(ModeResult(mode.mode_name, round(ev, 2), ", ".join(reasons) or "Base EV estimate"))

        best_mode = max(mode_results, key=lambda item: item.expected_value_per_hour) if mode_results else ModeResult("Market", 0.0, "No gameplay modes configured")
        launch_edge_pct = self.thresholds.get("launch_grind_ev_edge_pct", 0.05)
        required_grind_ev = market_stub_per_hour * (1.0 + launch_edge_pct) if launch_window_active else market_stub_per_hour
        action = RecommendationAction.GRIND if best_mode.expected_value_per_hour > required_grind_ev else RecommendationAction.FLIP

        if action == RecommendationAction.GRIND:
            if launch_window_active:
                rationale = (
                    f"First-48-hours rule: {best_mode.mode_name} returns {best_mode.expected_value_per_hour:.0f} EV/hour, "
                    f"clearing the launch premium over market EV/hour ({market_stub_per_hour:.0f})."
                )
            else:
                rationale = f"{best_mode.mode_name} offers {best_mode.expected_value_per_hour:.0f} EV/hour versus {market_stub_per_hour:.0f} market EV/hour."
        else:
            if launch_window_active:
                rationale = (
                    f"First-48-hours check failed: gameplay EV/hour ({best_mode.expected_value_per_hour:.0f}) does not clear the configured edge over market EV/hour ({market_stub_per_hour:.0f})."
                )
            else:
                rationale = f"Market EV/hour currently beats gameplay EV/hour ({market_stub_per_hour:.0f} vs {best_mode.expected_value_per_hour:.0f})."

        return GrindResult(
            action=action,
            best_mode_to_play_now=best_mode.mode_name,
            expected_market_stubs_per_hour=round(market_stub_per_hour, 2),
            pack_value_estimate=round(sum(mode.pack_value_per_hour for mode in modes), 2),
            expected_value_per_hour_by_mode=sorted(mode_results, key=lambda item: item.expected_value_per_hour, reverse=True),
            rationale=rationale,
        )
