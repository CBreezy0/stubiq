"""Combines strategy engine outputs into a single decision layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from app.utils.enums import MarketPhase, RecommendationAction
from app.utils.scoring import clamp, weighted_sum

from .market_engine import MarketResult
from .portfolio_engine import PortfolioResult
from .roster_update_engine import RosterUpdateResult


@dataclass
class StrategyInputs:
    market_phase: MarketPhase
    market_result: Optional[MarketResult] = None
    roster_result: Optional[RosterUpdateResult] = None
    portfolio_result: Optional[PortfolioResult] = None
    collection_progress_score: float = 0.0
    lineup_utility_score: float = 0.0


@dataclass
class StrategyResult:
    action: RecommendationAction
    confidence: float
    overall_score: float
    rationale: str
    rationale_json: Dict[str, float] = field(default_factory=dict)


class StrategyOrchestrator:
    """Phase-aware aggregation of all strategy signals."""

    def __init__(self, base_weights: Dict[str, float]):
        self.base_weights = dict(base_weights)

    def evaluate(self, inputs: StrategyInputs) -> StrategyResult:
        weights = self._phase_adjusted_weights(inputs.market_phase)
        market_action_score = self._market_stub_growth(inputs.market_result)
        downside = self._downside_protection(inputs.market_result, inputs.portfolio_result, inputs.roster_result)
        liquidity = inputs.market_result.liquidity_score if inputs.market_result else 35.0
        values = {
            "stub_growth_score": market_action_score,
            "collection_progress_score": inputs.collection_progress_score,
            "downside_protection_score": downside,
            "liquidity_score": liquidity,
            "lineup_utility_score": inputs.lineup_utility_score,
        }
        overall_score = weighted_sum(values, weights) * 100.0 if max(weights.values()) <= 1.0 else weighted_sum(values, weights)
        action = self._resolve_action(inputs.market_phase, inputs.market_result, inputs.roster_result, inputs.portfolio_result)
        rationale = self._build_rationale(action, inputs.market_phase)
        confidence = clamp(overall_score, 0.0, 100.0)
        return StrategyResult(
            action=action,
            confidence=round(confidence, 2),
            overall_score=round(overall_score, 2),
            rationale=rationale,
            rationale_json={key: round(value, 2) for key, value in values.items()},
        )

    def _phase_adjusted_weights(self, phase: MarketPhase) -> Dict[str, float]:
        weights = dict(self.base_weights)
        if phase == MarketPhase.EARLY_ACCESS:
            weights["liquidity_score"] += 0.05
            weights["collection_progress_score"] -= 0.10
            weights["stub_growth_score"] += 0.05
        elif phase == MarketPhase.FULL_LAUNCH_SUPPLY_SHOCK:
            weights["stub_growth_score"] += 0.05
            weights["downside_protection_score"] += 0.05
            weights["collection_progress_score"] += 0.03
        elif phase == MarketPhase.PRE_ATTRIBUTE_UPDATE:
            weights["stub_growth_score"] += 0.08
        elif phase == MarketPhase.CONTENT_DROP:
            weights["stub_growth_score"] += 0.04
            weights["liquidity_score"] += 0.03
        elif phase == MarketPhase.LATE_CYCLE:
            weights["collection_progress_score"] += 0.08
            weights["lineup_utility_score"] += 0.05
        total = sum(weights.values())
        return {key: value / total for key, value in weights.items()}

    def _market_stub_growth(self, market_result: Optional[MarketResult]) -> float:
        if not market_result:
            return 0.25
        action_bonus = {
            RecommendationAction.FLIP: 0.90,
            RecommendationAction.BUY: 0.75,
            RecommendationAction.WATCH: 0.45,
            RecommendationAction.IGNORE: 0.20,
            RecommendationAction.AVOID: 0.10,
        }.get(market_result.action, 0.30)
        return clamp(action_bonus + market_result.expected_profit_per_flip / 10000.0, 0.0, 1.0)

    def _downside_protection(
        self,
        market_result: Optional[MarketResult],
        portfolio_result: Optional[PortfolioResult],
        roster_result: Optional[RosterUpdateResult],
    ) -> float:
        market_component = 1.0 - ((market_result.risk_score / 100.0) if market_result else 0.45)
        portfolio_component = 1.0 - ((portfolio_result.portfolio_risk_score / 100.0) if portfolio_result else 0.40)
        roster_component = 1.0 - ((roster_result.downgrade_probability / 100.0) if roster_result else 0.35)
        return clamp((market_component + portfolio_component + roster_component) / 3.0, 0.0, 1.0)

    def _resolve_action(
        self,
        phase: MarketPhase,
        market_result: Optional[MarketResult],
        roster_result: Optional[RosterUpdateResult],
        portfolio_result: Optional[PortfolioResult],
    ) -> RecommendationAction:
        if phase == MarketPhase.EARLY_ACCESS and portfolio_result and portfolio_result.action == RecommendationAction.SELL:
            return RecommendationAction.SELL
        if portfolio_result and portfolio_result.action in {RecommendationAction.SELL, RecommendationAction.LOCK}:
            return portfolio_result.action
        if roster_result and roster_result.action in {RecommendationAction.BUY, RecommendationAction.SELL, RecommendationAction.HOLD}:
            return roster_result.action
        if market_result and market_result.action in {RecommendationAction.FLIP, RecommendationAction.BUY, RecommendationAction.WATCH}:
            return market_result.action
        return RecommendationAction.HOLD

    def _build_rationale(self, action: RecommendationAction, phase: MarketPhase) -> str:
        if action == RecommendationAction.SELL and phase == MarketPhase.EARLY_ACCESS:
            return "Launch-week liquidity is prioritized over locking or slow holds."
        if action == RecommendationAction.BUY and phase == MarketPhase.FULL_LAUNCH_SUPPLY_SHOCK:
            return "Supply shock has improved long-run buy conditions without relying on early-access baselines."
        if action == RecommendationAction.FLIP:
            return "Market spread and liquidity support repeatable stub growth."
        if action == RecommendationAction.LOCK:
            return "Collection progress and gatekeeper protection now outweigh short-run stub liquidity."
        return "Composite strategy scores favor patience over forced action."
