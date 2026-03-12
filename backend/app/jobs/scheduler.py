"""APScheduler integration for recurring sync and recommendation jobs."""

from __future__ import annotations

import logging
from typing import Callable, Dict, List

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.services.liquidity_ranker import LiquidityRanker
from app.utils.time import UTC, utcnow


logger = logging.getLogger(__name__)


class SchedulerManager:
    """Owns background jobs for market snapshots, MLB stats, and strategy refreshes."""

    def __init__(
        self,
        settings,
        session_factory,
        market_data_service,
        mlb_data_service,
        recommendation_service,
    ):
        self.settings = settings
        self.session_factory = session_factory
        self.market_data_service = market_data_service
        self.mlb_data_service = mlb_data_service
        self.recommendation_service = recommendation_service
        self.scheduler = BackgroundScheduler(timezone=UTC)
        self._started = False
        self._job_map: Dict[str, Callable[[], None]] = {
            "market_refresh": self.refresh_market_data,
            "fast_market_scan": self.fast_market_scan,
            "stats_refresh": self.refresh_player_stats,
            "lineup_refresh": self.refresh_lineups,
            "recommendations_refresh": self.refresh_recommendations,
            "roster_update_predictions_refresh": self.refresh_roster_update_predictions,
        }

    def start(self):
        if self._started or not self.settings.scheduler_enabled:
            return
        self.scheduler.add_job(
            self.refresh_market_data,
            IntervalTrigger(minutes=self.settings.market_snapshot_interval_minutes),
            id="market_refresh",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.fast_market_scan,
            IntervalTrigger(seconds=10),
            id="fast_market_scan",
            replace_existing=True,
        )
        logger.info("Configured fast market scan to run every 10 seconds")
        self.scheduler.add_job(
            self.refresh_player_stats,
            CronTrigger(hour=self.settings.daily_stats_refresh_hour_utc, minute=5),
            id="stats_refresh",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.refresh_lineups,
            IntervalTrigger(minutes=self.settings.lineup_refresh_interval_minutes),
            id="lineup_refresh",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.refresh_recommendations,
            IntervalTrigger(minutes=self.settings.strategy_refresh_interval_minutes),
            id="recommendations_refresh",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.refresh_roster_update_predictions,
            IntervalTrigger(hours=6),
            id="roster_update_predictions_refresh",
            replace_existing=True,
        )
        self.scheduler.start()
        self._started = True
        logger.info("Background scheduler started")

    def shutdown(self):
        if self._started:
            self.scheduler.shutdown(wait=False)
            self._started = False

    def is_running(self) -> bool:
        return self._started

    def run_job_now(self, job_name: str) -> List[str]:
        accepted: List[str] = []
        if job_name == "all":
            for name in self._job_map:
                self._job_map[name]()
                accepted.append(name)
            return accepted
        if job_name not in self._job_map:
            return accepted
        self._job_map[job_name]()
        accepted.append(job_name)
        return accepted

    def refresh_market_data(self):
        with self.session_factory() as session:
            phase = self.recommendation_service.get_phase(session).phase
            self.market_data_service.sync_catalog_and_market(session, phase)
            session.commit()

    def fast_market_scan(self):
        with self.session_factory() as session:
            phase = self.recommendation_service.get_phase(session).phase
            top_cards = LiquidityRanker.get_top_liquid_cards(session, limit=200)
            listings = self.market_data_service.adapter.fetch_listings()
            if top_cards:
                top_card_ids = set(top_cards)
                filtered = [
                    listing
                    for listing in listings
                    if str(
                        listing.get("item", {}).get("item_id")
                        or listing.get("item", {}).get("id")
                        or listing.get("item", {}).get("uuid")
                        or ""
                    ) in top_card_ids
                ]
                listings = filtered[:200]
            else:
                listings = listings[:200]
            observed_at = utcnow()
            for listing in listings:
                self.market_data_service._record_snapshot(session, listing, observed_at)
            session.commit()
            logger.info(
                "Fast scanner processing %s high-liquidity cards (frequency=%ss, phase=%s)",
                len(listings),
                10,
                phase.value,
            )

    def refresh_player_stats(self):
        with self.session_factory() as session:
            self.mlb_data_service.sync_player_stats(session)
            session.commit()

    def refresh_lineups(self):
        with self.session_factory() as session:
            self.mlb_data_service.sync_game_day_context(session)
            session.commit()

    def refresh_recommendations(self):
        with self.session_factory() as session:
            self.recommendation_service.generate_and_store_recommendations(session)
            session.commit()

    def refresh_roster_update_predictions(self):
        with self.session_factory() as session:
            self.recommendation_service.generate_and_store_roster_update_predictions(session)
            session.commit()
