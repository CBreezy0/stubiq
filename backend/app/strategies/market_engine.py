"""Market flipping and floor-buy strategy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from app.utils.enums import MarketPhase, RecommendationAction
from app.utils.scoring import clamp, floor_proximity, tax_adjusted_profit


@dataclass
class MarketInput:
    item_id: str
    name: str
    best_buy_order: Optional[int]
    best_sell_order: Optional[int]
    buy_now: Optional[int]
    sell_now: Optional[int]
    quicksell_value: Optional[int]
    rarity: Optional[str]
    series: Optional[str]
    is_live_series: bool
    is_collection_critical: bool
    phase: MarketPhase
    recent_price_change_pct: float = 0.0
    volatility_score: float = 50.0
    trend_compression_score: float = 50.0
    stable_reference_price: Optional[float] = None
    listing_depth: Optional[int] = None
    aggregate_liquidity_score: float = 50.0
    tax_rate: float = 0.10
    content_drop_flag: bool = False


@dataclass
class MarketResult:
    item_id: str
    action: RecommendationAction
    expected_profit_per_flip: int
    fill_velocity_score: float
    liquidity_score: float
    risk_score: float
    floor_proximity_score: float
    confidence: float
    rationale: str
    rationale_json: Dict[str, float] = field(default_factory=dict)


class MarketEngine:
    """Evaluates marketplace opportunities for flips and low-risk floor buys."""

    def __init__(self, thresholds: Dict[str, float]):
        self.thresholds = thresholds

    def evaluate(self, data: MarketInput) -> MarketResult:
        expected_profit = tax_adjusted_profit(data.best_buy_order, data.best_sell_order, data.tax_rate)
        spread = 0 if data.best_buy_order is None or data.best_sell_order is None else max(data.best_sell_order - data.best_buy_order, 0)
        current_entry_price = data.best_buy_order or data.buy_now or data.best_sell_order or data.sell_now
        floor_score = floor_proximity(current_entry_price, data.quicksell_value)

        liquidity_score = clamp(
            data.aggregate_liquidity_score * 0.7 + (min(data.listing_depth or 0, 25) / 25.0) * 30.0,
            0.0,
            100.0,
        )
        fill_velocity_score = clamp(
            liquidity_score * 0.65 + (100.0 - min(spread, 10000) / 100.0) * 0.35,
            0.0,
            100.0,
        )

        reference_markup_pct = 0.0
        if data.stable_reference_price and current_entry_price:
            reference_markup_pct = (current_entry_price - data.stable_reference_price) / data.stable_reference_price

        risk_score = 35.0 + (data.volatility_score * 0.35) - (floor_score * 0.20) - (data.trend_compression_score * 0.08)
        if reference_markup_pct > 0:
            risk_score += min(reference_markup_pct * 100.0, 20.0)
        if data.phase == MarketPhase.EARLY_ACCESS:
            risk_score += 22.0
        elif data.phase == MarketPhase.FULL_LAUNCH_SUPPLY_SHOCK:
            risk_score += 10.0
        elif data.phase == MarketPhase.CONTENT_DROP:
            risk_score += 8.0

        if data.recent_price_change_pct < -0.10 and data.phase != MarketPhase.EARLY_ACCESS:
            risk_score -= 4.0
        if data.content_drop_flag:
            risk_score += 5.0
        if data.is_collection_critical:
            risk_score -= 5.0
        risk_score = clamp(risk_score, 0.0, 100.0)

        low_risk_profit = expected_profit >= self.thresholds.get("low_risk_profit_min", 250.0)
        strong_fill = fill_velocity_score >= self.thresholds.get("strong_fill_velocity", 70.0)
        compression_ready = data.trend_compression_score >= self.thresholds.get("trend_compression_score_min", 58.0)
        early_watch_floor = floor_score >= self.thresholds.get("early_access_watch_floor_score_min", 82.0)
        early_buy_floor = floor_score >= self.thresholds.get("early_access_buy_floor_score_min", 96.0)
        full_launch_floor = floor_score >= self.thresholds.get("full_launch_floor_score_min", 72.0)
        inflated_vs_reference = reference_markup_pct >= self.thresholds.get("early_access_reference_markup_cap_pct", 0.18)

        action = RecommendationAction.IGNORE
        rationale = "Spread, liquidity, and phase context do not justify action right now."

        if data.phase == MarketPhase.EARLY_ACCESS:
            if low_risk_profit and strong_fill:
                action = RecommendationAction.FLIP
                rationale = (
                    "Early-access pricing is distorted, but the after-tax spread and fill speed support a short-duration flip rather than a fair-value buy."
                )
            elif early_buy_floor and compression_ready and liquidity_score >= 45.0:
                action = RecommendationAction.BUY
                rationale = (
                    "Card is essentially at the quicksell floor with trend compression, creating a low-risk early-access entry despite inflated market conditions."
                )
            elif early_watch_floor:
                action = RecommendationAction.WATCH
                rationale = (
                    "Early-access prices from March 13-16 are distorted; keep this on a floor watchlist and avoid using inflated prints as fair value."
                )
            else:
                action = RecommendationAction.IGNORE
                rationale = "Early-access distortion remains too high; preserve stubs unless the card is near floor or supports a fast flip."
        elif data.phase == MarketPhase.FULL_LAUNCH_SUPPLY_SHOCK:
            if full_launch_floor and compression_ready and liquidity_score >= 45.0:
                action = RecommendationAction.BUY
                rationale = (
                    "Full-launch supply shock is compressing downward momentum near the quicksell floor, so this looks like a controlled floor buy instead of a falling knife."
                )
            elif low_risk_profit and strong_fill:
                action = RecommendationAction.FLIP
                rationale = "Post-launch liquidity plus an after-tax spread support a launch-week flip."
            elif full_launch_floor:
                action = RecommendationAction.WATCH
                rationale = "Price is entering the floor zone, but trend compression is not strong enough yet to confirm the crash is slowing."
        elif full_launch_floor and compression_ready and liquidity_score >= 45.0:
            action = RecommendationAction.BUY
            rationale = "Card is close to quicksell with a compressed trend, creating an attractive low-risk buy setup."
        elif low_risk_profit and strong_fill:
            action = RecommendationAction.FLIP
            rationale = "After-tax spread and fill velocity support a high-probability flip."
        elif data.is_live_series and data.is_collection_critical and inflated_vs_reference:
            action = RecommendationAction.HOLD
            rationale = "Collection-critical Live Series card is expensive versus baseline, but scarcity argues for holding instead of chasing more inventory."
        elif expected_profit > 0 and liquidity_score >= 50.0:
            action = RecommendationAction.WATCH
            rationale = "Spread is positive, but waiting for better floor support or stronger trend compression is safer."

        if data.phase == MarketPhase.EARLY_ACCESS and inflated_vs_reference and action in {RecommendationAction.BUY, RecommendationAction.WATCH}:
            rationale += " Stable reference checks still show early-access markup, so position size should stay conservative."

        confidence = clamp(
            28.0
            + expected_profit / 150.0
            + fill_velocity_score * 0.24
            + floor_score * 0.16
            + data.trend_compression_score * 0.12
            - risk_score * 0.22,
            0.0,
            100.0,
        )
        return MarketResult(
            item_id=data.item_id,
            action=action,
            expected_profit_per_flip=expected_profit,
            fill_velocity_score=round(fill_velocity_score, 2),
            liquidity_score=round(liquidity_score, 2),
            risk_score=round(risk_score, 2),
            floor_proximity_score=round(floor_score, 2),
            confidence=round(confidence, 2),
            rationale=rationale,
            rationale_json={
                "expected_profit_per_flip": expected_profit,
                "fill_velocity_score": round(fill_velocity_score, 2),
                "liquidity_score": round(liquidity_score, 2),
                "risk_score": round(risk_score, 2),
                "floor_proximity_score": round(floor_score, 2),
                "trend_compression_score": round(data.trend_compression_score, 2),
                "stable_reference_price": round(data.stable_reference_price or 0.0, 2),
                "reference_markup_pct": round(reference_markup_pct * 100.0, 2),
            },
        )
