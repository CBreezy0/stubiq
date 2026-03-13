"""Recommendation assembly and orchestration service."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import (
    Card,
    MarketPhaseHistory,
    PlayerStatsDaily,
    PlayerStatsRolling,
    PortfolioPosition,
    ProgramReward,
    RosterUpdateCalendar,
    RosterUpdatePrediction,
    StrategyRecommendation,
    User,
)
from app.schemas.cards import CardDetailResponse, CardSummaryResponse
from app.schemas.collections import CollectionPriorityResponse, CollectionTarget
from app.schemas.common import MarketPhaseResponse, RecommendationView
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.grind import GrindRecommendationResponse, ModeValueResponse
from app.schemas.investments import (
    RosterUpdatePlayerAnalysisResponse,
    RosterUpdateRecommendationListResponse,
    RosterUpdateRecommendationResponse,
)
from app.schemas.market import MarketOpportunityListResponse, MarketOpportunityResponse
from app.schemas.portfolio import PortfolioPositionResponse, PortfolioRecommendationResponse, PortfolioResponse
from app.services.config_store import ConfigStore
from app.services.market_data import CardMarketContext, MarketDataService
from app.services.portfolio import PortfolioService
from app.services.user_service import UserService
from app.strategies import (
    CollectionEngine,
    CollectionInput,
    GrindEVEngine,
    GrindModeInput,
    MarketEngine,
    MarketInput,
    MarketPhaseEngine,
    PhaseObservation,
    PortfolioEngine,
    PortfolioInput,
    RosterUpdateEngine,
    RosterUpdateInput,
    StrategyInputs,
    StrategyOrchestrator,
)
from app.utils.enums import MarketPhase, RecommendationAction, RecommendationType, UpdateType
from app.utils.scoring import clamp, pct_change
from app.utils.time import utcnow


logger = logging.getLogger(__name__)


class RecommendationService:
    """Builds market, roster, portfolio, collection, and grind recommendations."""

    def __init__(
        self,
        settings: Settings,
        config_store: ConfigStore,
        market_data_service: MarketDataService,
        portfolio_service: PortfolioService,
        user_service: UserService,
    ):
        self.settings = settings
        self.config_store = config_store
        self.market_data_service = market_data_service
        self.portfolio_service = portfolio_service
        self.user_service = user_service
        self.phase_engine = MarketPhaseEngine(settings)
        self.roster_update_engine = RosterUpdateEngine(settings.quicksell_tiers)

    def _engine_thresholds(self, session: Session, user: Optional[User] = None) -> Dict[str, float]:
        if user is None:
            return self.config_store.get_engine_thresholds(session, self.settings.engine_thresholds)
        return self.user_service.get_engine_thresholds(session, user)

    def _strategy_weights(self, session: Session) -> Dict[str, float]:
        return self.config_store.get_strategy_weights(session, self.settings.strategy_weights)

    def _market_engine(self, session: Session, user: Optional[User] = None) -> MarketEngine:
        return MarketEngine(self._engine_thresholds(session, user))

    def _collection_engine(self, session: Session, user: Optional[User] = None) -> CollectionEngine:
        return CollectionEngine(self._engine_thresholds(session, user))

    def _portfolio_engine(self, session: Session, user: Optional[User] = None) -> PortfolioEngine:
        return PortfolioEngine(self._engine_thresholds(session, user))

    def _grind_engine(self, session: Session, user: Optional[User] = None) -> GrindEVEngine:
        return GrindEVEngine(self.settings.feature_flags, self._engine_thresholds(session, user))

    def _orchestrator(self, session: Session) -> StrategyOrchestrator:
        return StrategyOrchestrator(self._strategy_weights(session))

    def _launch_window_active(self, session: Session, as_of=None, user: Optional[User] = None) -> bool:
        as_of = as_of or utcnow()
        if not self.settings.feature_flags.launch_phase_logic_enabled:
            return False
        launch_window_hours = float(self._engine_thresholds(session, user).get("launch_window_hours", 48.0))
        launch_start = as_of.replace(
            year=self.settings.early_access_start_date.year,
            month=self.settings.early_access_start_date.month,
            day=self.settings.early_access_start_date.day,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        return 0.0 <= (as_of - launch_start).total_seconds() / 3600.0 <= launch_window_hours

    def _trend_compression_score(self, aggregate) -> float:
        if aggregate is None:
            return 45.0
        avg_15m = aggregate.avg_price_15m
        avg_1h = aggregate.avg_price_1h
        avg_6h = aggregate.avg_price_6h
        avg_24h = aggregate.avg_price_24h
        if not avg_15m or not avg_1h or not avg_6h:
            return 45.0

        short_drop = max(0.0, (avg_1h - avg_15m) / avg_1h) if avg_1h else 0.0
        medium_drop = max(0.0, (avg_6h - avg_1h) / avg_6h) if avg_6h else 0.0
        long_drop = max(0.0, (avg_24h - avg_6h) / avg_24h) if avg_24h else 0.0
        score = 50.0 + (medium_drop - short_drop) * 240.0 + (long_drop - short_drop) * 120.0
        if avg_15m >= avg_1h:
            score += 10.0
        return round(clamp(score, 0.0, 100.0), 2)

    def _stable_reference_price(self, phase: MarketPhase, aggregate) -> Optional[float]:
        if aggregate is None or phase == MarketPhase.EARLY_ACCESS:
            return None
        return aggregate.avg_price_24h or aggregate.avg_price_6h or aggregate.avg_price_1h


    def get_phase(self, session: Session, user: Optional[User] = None) -> MarketPhaseResponse:
        override = self.config_store.get_market_phase_override(session) or self.settings.market_phase_override
        metrics = self.market_data_service.build_market_observation(session)
        now = utcnow()
        next_update_at = session.scalar(
            select(RosterUpdateCalendar.update_date)
            .where(RosterUpdateCalendar.update_type == UpdateType.ATTRIBUTE_UPDATE)
            .where(RosterUpdateCalendar.update_date >= now)
            .order_by(RosterUpdateCalendar.update_date.asc())
            .limit(1)
        )
        last_update_at = session.scalar(
            select(RosterUpdateCalendar.update_date)
            .where(RosterUpdateCalendar.update_type == UpdateType.ATTRIBUTE_UPDATE)
            .where(RosterUpdateCalendar.update_date < now)
            .order_by(RosterUpdateCalendar.update_date.desc())
            .limit(1)
        )
        content_drop_flag = session.scalar(
            select(RosterUpdateCalendar.id)
            .where(RosterUpdateCalendar.update_type == UpdateType.CONTENT_DROP)
            .where(RosterUpdateCalendar.update_date >= now - timedelta(hours=24))
            .limit(1)
        ) is not None
        self.phase_engine.thresholds = self._engine_thresholds(session, user)
        decision = self.phase_engine.detect_phase(
            PhaseObservation(
                as_of=now,
                recent_market_drop_pct=metrics.get("recent_market_drop_pct", 0.0),
                recent_supply_growth_pct=metrics.get("recent_supply_growth_pct", 0.0),
                content_drop_flag=content_drop_flag,
                current_override=override,
                next_update_at=next_update_at,
                last_update_at=last_update_at,
            )
        )
        return MarketPhaseResponse(
            phase=decision.phase,
            confidence=decision.confidence,
            rationale=decision.rationale,
            override_active=decision.override_active,
            detected_at=decision.detected_at,
        )

    def get_phase_history(self, session: Session) -> List[dict]:
        rows = session.scalars(select(MarketPhaseHistory).order_by(MarketPhaseHistory.phase_start.desc()).limit(20)).all()
        return [
            {
                "phase": row.phase,
                "phase_start": row.phase_start,
                "phase_end": row.phase_end,
                "notes": row.notes,
            }
            for row in rows
        ]

    def get_flips(self, session: Session, limit: int = 25, user: Optional[User] = None) -> MarketOpportunityListResponse:
        phase = self.get_phase(session, user).phase
        opportunities = [
            self._build_market_opportunity(session, context, phase, user)
            for context in self.market_data_service.list_market_contexts(session)
            if context.snapshot is not None
        ]
        filtered = [item for item in opportunities if item.action == RecommendationAction.FLIP]
        filtered.sort(key=lambda item: (item.expected_profit_per_flip or 0, item.confidence), reverse=True)
        return MarketOpportunityListResponse(phase=phase, count=len(filtered[:limit]), items=filtered[:limit])

    def get_floor_buys(self, session: Session, limit: int = 25, user: Optional[User] = None) -> MarketOpportunityListResponse:
        phase = self.get_phase(session, user).phase
        opportunities = [
            self._build_market_opportunity(session, context, phase, user)
            for context in self.market_data_service.list_market_contexts(session)
            if context.snapshot is not None
        ]
        floor_score_min = self._engine_thresholds(session, user).get("floor_endpoint_score_min", 70.0)
        filtered = [
            item
            for item in opportunities
            if item.floor_proximity_score >= floor_score_min and item.action in {RecommendationAction.BUY, RecommendationAction.WATCH}
        ]
        filtered.sort(key=lambda item: (item.floor_proximity_score, item.confidence), reverse=True)
        return MarketOpportunityListResponse(phase=phase, count=len(filtered[:limit]), items=filtered[:limit])

    def get_roster_update_targets(self, session: Session, limit: int = 50, user: Optional[User] = None) -> RosterUpdateRecommendationListResponse:
        rows = self._build_roster_update_targets(session)
        rows.sort(
            key=lambda item: (
                item.action == RecommendationAction.BUY,
                item.expected_profit,
                item.upgrade_probability - item.downside_risk,
                item.confidence,
            ),
            reverse=True,
        )
        return RosterUpdateRecommendationListResponse(count=len(rows[:limit]), items=rows[:limit])

    def get_roster_update_player_analysis(self, session: Session, name: str) -> Optional[RosterUpdatePlayerAnalysisResponse]:
        lowered = name.strip().lower()
        if not lowered:
            return None
        card = session.scalar(
            select(Card)
            .where(Card.is_live_series.is_(True))
            .where(or_(func.lower(Card.name) == lowered, func.lower(Card.name).like(f"%{lowered}%")))
            .order_by(func.length(Card.name).asc())
            .limit(1)
        )
        if card is None:
            return None
        analysis = self._build_roster_update_analysis(session, card, context=self._roster_context(session))
        if analysis is None:
            return None
        return RosterUpdatePlayerAnalysisResponse(**analysis.model_dump(), matching_name=name)

    def get_collection_priorities(self, session: Session, user: Optional[User] = None) -> CollectionPriorityResponse:
        phase = self.get_phase(session, user).phase
        positions = {position.item_id: position for position in self.portfolio_service.list_positions(session, user)}
        snapshots = self.market_data_service.get_latest_snapshots(session)
        live_cards = session.scalars(select(Card).where(Card.is_live_series.is_(True))).all()
        result = self._collection_engine(session, user).evaluate(
            phase,
            [
                CollectionInput(
                    item_id=card.item_id,
                    card_name=card.name,
                    team=card.team or "Unknown",
                    division=card.division or "Unknown",
                    league=card.league or "Unknown",
                    current_price=(snapshots.get(card.item_id).best_sell_order if snapshots.get(card.item_id) else card.quicksell_value or 0),
                    quicksell_value=card.quicksell_value or 0,
                    overall=card.overall or 0,
                    is_owned=card.item_id in positions and positions[card.item_id].quantity > 0,
                    locked_for_collection=positions.get(card.item_id).locked_for_collection if card.item_id in positions else False,
                    quantity=positions.get(card.item_id).quantity if card.item_id in positions else 0,
                )
                for card in live_cards
                if card.division and card.league
            ],
        )
        return CollectionPriorityResponse(
            market_phase=phase,
            projected_completion_cost=result.projected_completion_cost,
            ranked_division_targets=[CollectionTarget(**target.__dict__) for target in result.ranked_division_targets],
            ranked_team_targets=[CollectionTarget(**target.__dict__) for target in result.ranked_team_targets],
            recommended_cards_to_lock=result.recommended_cards_to_lock,
            recommended_cards_to_delay=result.recommended_cards_to_delay,
        )

    def get_portfolio(self, session: Session, user: Optional[User] = None) -> PortfolioResponse:
        positions = self.portfolio_service.list_positions(session, user)
        snapshots = self.market_data_service.get_latest_snapshots(session)
        cards = {card.item_id: card for card in session.scalars(select(Card)).all()}
        items: List[PortfolioPositionResponse] = []
        total_market_value = 0
        total_cost_basis = 0
        total_unrealized_profit = 0
        for position in positions:
            card = cards.get(position.item_id)
            snapshot = snapshots.get(position.item_id)
            item = self._build_portfolio_position(position, card, snapshot)
            items.append(item)
            total_market_value += (item.current_market_value or 0) * item.quantity
            total_cost_basis += item.total_cost_basis
            total_unrealized_profit += item.unrealized_profit or 0
        return PortfolioResponse(
            total_positions=len(items),
            total_market_value=total_market_value,
            total_cost_basis=total_cost_basis,
            total_unrealized_profit=total_unrealized_profit,
            items=items,
        )

    def get_portfolio_recommendations(self, session: Session, user: Optional[User] = None) -> List[PortfolioRecommendationResponse]:
        phase = self.get_phase(session, user).phase
        positions = self.portfolio_service.list_positions(session, user)
        cards = {card.item_id: card for card in session.scalars(select(Card)).all()}
        results: List[PortfolioRecommendationResponse] = []
        for position in positions:
            card = cards.get(position.item_id)
            if not card:
                continue
            scarcity_score = 80.0 if (card.series or "").lower() in {"event", "battle royale", "ranked"} else (55.0 if not card.is_live_series else 40.0)
            lineup_utility_score = 90.0 if (card.overall or 0) >= 95 else (70.0 if (card.overall or 0) >= 88 else 45.0)
            result = self._portfolio_engine(session, user).evaluate(
                PortfolioInput(
                    item_id=card.item_id,
                    card_name=card.name,
                    is_live_series=card.is_live_series,
                    overall=card.overall or 0,
                    quantity=position.quantity,
                    avg_acquisition_cost=position.avg_acquisition_cost,
                    current_market_value=position.current_market_value or card.quicksell_value or 0,
                    quicksell_value=position.quicksell_value or card.quicksell_value or 0,
                    locked_for_collection=position.locked_for_collection,
                    duplicate_count=position.duplicate_count,
                    scarcity_score=scarcity_score,
                    lineup_utility_score=lineup_utility_score,
                    collection_critical=card.is_live_series and (card.overall or 0) >= 88,
                    phase=phase,
                )
            )
            results.append(
                PortfolioRecommendationResponse(
                    item_id=position.item_id,
                    action=result.action,
                    confidence=result.confidence,
                    sell_now_score=result.sell_now_score,
                    hold_score=result.hold_score,
                    lock_score=result.lock_score,
                    flip_out_score=result.flip_out_score,
                    portfolio_risk_score=result.portfolio_risk_score,
                    rationale=result.rationale,
                )
            )
        results.sort(key=lambda item: (item.action == RecommendationAction.SELL, item.confidence), reverse=True)
        return results

    def get_grind_recommendation(self, session: Session, user: Optional[User] = None) -> GrindRecommendationResponse:
        rewards = session.scalars(select(ProgramReward)).all()
        mode_inputs: List[GrindModeInput] = []
        for reward in rewards:
            estimated_hours = float((reward.source_json or {}).get("estimated_hours", 1.5) or 1.5)
            reward_value = float(reward.reward_stub_value_estimate or 0)
            mode_inputs.append(
                GrindModeInput(
                    mode_name=reward.mode_name,
                    base_stub_value_per_hour=(reward_value * 0.5) / estimated_hours,
                    pack_value_per_hour=(reward_value * 0.35) / estimated_hours,
                    pxp_value_per_hour=(reward_value * 0.15) / estimated_hours,
                    collection_progress_bonus=1200.0 if "Affinity" in reward.mode_name else 0.0,
                    expires_soon=bool(reward.expires_at and reward.expires_at <= utcnow() + timedelta(days=7)),
                )
            )
        flips = self.get_flips(session, limit=10, user=user).items
        market_stub_per_hour = 0.0
        if flips:
            market_stub_per_hour = sum((item.expected_profit_per_flip or 0) * (item.fill_velocity_score / 100.0) * 6.0 for item in flips) / len(flips)
        result = self._grind_engine(session, user).evaluate(
            self.get_phase(session, user).phase,
            market_stub_per_hour,
            mode_inputs,
            launch_window_active=self._launch_window_active(session, user=user),
        )
        return GrindRecommendationResponse(
            action=result.action,
            best_mode_to_play_now=result.best_mode_to_play_now,
            expected_market_stubs_per_hour=result.expected_market_stubs_per_hour,
            expected_value_per_hour_by_mode=[ModeValueResponse(mode_name=item.mode_name, expected_value_per_hour=item.expected_value_per_hour, rationale=item.rationale) for item in result.expected_value_per_hour_by_mode],
            pack_value_estimate=result.pack_value_estimate,
            rationale=result.rationale,
        )

    def get_dashboard_summary(self, session: Session, user: Optional[User] = None) -> DashboardSummaryResponse:
        phase = self.get_phase(session, user)
        collection = self.get_collection_priorities(session, user)
        portfolio = self.get_portfolio(session, user)
        portfolio_recommendations = self.get_portfolio_recommendations(session, user)
        flips = self.get_flips(session, limit=10, user=user).items
        floors = self.get_floor_buys(session, limit=10, user=user).items
        roster = self.get_roster_update_targets(session, limit=10, user=user).items
        grind = self.get_grind_recommendation(session, user)
        alerts = []
        if phase.phase == MarketPhase.EARLY_ACCESS:
            alerts.append("Early access prices are distorted from March 13-16; treat these as liquidity signals, not fair value baselines.")
        if phase.phase == MarketPhase.FULL_LAUNCH_SUPPLY_SHOCK:
            alerts.append("Full launch supply shock is active from March 17 onward; avoid buying falling knives without floor support.")
        if phase.phase == MarketPhase.PRE_ATTRIBUTE_UPDATE:
            alerts.append("Attribute update window is active; review 79->80 and 84->85 candidates before the deadline.")
        return DashboardSummaryResponse(
            market_phase=phase,
            launch_week_alerts=alerts,
            top_flips=flips,
            top_floor_buys=floors,
            top_roster_update_targets=roster,
            collection_priorities=collection,
            portfolio=portfolio.items,
            top_sells=[item for item in portfolio_recommendations if item.action == RecommendationAction.SELL][:10],
            grind_recommendation=grind,
        )

    def get_card_detail(self, session: Session, item_id: str, user: Optional[User] = None) -> Optional[CardDetailResponse]:
        try:
            context = self.market_data_service.get_card_context(session, item_id)
            if context is None:
                return None
            recommendations = [
                RecommendationView(
                    recommendation_type=row.recommendation_type,
                    action=row.action,
                    confidence=row.confidence,
                    expected_profit=row.expected_profit,
                    expected_value=row.expected_value,
                    market_phase=MarketPhase((row.rationale_json or {}).get("market_phase", self.get_phase(session, user).phase.value)),
                    rationale=(row.rationale_json or {}).get("rationale", "Persisted strategy recommendation"),
                    rationale_json=row.rationale_json or {},
                )
                for row in self.market_data_service.get_recent_recommendations(session, item_id)
            ]
            summary = self._build_card_summary(context.card, context.snapshot)
            aggregate = context.aggregate
            return CardDetailResponse(
                **summary.model_dump(),
                metadata_json=context.card.metadata_json or {},
                aggregate_phase=aggregate.phase.value if aggregate else None,
                avg_price_15m=aggregate.avg_price_15m if aggregate else None,
                avg_price_1h=aggregate.avg_price_1h if aggregate else None,
                avg_price_6h=aggregate.avg_price_6h if aggregate else None,
                avg_price_24h=aggregate.avg_price_24h if aggregate else None,
                volatility_score=aggregate.volatility_score if aggregate else None,
                liquidity_score=aggregate.liquidity_score if aggregate else None,
                recommendations=recommendations,
            )
        except SQLAlchemyError:
            logger.exception("Database query failed while building card detail response for item_id=%s", item_id)
            raise

    def generate_and_store_recommendations(self, session: Session) -> Dict[str, int]:
        phase = self.get_phase(session)
        self._ensure_phase_history(session, phase.phase)
        count = 0
        for row in self.get_flips(session, limit=20).items:
            session.add(
                StrategyRecommendation(
                    item_id=row.item_id,
                    recommendation_type=RecommendationType.MARKET,
                    action=row.action,
                    confidence=row.confidence,
                    expected_profit=row.expected_profit_per_flip,
                    expected_value=row.fill_velocity_score,
                    rationale_json={"market_phase": phase.phase.value, "rationale": row.rationale},
                )
            )
            count += 1
        for row in self.get_roster_update_targets(session, limit=20).items:
            session.add(
                StrategyRecommendation(
                    item_id=row.item_id,
                    recommendation_type=RecommendationType.ROSTER_UPDATE,
                    action=row.action,
                    confidence=row.confidence,
                    expected_profit=None,
                    expected_value=row.expected_market_value,
                    rationale_json={"market_phase": phase.phase.value, "rationale": row.rationale},
                )
            )
            count += 1
        for row in self.get_portfolio_recommendations(session)[:20]:
            session.add(
                StrategyRecommendation(
                    item_id=row.item_id,
                    recommendation_type=RecommendationType.PORTFOLIO,
                    action=row.action,
                    confidence=row.confidence,
                    expected_profit=None,
                    expected_value=row.sell_now_score,
                    rationale_json={"market_phase": phase.phase.value, "rationale": row.rationale},
                )
            )
            count += 1
        return {"stored": count}

    def _ensure_phase_history(self, session: Session, phase: MarketPhase) -> None:
        latest = session.scalar(select(MarketPhaseHistory).order_by(MarketPhaseHistory.phase_start.desc()).limit(1))
        if latest and latest.phase == phase and latest.phase_end is None:
            return
        now = utcnow()
        if latest and latest.phase_end is None:
            latest.phase_end = now
            session.add(latest)
        session.add(MarketPhaseHistory(phase=phase, phase_start=now, notes="Auto-detected phase"))

    def _build_market_opportunity(self, session: Session, context: CardMarketContext, phase: MarketPhase, user: Optional[User] = None) -> MarketOpportunityResponse:
        snapshot = context.snapshot
        aggregate = context.aggregate
        card = context.card
        result = self._market_engine(session, user).evaluate(
            MarketInput(
                item_id=card.item_id,
                name=card.name,
                best_buy_order=snapshot.best_buy_order if snapshot else None,
                best_sell_order=snapshot.best_sell_order if snapshot else None,
                buy_now=snapshot.buy_now if snapshot else None,
                sell_now=snapshot.sell_now if snapshot else None,
                quicksell_value=card.quicksell_value,
                rarity=card.rarity,
                series=card.series,
                is_live_series=card.is_live_series,
                is_collection_critical=card.is_live_series and (card.overall or 0) >= 88,
                phase=phase,
                recent_price_change_pct=pct_change(aggregate.avg_price_1h if aggregate else None, aggregate.avg_price_24h if aggregate else None),
                volatility_score=aggregate.volatility_score if aggregate and aggregate.volatility_score is not None else 50.0,
                trend_compression_score=self._trend_compression_score(aggregate),
                stable_reference_price=self._stable_reference_price(phase, aggregate),
                listing_depth=(card.metadata_json or {}).get("listing_depth"),
                aggregate_liquidity_score=aggregate.liquidity_score if aggregate and aggregate.liquidity_score is not None else 50.0,
                tax_rate=self.settings.market_tax_rate,
            )
        )
        return MarketOpportunityResponse(
            item_id=card.item_id,
            card=self._build_card_summary(card, snapshot),
            action=result.action,
            expected_profit_per_flip=result.expected_profit_per_flip,
            fill_velocity_score=result.fill_velocity_score,
            liquidity_score=result.liquidity_score,
            risk_score=result.risk_score,
            floor_proximity_score=result.floor_proximity_score,
            market_phase=phase,
            confidence=result.confidence,
            rationale=result.rationale,
        )

    def generate_and_store_roster_update_predictions(self, session: Session) -> Dict[str, int]:
        generated_at = utcnow()
        rows = self._build_roster_update_targets(session)
        stored = 0
        for row in rows:
            session.add(
                RosterUpdatePrediction(
                    item_id=row.item_id,
                    player_name=row.player_name,
                    mlb_player_id=row.mlb_player_id,
                    current_ovr=row.current_ovr,
                    current_price=row.current_price,
                    expected_quicksell_value=row.expected_quicksell_value,
                    expected_market_price=row.expected_market_value,
                    upgrade_probability=row.upgrade_probability,
                    expected_profit=row.expected_profit,
                    downside_risk=row.downside_risk,
                    recommendation=row.action,
                    confidence=row.confidence,
                    rationale_json=row.rationale_json,
                    generated_at=generated_at,
                )
            )
            stored += 1
        return {"stored": stored}

    def _build_roster_update_targets(self, session: Session) -> List[RosterUpdateRecommendationResponse]:
        live_cards = session.scalars(select(Card).where(Card.is_live_series.is_(True)).where(Card.mlb_player_id.is_not(None))).all()
        live_cards = [card for card in live_cards if (card.overall or 0) in {79, 84} or (card.overall or 0) >= 88]
        context = self._roster_context(session)
        rows: List[RosterUpdateRecommendationResponse] = []
        for card in live_cards:
            analysis = self._build_roster_update_analysis(session, card, context=context)
            if analysis is None or analysis.action == RecommendationAction.AVOID:
                continue
            rows.append(analysis)
        return rows

    def _build_roster_update_analysis(self, session: Session, card: Card, context: Optional[dict] = None) -> Optional[RosterUpdateRecommendationResponse]:
        if not card.mlb_player_id or not card.is_live_series:
            return None

        context = context or self._roster_context(session)
        snapshots = context["snapshots"]
        aggregates = context["aggregates"]
        daily_by_player = context["daily_by_player"]
        rolling_by_player = context["rolling_by_player"]
        lineup_by_player = context["lineup_by_player"]
        probable_by_player = context["probable_by_player"]
        daily = daily_by_player.get(card.mlb_player_id)
        rolling = rolling_by_player.get(card.mlb_player_id, {})
        snapshot = snapshots.get(card.item_id)
        aggregate = aggregates.get(card.item_id)
        if daily is None and not rolling:
            return None

        next_update_at = context["next_update_at"]
        days_until_update = ((next_update_at - utcnow()).total_seconds() / 86400.0) if next_update_at else None

        market_price = snapshot.best_sell_order if snapshot and snapshot.best_sell_order is not None else card.quicksell_value or 0
        input_row = self._build_roster_input(
            card=card,
            daily=daily,
            rolling=rolling,
            snapshot=snapshot,
            aggregate=aggregate,
            lineup=lineup_by_player.get(card.mlb_player_id),
            probable=probable_by_player.get(card.mlb_player_id),
            days_until_update=days_until_update,
            market_price=market_price,
        )
        result = self.roster_update_engine.evaluate(input_row)
        return RosterUpdateRecommendationResponse(
            item_id=card.item_id,
            player_name=result.player_name,
            mlb_player_id=int(card.mlb_player_id),
            card=self._build_card_summary(card, snapshot),
            action=result.action,
            current_ovr=result.current_overall,
            current_price=market_price,
            upgrade_probability=result.upgrade_probability,
            downgrade_probability=result.downgrade_probability,
            expected_quicksell_value=result.expected_quicksell_value,
            expected_market_value=result.expected_market_value,
            expected_profit=result.expected_profit,
            downside_risk=result.downside_risk,
            confidence=result.confidence,
            rationale=result.rationale,
            rationale_json=result.rationale_json,
            generated_at=utcnow(),
        )

    def _build_roster_input(
        self,
        *,
        card: Card,
        daily,
        rolling,
        snapshot,
        aggregate,
        lineup,
        probable,
        days_until_update: Optional[float],
        market_price: int,
    ) -> RosterUpdateInput:
        rolling7 = rolling.get(7)
        rolling15 = rolling.get(15)
        rolling30 = rolling.get(30)
        price_momentum = 0.0
        if aggregate and aggregate.avg_price_24h:
            anchor = aggregate.avg_price_24h or aggregate.avg_price_6h or market_price
            price_momentum = ((market_price - anchor) / anchor) if anchor else 0.0

        stat_momentum = None
        if card.is_pitcher:
            baseline = rolling15.era if rolling15 and rolling15.era is not None else daily.era if daily else None
            recent = rolling7.era if rolling7 and rolling7.era is not None else baseline
            if baseline is not None and recent is not None:
                stat_momentum = baseline - recent
        else:
            baseline = rolling30.ops if rolling30 and rolling30.ops is not None else daily.ops if daily else None
            recent = rolling7.ops if rolling7 and rolling7.ops is not None else baseline
            if baseline is not None and recent is not None:
                stat_momentum = recent - baseline

        role_security = 55.0
        if probable or lineup:
            role_security = 80.0
        if lineup and getattr(lineup, 'confirmed', False):
            role_security += 10.0
        if probable and getattr(probable, 'confirmed', False):
            role_security += 10.0

        return RosterUpdateInput(
            item_id=card.item_id,
            card_name=card.name,
            player_name=card.name,
            mlb_player_id=card.mlb_player_id,
            current_overall=card.overall or 0,
            market_price=market_price,
            quicksell_value=card.quicksell_value or 0,
            series=card.series,
            rarity=card.rarity,
            avg=daily.avg if daily else None,
            ops=daily.ops if daily else None,
            iso=daily.iso if daily else None,
            hr=daily.hr if daily else None,
            bb_rate=daily.bb_rate if daily else None,
            k_rate=daily.k_rate if daily else None,
            era=daily.era if daily else None,
            whip=daily.whip if daily else None,
            k_per_9=daily.k_per_9 if daily else None,
            bb_per_9=daily.bb_per_9 if daily else None,
            innings=daily.innings if daily else None,
            rolling_7_ops=rolling7.ops if rolling7 else None,
            rolling_15_ops=rolling15.ops if rolling15 else None,
            rolling_30_ops=rolling30.ops if rolling30 else None,
            season_ops=daily.ops if daily else None,
            rolling_7_era=rolling7.era if rolling7 else None,
            rolling_15_era=rolling15.era if rolling15 else None,
            season_era=daily.era if daily else None,
            rolling_7_whip=rolling7.whip if rolling7 else None,
            rolling_15_whip=rolling15.whip if rolling15 else None,
            rolling_7_k_rate=rolling7.k_rate if rolling7 else daily.k_rate if daily else None,
            rolling_15_k_rate=rolling15.k_rate if rolling15 else daily.k_rate if daily else None,
            rolling_7_bb_rate=rolling7.bb_rate if rolling7 else daily.bb_rate if daily else None,
            rolling_15_bb_rate=rolling15.bb_rate if rolling15 else daily.bb_rate if daily else None,
            lineup_spot=lineup.lineup_spot if lineup else None,
            role_security=role_security,
            probable_starter=bool(card.is_pitcher and probable),
            saves=daily.saves or 0 if daily else 0,
            holds=daily.holds or 0 if daily else 0,
            injury_risk=float((card.metadata_json or {}).get("injury_risk", 0.0) or 0.0),
            days_until_update=days_until_update,
            is_pitcher=bool(card.is_pitcher),
            price_momentum=price_momentum,
            stat_momentum=stat_momentum,
            social_hype_factor=float((card.metadata_json or {}).get("social_hype_factor", 0.0) or 0.0),
        )

    def _roster_context(self, session: Session) -> Dict[str, object]:
        next_update_at = session.scalar(
            select(RosterUpdateCalendar.update_date)
            .where(RosterUpdateCalendar.update_type == UpdateType.ATTRIBUTE_UPDATE)
            .where(RosterUpdateCalendar.update_date >= utcnow())
            .order_by(RosterUpdateCalendar.update_date.asc())
            .limit(1)
        )
        next_update_at = self._coerce_utc(next_update_at)
        return {
            "snapshots": self.market_data_service.get_latest_snapshots(session),
            "aggregates": self.market_data_service.get_latest_aggregates(session),
            "daily_by_player": self._latest_daily_by_player(session),
            "rolling_by_player": self._latest_rolling_by_player(session),
            "lineup_by_player": self._latest_lineup_by_player(session),
            "probable_by_player": self._latest_probable_by_player(session),
            "next_update_at": next_update_at,
        }

    def _build_portfolio_position(self, position: PortfolioPosition, card: Optional[Card], snapshot) -> PortfolioPositionResponse:
        current_market_value = position.current_market_value or (snapshot.best_sell_order if snapshot else None) or position.quicksell_value or 0
        card_summary = self._build_card_summary(card or Card(item_id=position.item_id, name=position.card_name, is_live_series=False, metadata_json={}), snapshot)
        total_cost_basis = position.quantity * position.avg_acquisition_cost
        unrealized_profit = (current_market_value - position.avg_acquisition_cost) * position.quantity if current_market_value is not None else None
        quicksell_floor_total = (position.quicksell_value or 0) * position.quantity if position.quicksell_value is not None else None
        return PortfolioPositionResponse(
            item_id=position.item_id,
            card=card_summary,
            quantity=position.quantity,
            avg_acquisition_cost=position.avg_acquisition_cost,
            current_market_value=current_market_value,
            quicksell_value=position.quicksell_value,
            locked_for_collection=position.locked_for_collection,
            duplicate_count=position.duplicate_count,
            source=position.source,
            created_at=position.created_at,
            updated_at=position.updated_at,
            total_cost_basis=total_cost_basis,
            unrealized_profit=unrealized_profit,
            quicksell_floor_total=quicksell_floor_total,
        )

    def _build_card_summary(self, card: Card, snapshot) -> CardSummaryResponse:
        return CardSummaryResponse(
            item_id=card.item_id,
            name=card.name,
            series=card.series,
            team=card.team,
            division=card.division,
            league=card.league,
            overall=card.overall,
            rarity=card.rarity,
            display_position=card.display_position,
            is_live_series=card.is_live_series,
            quicksell_value=card.quicksell_value,
            latest_buy_now=snapshot.buy_now if snapshot else None,
            latest_sell_now=snapshot.sell_now if snapshot else None,
            latest_best_buy_order=snapshot.best_buy_order if snapshot else None,
            latest_best_sell_order=snapshot.best_sell_order if snapshot else None,
            latest_tax_adjusted_spread=snapshot.tax_adjusted_spread if snapshot else None,
            observed_at=snapshot.observed_at if snapshot else None,
        )

    def _coerce_utc(self, value):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=utcnow().tzinfo)
        return value.astimezone(utcnow().tzinfo)

    def _latest_daily_by_player(self, session: Session) -> Dict[int, PlayerStatsDaily]:
        rows = session.scalars(select(PlayerStatsDaily).order_by(PlayerStatsDaily.stat_date.desc())).all()
        lookup: Dict[int, PlayerStatsDaily] = {}
        for row in rows:
            lookup.setdefault(row.mlb_player_id, row)
        return lookup

    def _latest_rolling_by_player(self, session: Session) -> Dict[int, Dict[int, PlayerStatsRolling]]:
        rows = session.scalars(select(PlayerStatsRolling).order_by(PlayerStatsRolling.as_of_date.desc())).all()
        lookup: Dict[int, Dict[int, PlayerStatsRolling]] = {}
        for row in rows:
            lookup.setdefault(row.mlb_player_id, {})
            lookup[row.mlb_player_id].setdefault(row.window_days, row)
        return lookup

    def _latest_lineup_by_player(self, session: Session):
        rows = session.scalars(select(PlayerStatsDaily).limit(0)).all()
        _ = rows
        lookup = {}
        from app.models import LineupStatus

        for row in session.scalars(select(LineupStatus).order_by(LineupStatus.game_date.desc())).all():
            lookup.setdefault(row.mlb_player_id, row)
        return lookup

    def _latest_probable_by_player(self, session: Session):
        lookup = {}
        from app.models import ProbableStarter

        for row in session.scalars(select(ProbableStarter).order_by(ProbableStarter.game_date.desc())).all():
            lookup.setdefault(row.mlb_player_id, row)
        return lookup
