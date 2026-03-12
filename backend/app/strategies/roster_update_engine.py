"""Live Series roster update investment logic.

This engine models the part of Diamond Dynasty investing that matters most during the MLB season:
periodic roster updates. SDS typically adjusts Live Series ratings based on real MLB performance. The
most valuable jumps to predict are 79 -> 80 and 84 -> 85 because they change quicksell tiers and often
create the largest low-risk investment windows.

The scoring model stays deliberately explainable:
- recent_performance_score: how strong the player's short-window production is right now
- season_performance_score: whether the hot streak is supported by broader season skill
- role_security_score: whether the player actually has a stable lineup / rotation / bullpen role
- stat_trend_score: whether shorter windows are improving over longer windows
- hype_score: price and performance momentum proxy for market demand

These are combined into an upgrade probability, then paired with a downside model based on quicksell
support and current market price. The resulting recommendation is BUY / HOLD / SELL / AVOID.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.utils.enums import RecommendationAction
from app.utils.scoring import clamp


@dataclass
class RosterUpdateInput:
    item_id: str
    card_name: str
    player_name: Optional[str] = None
    mlb_player_id: Optional[int] = None
    current_overall: int = 0
    market_price: int = 0
    quicksell_value: int = 0
    series: Optional[str] = None
    rarity: Optional[str] = None
    avg: Optional[float] = None
    ops: Optional[float] = None
    iso: Optional[float] = None
    hr: Optional[int] = None
    bb_rate: Optional[float] = None
    k_rate: Optional[float] = None
    era: Optional[float] = None
    whip: Optional[float] = None
    k_per_9: Optional[float] = None
    bb_per_9: Optional[float] = None
    innings: Optional[float] = None
    rolling_7_ops: Optional[float] = None
    rolling_15_ops: Optional[float] = None
    rolling_30_ops: Optional[float] = None
    season_ops: Optional[float] = None
    rolling_7_era: Optional[float] = None
    rolling_15_era: Optional[float] = None
    season_era: Optional[float] = None
    rolling_7_whip: Optional[float] = None
    rolling_15_whip: Optional[float] = None
    rolling_7_k_rate: Optional[float] = None
    rolling_15_k_rate: Optional[float] = None
    rolling_7_bb_rate: Optional[float] = None
    rolling_15_bb_rate: Optional[float] = None
    lineup_spot: Optional[int] = None
    role_security: float = 50.0
    probable_starter: bool = False
    saves: int = 0
    holds: int = 0
    injury_risk: float = 0.0
    days_until_update: Optional[float] = None
    is_pitcher: bool = False
    price_momentum: float = 0.0
    stat_momentum: Optional[float] = None
    social_hype_factor: float = 0.0


@dataclass
class RosterUpdateResult:
    item_id: str
    player_name: str
    mlb_player_id: Optional[int]
    current_overall: int
    action: RecommendationAction
    upgrade_probability: float
    downgrade_probability: float
    expected_quicksell_value: int
    expected_market_value: float
    expected_profit: float
    downside_risk: float
    confidence: float
    rationale: str
    rationale_json: Dict[str, Any] = field(default_factory=dict)


class RosterUpdateEngine:
    """Predicts roster-update outcomes for Live Series investments.

    The model is intentionally rules-driven rather than opaque. That keeps day-one launch tuning fast
    and makes every recommendation traceable to form, role stability, trend quality, and downside.
    """

    def __init__(self, quicksell_tiers: Dict[str, int], risk_margin_multiplier: float = 0.15):
        self.quicksell_tiers = quicksell_tiers
        self.risk_margin_multiplier = risk_margin_multiplier

    def evaluate(self, data: RosterUpdateInput) -> RosterUpdateResult:
        """Return a buy/hold/sell/avoid recommendation for one Live Series player."""
        player_name = data.player_name or data.card_name
        recent_performance_score = self._recent_performance_score(data)
        season_performance_score = self._season_performance_score(data)
        role_security_score = self._role_security_score(data)
        stat_trend_score = self._stat_trend_score(data)
        hype_score = self._hype_score(data, recent_performance_score, stat_trend_score)

        upgrade_score = (
            0.35 * recent_performance_score
            + 0.25 * season_performance_score
            + 0.15 * role_security_score
            + 0.15 * stat_trend_score
            + 0.10 * hype_score
        )
        urgency_bonus = 0.0
        if data.days_until_update is not None:
            if data.days_until_update <= 2:
                urgency_bonus = 8.0
            elif data.days_until_update <= 5:
                urgency_bonus = 4.0

        injury_penalty = clamp(data.injury_risk * 20.0, 0.0, 20.0)
        role_instability_penalty = clamp(max(0.0, 60.0 - role_security_score) * 0.30, 0.0, 12.0)
        target_bonus = 6.0 if data.current_overall in {79, 84} else (2.0 if data.current_overall >= 88 else 0.0)
        upgrade_probability = clamp((upgrade_score + urgency_bonus + target_bonus - injury_penalty - role_instability_penalty) / 100.0, 0.0, 1.0)

        downgrade_probability = clamp(
            (
                (100.0 - season_performance_score) * 0.40
                + (100.0 - recent_performance_score) * 0.25
                + (100.0 - role_security_score) * 0.15
                + injury_penalty * 1.2
            )
            / 100.0,
            0.0,
            1.0,
        )

        target_overall = self._target_overall(data.current_overall, upgrade_probability)
        expected_quicksell = max(data.quicksell_value, self._quicksell_for_overall(target_overall))
        downside_risk = self._downside_risk(data, expected_quicksell, role_security_score, hype_score)
        expected_market_value = self._expected_market_price(data, upgrade_probability, downside_risk, expected_quicksell, hype_score)
        expected_profit = round(expected_market_value - data.market_price, 2)

        action, rationale = self._recommend_action(
            data,
            upgrade_probability,
            downgrade_probability,
            expected_quicksell,
            expected_profit,
            downside_risk,
            role_security_score,
        )

        confidence = clamp(
            upgrade_probability * 100.0 * 0.55
            + (1.0 - downside_risk) * 100.0 * 0.25
            + role_security_score * 0.10
            + stat_trend_score * 0.10,
            0.0,
            100.0,
        )

        return RosterUpdateResult(
            item_id=data.item_id,
            player_name=player_name,
            mlb_player_id=data.mlb_player_id,
            current_overall=data.current_overall,
            action=action,
            upgrade_probability=round(upgrade_probability, 4),
            downgrade_probability=round(downgrade_probability, 4),
            expected_quicksell_value=int(expected_quicksell),
            expected_market_value=round(expected_market_value, 2),
            expected_profit=expected_profit,
            downside_risk=round(downside_risk, 4),
            confidence=round(confidence, 2),
            rationale=rationale,
            rationale_json={
                "recent_performance_score": round(recent_performance_score, 2),
                "season_performance_score": round(season_performance_score, 2),
                "role_security_score": round(role_security_score, 2),
                "stat_trend_score": round(stat_trend_score, 2),
                "hype_score": round(hype_score, 2),
                "upgrade_score": round(upgrade_score, 2),
                "urgency_bonus": round(urgency_bonus, 2),
                "injury_penalty": round(injury_penalty, 2),
                "role_instability_penalty": round(role_instability_penalty, 2),
                "near_quicksell_floor": data.market_price <= self._risk_margin_price(expected_quicksell),
                "price_momentum": round(data.price_momentum, 4),
                "stat_momentum": round(self._safe(data.stat_momentum), 4),
                "social_hype_factor": round(data.social_hype_factor, 4),
            },
        )

    def _recommend_action(
        self,
        data: RosterUpdateInput,
        upgrade_probability: float,
        downgrade_probability: float,
        expected_quicksell: int,
        expected_profit: float,
        downside_risk: float,
        role_security_score: float,
    ) -> tuple[RecommendationAction, str]:
        triple_quicksell = data.market_price >= expected_quicksell * 3
        near_floor = data.market_price <= self._risk_margin_price(expected_quicksell)

        if triple_quicksell and data.current_overall in {79, 84} and upgrade_probability < 0.85:
            return (
                RecommendationAction.SELL,
                "Market price is already at least 3x quicksell, so the upside is no longer attractive relative to update risk.",
            )
        if data.current_overall == 84 and upgrade_probability >= 0.68 and downside_risk <= 0.40 and expected_profit > 0 and role_security_score >= 60.0:
            return (
                RecommendationAction.BUY,
                "84-to-85 candidate shows strong recent and season skill support with manageable downside to the next quicksell tier.",
            )
        if data.current_overall == 79 and upgrade_probability >= 0.62 and downside_risk <= 0.45 and expected_profit > 0 and role_security_score >= 58.0:
            return (
                RecommendationAction.BUY,
                "79-to-80 bulk target has enough performance momentum and role stability to justify accumulation.",
            )
        if near_floor and upgrade_probability >= 0.52 and expected_profit >= 0 and role_security_score >= 55.0:
            return (
                RecommendationAction.BUY,
                "Current price is close to quicksell support, so downside is limited while the update thesis remains viable.",
            )
        if downgrade_probability >= 0.55 or downside_risk >= 0.78:
            return (
                RecommendationAction.SELL,
                "Role instability or weak skill support makes the downside too large to keep holding ahead of the update.",
            )
        if upgrade_probability >= 0.55:
            return (
                RecommendationAction.HOLD,
                "Upgrade signal is positive, but the entry price is no longer clean enough to add aggressively.",
            )
        return RecommendationAction.AVOID, "The current form, role, and price setup do not create a strong update edge."

    def _recent_performance_score(self, data: RosterUpdateInput) -> float:
        if data.is_pitcher:
            era_score = clamp((5.25 - self._first(data.rolling_7_era, data.rolling_15_era, data.season_era, 4.20)) / 3.5 * 35.0, 0.0, 35.0)
            whip_score = clamp((1.45 - self._first(data.rolling_7_whip, data.whip, 1.28)) / 0.65 * 20.0, 0.0, 20.0)
            k_score = clamp((self._first(data.k_per_9, 8.5) - 7.0) / 6.0 * 25.0, 0.0, 25.0)
            command_score = clamp((3.8 - self._first(data.bb_per_9, 3.2)) / 2.5 * 10.0, 0.0, 10.0)
            leverage_score = clamp((data.saves * 2.5) + (data.holds * 1.5), 0.0, 10.0)
            return clamp(era_score + whip_score + k_score + command_score + leverage_score, 0.0, 100.0)

        avg_score = clamp((self._first(data.avg, 0.250) - 0.235) / 0.09 * 18.0, 0.0, 18.0)
        ops_score = clamp((self._first(data.rolling_7_ops, data.rolling_15_ops, data.ops, 0.720) - 0.700) / 0.35 * 38.0, 0.0, 38.0)
        iso_score = clamp((self._first(data.iso, 0.140) - 0.125) / 0.18 * 15.0, 0.0, 15.0)
        hr_score = clamp(self._first(data.hr, 0) * 2.2, 0.0, 12.0)
        discipline_score = clamp((self._first(data.bb_rate, 0.07) * 100.0) - (self._first(data.k_rate, 0.24) * 45.0) + 8.0, 0.0, 17.0)
        return clamp(avg_score + ops_score + iso_score + hr_score + discipline_score, 0.0, 100.0)

    def _season_performance_score(self, data: RosterUpdateInput) -> float:
        if data.is_pitcher:
            season_era_score = clamp((5.10 - self._first(data.season_era, data.rolling_15_era, 4.25)) / 3.3 * 42.0, 0.0, 42.0)
            k_score = clamp((self._first(data.k_per_9, 8.0) - 7.0) / 5.5 * 24.0, 0.0, 24.0)
            bb_score = clamp((3.8 - self._first(data.bb_per_9, 3.1)) / 2.4 * 14.0, 0.0, 14.0)
            workload_score = clamp(self._first(data.innings, 0.0) / 55.0 * 20.0, 0.0, 20.0)
            return clamp(season_era_score + k_score + bb_score + workload_score, 0.0, 100.0)

        season_ops = self._first(data.season_ops, data.ops, 0.720)
        ops_score = clamp((season_ops - 0.700) / 0.28 * 40.0, 0.0, 40.0)
        iso_score = clamp((self._first(data.iso, 0.140) - 0.125) / 0.16 * 18.0, 0.0, 18.0)
        avg_score = clamp((self._first(data.avg, 0.250) - 0.240) / 0.07 * 15.0, 0.0, 15.0)
        discipline_score = clamp((self._first(data.bb_rate, 0.07) * 100.0) - (self._first(data.k_rate, 0.24) * 35.0) + 6.0, 0.0, 15.0)
        production_score = clamp(self._first(data.hr, 0) * 2.0, 0.0, 12.0)
        return clamp(ops_score + iso_score + avg_score + discipline_score + production_score, 0.0, 100.0)

    def _role_security_score(self, data: RosterUpdateInput) -> float:
        base = clamp(data.role_security, 0.0, 100.0)
        if data.is_pitcher and data.probable_starter:
            base += 8.0
        if not data.is_pitcher and data.lineup_spot is not None:
            if data.lineup_spot <= 4:
                base += 10.0
            elif data.lineup_spot <= 6:
                base += 5.0
        if data.saves >= 4:
            base += 8.0
        if data.holds >= 6:
            base += 5.0
        return clamp(base - data.injury_risk * 18.0, 0.0, 100.0)

    def _stat_trend_score(self, data: RosterUpdateInput) -> float:
        if data.stat_momentum is not None:
            return clamp(50.0 + data.stat_momentum * 120.0, 0.0, 100.0)

        if data.is_pitcher:
            baseline = self._first(data.season_era, data.rolling_15_era, 4.20)
            recent = self._first(data.rolling_7_era, data.rolling_15_era, baseline)
            improvement = baseline - recent
            command_improvement = self._first(data.rolling_15_bb_rate, 0.09) - self._first(data.rolling_7_bb_rate, 0.09)
            return clamp(50.0 + improvement * 18.0 + command_improvement * 220.0, 0.0, 100.0)

        baseline = self._first(data.rolling_30_ops, data.season_ops, data.ops, 0.720)
        recent = self._first(data.rolling_7_ops, data.rolling_15_ops, baseline)
        mid = self._first(data.rolling_15_ops, baseline)
        return clamp(50.0 + (recent - baseline) * 180.0 + (recent - mid) * 120.0, 0.0, 100.0)

    def _hype_score(self, data: RosterUpdateInput, recent_performance_score: float, trend_score: float) -> float:
        stat_hype = clamp((recent_performance_score - 50.0) * 0.8, 0.0, 55.0)
        price_hype = clamp(data.price_momentum * 250.0 + 20.0, 0.0, 30.0)
        social_hype = clamp(data.social_hype_factor * 100.0, 0.0, 15.0)
        trend_bonus = clamp((trend_score - 50.0) * 0.3, 0.0, 10.0)
        return clamp(stat_hype + price_hype + social_hype + trend_bonus, 0.0, 100.0)

    def _downside_risk(self, data: RosterUpdateInput, expected_quicksell: int, role_security_score: float, hype_score: float) -> float:
        price_floor = self._risk_margin_price(expected_quicksell)
        if data.market_price <= price_floor:
            base_risk = 0.06
        else:
            premium_ratio = (data.market_price - expected_quicksell) / max(expected_quicksell, 1)
            base_risk = clamp(premium_ratio / 3.0, 0.0, 1.0)
        stability_modifier = (100.0 - role_security_score) / 250.0
        hype_modifier = clamp((hype_score - 65.0) / 120.0, 0.0, 0.20)
        return clamp(base_risk + stability_modifier + hype_modifier + data.injury_risk * 0.20, 0.0, 1.0)

    def _expected_market_price(
        self,
        data: RosterUpdateInput,
        upgrade_probability: float,
        downside_risk: float,
        expected_quicksell: int,
        hype_score: float,
    ) -> float:
        tier_step_bonus = max(expected_quicksell - data.quicksell_value, 0)
        momentum_bonus = clamp(data.price_momentum, -0.30, 0.50) * data.market_price
        hype_bonus = (hype_score / 100.0) * data.market_price * 0.10
        uplift = data.market_price * (upgrade_probability * 0.55 - downside_risk * 0.20)
        return max(expected_quicksell, round(data.market_price + uplift + tier_step_bonus + momentum_bonus * 0.25 + hype_bonus, 2))

    def _target_overall(self, current_overall: int, upgrade_probability: float) -> int:
        if current_overall in {79, 84} and upgrade_probability >= 0.45:
            return current_overall + 1
        return current_overall

    def _risk_margin_price(self, quicksell_value: int) -> int:
        return int(quicksell_value + max(100.0, quicksell_value * self.risk_margin_multiplier))

    def _quicksell_for_overall(self, overall: int) -> int:
        for bucket, value in self.quicksell_tiers.items():
            lower, upper = bucket.split("-")
            if int(lower) <= overall <= int(upper):
                return int(value)
        return 0

    def _first(self, *values):
        for value in values:
            if value is not None:
                return value
        return 0.0

    def _safe(self, value: Optional[float]) -> float:
        return 0.0 if value is None else value
