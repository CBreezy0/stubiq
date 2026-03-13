"""Background worker for precomputing market analytics caches."""

from __future__ import annotations

import logging
import time
from typing import Callable, Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import configure_database, create_session_factory
from app.models import FloorOpportunity, MarketMoverCache, MarketPhaseCache, TopFlip
from app.services import (
    ConfigStore,
    MarketDataService,
    PortfolioService,
    RecommendationService,
    ShowApiAdapter,
    ShowSyncService,
    UserService,
)
from app.utils.time import UTC, utcnow


logger = logging.getLogger(__name__)


class MarketAnalyticsWorker:
    """Owns APScheduler jobs for precomputing market analytics tables."""

    TOP_FLIP_LIMIT = 50
    MARKET_MOVER_LIMIT = 50
    FLOOR_OPPORTUNITY_LIMIT = 50

    def __init__(
        self,
        settings: Settings,
        session_factory,
        show_sync_service: ShowSyncService,
        market_data_service: MarketDataService,
        recommendation_service: RecommendationService,
    ):
        self.settings = settings
        self.session_factory = session_factory
        self.show_sync_service = show_sync_service
        self.market_data_service = market_data_service
        self.recommendation_service = recommendation_service
        self.scheduler = BackgroundScheduler(timezone=UTC)
        self._started = False
        self._job_map: Dict[str, Callable[[], None]] = {
            "listings_sync": self.sync_market_listings,
            "top_flips": self.compute_top_flips,
            "market_movers": self.compute_market_movers,
            "floor_opportunities": self.compute_floor_opportunities,
            "market_phase": self.update_market_phase,
        }

    def start(self) -> None:
        if self._started or not self.settings.scheduler_enabled:
            return
        self.scheduler.add_job(
            self.sync_market_listings,
            IntervalTrigger(minutes=2),
            id="market_worker_listings_sync",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.compute_top_flips,
            IntervalTrigger(minutes=3),
            id="market_worker_top_flips",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.compute_market_movers,
            IntervalTrigger(minutes=3),
            id="market_worker_market_movers",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.compute_floor_opportunities,
            IntervalTrigger(minutes=5),
            id="market_worker_floor_opportunities",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.update_market_phase,
            IntervalTrigger(minutes=10),
            id="market_worker_market_phase",
            replace_existing=True,
        )
        self.scheduler.start()
        self._started = True
        logger.info("Market analytics worker started")

    def shutdown(self) -> None:
        if self._started:
            self.scheduler.shutdown(wait=False)
            self._started = False

    def is_running(self) -> bool:
        return self._started

    def run_job_now(self, job_name: str) -> List[str]:
        accepted: List[str] = []
        if job_name == "all":
            for name, job in self._job_map.items():
                job()
                accepted.append(name)
            return accepted
        job = self._job_map.get(job_name)
        if job is None:
            return accepted
        job()
        accepted.append(job_name)
        return accepted

    def sync_market_listings(self) -> None:
        def _job(session: Session) -> None:
            phase = self.recommendation_service.get_phase(session).phase
            sync_result = self.show_sync_service.sync_listings(session)
            self.market_data_service.compute_market_aggregates(session, phase)
            logger.info(
                "Market listings sync complete: %s pages, %s listings, phase=%s",
                sync_result.get("pages", 0),
                sync_result.get("listings", 0),
                phase.value,
            )

        self._run_with_session("listings_sync", _job)

    def compute_top_flips(self) -> None:
        def _job(session: Session) -> None:
            response = self.show_sync_service.get_top_flip_listings_response(session)
            computed_at = utcnow()
            rows = [
                TopFlip(
                    item_id=item.uuid,
                    name=item.name,
                    buy_price=item.best_buy_price,
                    sell_price=item.best_sell_price,
                    profit=item.profit_after_tax,
                    roi=item.roi,
                    profit_per_min=item.profit_per_minute,
                    updated_at=computed_at,
                )
                for item in response.items
            ]
            self._replace_rows(session, TopFlip, rows)
            logger.info("Top flips cache updated with %s rows", len(rows))

        self._run_with_session("top_flips", _job)

    def compute_market_movers(self) -> None:
        def _job(session: Session) -> None:
            response = self.show_sync_service.get_market_movers_response(session, limit=self.MARKET_MOVER_LIMIT)
            computed_at = utcnow()
            rows = [
                MarketMoverCache(
                    item_id=item.item_id,
                    name=item.name,
                    current_price=item.best_sell_price,
                    previous_price=(item.best_sell_price - item.price_change) if item.best_sell_price is not None else None,
                    change_percent=item.change_percent,
                    volume=None,
                    updated_at=computed_at,
                )
                for item in response.items
            ]
            self._replace_rows(session, MarketMoverCache, rows)
            logger.info("Market movers cache updated with %s rows", len(rows))

        self._run_with_session("market_movers", _job)

    def compute_floor_opportunities(self) -> None:
        def _job(session: Session) -> None:
            response = self.recommendation_service.get_floor_buys(session, limit=self.FLOOR_OPPORTUNITY_LIMIT)
            computed_at = utcnow()
            rows = []
            for item in response.items:
                floor_price = item.card.latest_best_sell_order or item.card.latest_sell_now
                expected_value = float(item.card.quicksell_value) if item.card.quicksell_value is not None else None
                roi = None
                if floor_price not in (None, 0) and expected_value is not None:
                    roi = round(((expected_value - float(floor_price)) / float(floor_price)) * 100.0, 2)
                rows.append(
                    FloorOpportunity(
                        item_id=item.item_id,
                        name=item.card.name,
                        floor_price=floor_price,
                        expected_value=expected_value,
                        roi=roi,
                        updated_at=computed_at,
                    )
                )
            self._replace_rows(session, FloorOpportunity, rows)
            logger.info("Floor opportunities cache updated with %s rows", len(rows))

        self._run_with_session("floor_opportunities", _job)

    def update_market_phase(self) -> None:
        def _job(session: Session) -> None:
            response = self.recommendation_service.get_phase(session)
            row = MarketPhaseCache(
                phase=response.phase,
                confidence=response.confidence,
                updated_at=utcnow(),
            )
            self._replace_rows(session, MarketPhaseCache, [row])
            logger.info("Market phase cache updated: %s (confidence=%s)", response.phase.value, response.confidence)

        self._run_with_session("market_phase", _job)

    def _run_with_session(self, job_name: str, job: Callable[[Session], None]) -> None:
        with self.session_factory() as session:
            try:
                job(session)
                session.commit()
            except Exception:
                session.rollback()
                logger.exception("Market worker job failed: %s", job_name)
                raise

    def _replace_rows(self, session: Session, model, rows: list[object]) -> None:
        session.execute(delete(model))
        if rows:
            session.add_all(rows)


def create_market_worker(settings: Optional[Settings] = None) -> MarketAnalyticsWorker:
    settings = settings or get_settings()
    engine = configure_database(settings.database_url, echo=settings.debug)
    session_factory = create_session_factory(engine)
    show_adapter = ShowApiAdapter(settings.show_api_base_url, timeout_seconds=settings.request_timeout_seconds)
    market_data_service = MarketDataService(settings, show_adapter)
    show_sync_service = ShowSyncService(settings, show_adapter, market_data_service)
    config_store = ConfigStore()
    portfolio_service = PortfolioService(market_data_service)
    user_service = UserService(settings)
    recommendation_service = RecommendationService(settings, config_store, market_data_service, portfolio_service, user_service)
    return MarketAnalyticsWorker(
        settings=settings,
        session_factory=session_factory,
        show_sync_service=show_sync_service,
        market_data_service=market_data_service,
        recommendation_service=recommendation_service,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    worker = create_market_worker()
    worker.start()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        worker.shutdown()


if __name__ == "__main__":
    main()
