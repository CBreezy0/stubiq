"""Portfolio management logic for owned cards."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from app.utils.enums import MarketPhase, RecommendationAction
from app.utils.scoring import clamp


@dataclass
class PortfolioInput:
    item_id: str
    card_name: str
    is_live_series: bool
    overall: int
    quantity: int
    avg_acquisition_cost: int
    current_market_value: int
    quicksell_value: int
    locked_for_collection: bool
    duplicate_count: int
    scarcity_score: float
    lineup_utility_score: float
    collection_critical: bool
    phase: MarketPhase


@dataclass
class PortfolioResult:
    item_id: str
    action: RecommendationAction
    sell_now_score: float
    hold_score: float
    lock_score: float
    flip_out_score: float
    portfolio_risk_score: float
    confidence: float
    rationale: str
    rationale_json: Dict[str, float] = field(default_factory=dict)


class PortfolioEngine:
    """Scores owned inventory for hold, sell, lock, or flip-out decisions."""

    def __init__(self, thresholds: Dict[str, float]):
        self.thresholds = thresholds

    def evaluate(self, data: PortfolioInput) -> PortfolioResult:
        profit_pct = 0.0
        if data.avg_acquisition_cost > 0:
            profit_pct = (data.current_market_value - data.avg_acquisition_cost) / float(data.avg_acquisition_cost)
        concentration_penalty = 18.0 if data.duplicate_count >= 2 else 0.0
        early_access_bonus = 15.0 if data.phase == MarketPhase.EARLY_ACCESS else 0.0

        sell_now_score = 20.0 + max(profit_pct, 0.0) * 60.0 + concentration_penalty + early_access_bonus
        hold_score = 20.0 + data.lineup_utility_score * 0.40 + (10.0 if data.is_live_series and data.overall >= 88 else 0.0)
        lock_score = 5.0 + (25.0 if data.locked_for_collection else 0.0) + (18.0 if data.collection_critical else 0.0)
        flip_out_score = 15.0 + data.duplicate_count * 10.0 + max(profit_pct, 0.0) * 40.0
        portfolio_risk_score = 20.0 + concentration_penalty + (0.0 if data.current_market_value <= data.quicksell_value * 1.2 else 10.0)

        action = RecommendationAction.HOLD
        rationale = "Owned card still has a balanced hold profile."

        if not data.is_live_series and data.scarcity_score < 55.0 and data.lineup_utility_score < 70.0:
            action = RecommendationAction.SELL
            rationale = "Non-live card lacks enough scarcity or lineup value to justify holding."
        elif data.is_live_series and data.overall >= 88 and data.duplicate_count == 0 and not data.locked_for_collection:
            action = RecommendationAction.HOLD
            rationale = "Live Series 88+ gatekeeper logic protects this core collection asset."
        elif data.duplicate_count > 0 and sell_now_score >= hold_score:
            action = RecommendationAction.SELL
            rationale = "Duplicate inventory should usually be sold unless scarcity is exceptional."
        elif data.collection_critical and not data.locked_for_collection and data.phase != MarketPhase.EARLY_ACCESS:
            action = RecommendationAction.LOCK
            rationale = "Collection-critical card is worth locking outside distorted early-access pricing."
        elif data.phase == MarketPhase.EARLY_ACCESS and not data.is_live_series:
            action = RecommendationAction.SELL
            rationale = "Early-access distortion favors selling non-live assets aggressively."

        confidence = clamp(max(sell_now_score, hold_score, lock_score, flip_out_score) * 0.85, 0.0, 100.0)
        return PortfolioResult(
            item_id=data.item_id,
            action=action,
            sell_now_score=round(clamp(sell_now_score), 2),
            hold_score=round(clamp(hold_score), 2),
            lock_score=round(clamp(lock_score), 2),
            flip_out_score=round(clamp(flip_out_score), 2),
            portfolio_risk_score=round(clamp(portfolio_risk_score), 2),
            confidence=round(confidence, 2),
            rationale=rationale,
            rationale_json={
                "sell_now_score": round(clamp(sell_now_score), 2),
                "hold_score": round(clamp(hold_score), 2),
                "lock_score": round(clamp(lock_score), 2),
                "flip_out_score": round(clamp(flip_out_score), 2),
            },
        )
