"""Live Series collection planning strategy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from app.utils.enums import MarketPhase
from app.utils.scoring import clamp


@dataclass
class CollectionInput:
    item_id: str
    card_name: str
    team: str
    division: str
    league: str
    current_price: int
    quicksell_value: int
    overall: int
    is_owned: bool
    locked_for_collection: bool
    quantity: int = 0


@dataclass
class CollectionTarget:
    name: str
    level: str
    priority_score: float
    completion_pct: float
    remaining_cost: int
    owned_gatekeeper_value: int
    reward_value_proxy: int
    rationale: str


@dataclass
class CollectionResult:
    projected_completion_cost: int
    ranked_division_targets: List[CollectionTarget] = field(default_factory=list)
    ranked_team_targets: List[CollectionTarget] = field(default_factory=list)
    recommended_cards_to_lock: List[str] = field(default_factory=list)
    recommended_cards_to_delay: List[str] = field(default_factory=list)


class CollectionEngine:
    """Ranks teams and divisions by efficient Live Series completion value."""

    def __init__(self, thresholds: Dict[str, float]):
        self.thresholds = thresholds

    def evaluate(self, phase: MarketPhase, cards: Sequence[CollectionInput]) -> CollectionResult:
        live_cards = [card for card in cards if card.division and card.league]
        projected_completion_cost = sum(card.current_price for card in live_cards if not card.is_owned)
        team_targets = self._rank_groups(phase, live_cards, level="team")
        division_targets = self._rank_groups(phase, live_cards, level="division")

        lock_cards: List[str] = []
        delay_cards: List[str] = []
        for card in live_cards:
            high_gatekeeper = card.current_price >= self.thresholds.get("high_gatekeeper_price", 90000.0)
            if card.is_owned and high_gatekeeper:
                lock_cards.append(card.card_name)
            elif phase == MarketPhase.EARLY_ACCESS and card.is_owned and not high_gatekeeper:
                delay_cards.append(card.card_name)

        return CollectionResult(
            projected_completion_cost=projected_completion_cost,
            ranked_division_targets=division_targets,
            ranked_team_targets=team_targets,
            recommended_cards_to_lock=sorted(set(lock_cards)),
            recommended_cards_to_delay=sorted(set(delay_cards)),
        )

    def _rank_groups(self, phase: MarketPhase, cards: Sequence[CollectionInput], level: str) -> List[CollectionTarget]:
        groups: Dict[str, List[CollectionInput]] = {}
        for card in cards:
            key = card.team if level == "team" else card.division
            groups.setdefault(key, []).append(card)

        targets: List[CollectionTarget] = []
        for group_name, group_cards in groups.items():
            total = len(group_cards)
            owned = sum(1 for card in group_cards if card.is_owned)
            completion_pct = owned / total if total else 0.0
            remaining_cost = sum(card.current_price for card in group_cards if not card.is_owned)
            owned_gatekeeper_value = sum(
                card.current_price
                for card in group_cards
                if card.is_owned and card.current_price >= self.thresholds.get("high_gatekeeper_price", 90000.0)
            )
            reward_value = int(
                self.thresholds.get(
                    "collection_team_reward_value" if level == "team" else "collection_division_reward_value",
                    15000.0 if level == "team" else 45000.0,
                )
            )
            gatekeeper_score = owned_gatekeeper_value / self.thresholds.get("collection_gatekeeper_value_divisor", 3000.0)
            completion_score = completion_pct * self.thresholds.get("collection_completion_score_weight", 45.0)
            reward_score = reward_value / self.thresholds.get("collection_reward_value_divisor", 2500.0)
            opportunity_cost_penalty = remaining_cost * self.thresholds.get("collection_remaining_cost_penalty_rate", 0.0002)
            early_access_penalty = self.thresholds.get("collection_early_access_penalty", 15.0) if phase == MarketPhase.EARLY_ACCESS else 0.0
            score = gatekeeper_score + completion_score + reward_score - opportunity_cost_penalty - early_access_penalty

            reasons = [
                f"{completion_pct:.0%} complete",
                f"{owned_gatekeeper_value:,} stubs of owned gatekeepers",
                f"{remaining_cost:,} stubs remaining",
            ]

            if owned_gatekeeper_value > 0:
                score += self.thresholds.get("collection_owned_gatekeeper_priority_bonus", 10.0)
                reasons.append("owned gatekeeper boosts collection leverage")
            if completion_pct >= self.thresholds.get("division_completion_boost_pct", 0.70):
                score += self.thresholds.get("collection_close_completion_bonus", 12.0)
                reasons.append("group is close enough to justify finishing")
            if remaining_cost <= self.thresholds.get("reasonable_division_cost", 175000.0):
                score += self.thresholds.get("collection_low_remaining_cost_bonus", 8.0)
                reasons.append("remaining cost is manageable")
            if phase == MarketPhase.EARLY_ACCESS:
                reasons.append("early-access locking penalty applied")

            rationale = f"{group_name}: " + "; ".join(reasons) + "."
            targets.append(
                CollectionTarget(
                    name=group_name,
                    level=level,
                    priority_score=round(clamp(score, 0.0, 100.0), 2),
                    completion_pct=round(completion_pct, 4),
                    remaining_cost=int(remaining_cost),
                    owned_gatekeeper_value=int(owned_gatekeeper_value),
                    reward_value_proxy=reward_value,
                    rationale=rationale,
                )
            )
        return sorted(targets, key=lambda item: item.priority_score, reverse=True)
