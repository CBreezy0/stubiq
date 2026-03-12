"""Market phase detection logic."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config import Settings
from app.utils.enums import MarketPhase


@dataclass
class PhaseObservation:
    as_of: datetime
    recent_market_drop_pct: float = 0.0
    recent_supply_growth_pct: float = 0.0
    content_drop_flag: bool = False
    stub_sale_flag: bool = False
    current_override: Optional[MarketPhase] = None
    next_update_at: Optional[datetime] = None
    last_update_at: Optional[datetime] = None


@dataclass
class PhaseDecision:
    phase: MarketPhase
    confidence: float
    rationale: str
    override_active: bool
    detected_at: datetime


class MarketPhaseEngine:
    """Detects current market phase using launch dates, updates, and market behavior."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.thresholds = settings.engine_thresholds

    def detect_phase(self, observation: PhaseObservation) -> PhaseDecision:
        now = observation.as_of.astimezone(timezone.utc)
        next_update_at = self._coerce_utc(observation.next_update_at)
        last_update_at = self._coerce_utc(observation.last_update_at)
        launch_shock_days = float(self.thresholds.get("full_launch_supply_shock_days", 3.0))
        late_cycle_days = float(self.thresholds.get("late_cycle_days", 210.0))
        if observation.current_override:
            return PhaseDecision(
                phase=observation.current_override,
                confidence=100.0,
                rationale="Manual market phase override is active.",
                override_active=True,
                detected_at=now,
            )

        if observation.stub_sale_flag:
            return PhaseDecision(MarketPhase.STUB_SALE, 88.0, "Stub sale conditions detected.", False, now)

        if observation.content_drop_flag:
            return PhaseDecision(
                MarketPhase.CONTENT_DROP,
                84.0,
                "Recent content release flag or supply-demand shock detected.",
                False,
                now,
            )

        if self.settings.feature_flags.launch_phase_logic_enabled:
            if self.settings.early_access_start_date <= now.date() < self.settings.full_launch_start_date:
                return PhaseDecision(
                    MarketPhase.EARLY_ACCESS,
                    95.0,
                    "March 13-16 style early-access distortion window: low supply, inflated prices, and weak fair-value signals.",
                    False,
                    now,
                )
            if self.settings.full_launch_start_date <= now.date() < (
                self.settings.full_launch_start_date + timedelta(days=launch_shock_days)
            ):
                return PhaseDecision(
                    MarketPhase.FULL_LAUNCH_SUPPLY_SHOCK,
                    92.0,
                    "Official full-launch supply shock window is active; baseline prices should reset off post-launch supply.",
                    False,
                    now,
                )

        if next_update_at:
            hours_to_update = (next_update_at - now).total_seconds() / 3600.0
            if 0.0 <= hours_to_update <= float(self.thresholds.get("pre_update_hours", 48.0)):
                return PhaseDecision(
                    MarketPhase.PRE_ATTRIBUTE_UPDATE,
                    82.0,
                    "Roster update is approaching; roster-investment sensitivity increased.",
                    False,
                    now,
                )

        if last_update_at:
            hours_since_update = (now - last_update_at).total_seconds() / 3600.0
            if 0.0 <= hours_since_update <= float(self.thresholds.get("post_update_hours", 24.0)):
                return PhaseDecision(
                    MarketPhase.POST_ATTRIBUTE_UPDATE,
                    82.0,
                    "Fresh roster update reaction window is active.",
                    False,
                    now,
                )

        if (
            observation.recent_market_drop_pct <= -abs(float(self.thresholds.get("launch_shock_drop_pct", 0.18)))
            and observation.recent_supply_growth_pct > 0.15
        ):
            return PhaseDecision(
                MarketPhase.FULL_LAUNCH_SUPPLY_SHOCK,
                78.0,
                "Recent market crash and supply spike resemble a launch-style supply shock.",
                False,
                now,
            )

        game_age_days = (now.date() - self.settings.full_launch_start_date).days
        if game_age_days > late_cycle_days:
            return PhaseDecision(MarketPhase.LATE_CYCLE, 70.0, "Late-cycle market environment detected.", False, now)

        return PhaseDecision(
            MarketPhase.STABILIZATION,
            72.0,
            "Market behavior appears closer to post-launch stabilization than shock conditions.",
            False,
            now,
        )

    def _coerce_utc(self, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
