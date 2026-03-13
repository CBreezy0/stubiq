"""Persistence and parsing layer for MLB The Show marketplace-adjacent endpoints."""

from __future__ import annotations

from collections import defaultdict
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any, Optional

from sqlalchemy import Float, case, cast, func, literal, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.config import Settings
from app.models import Card, ListingsSnapshot, MarketHistoryAggregate, MarketListing, PriceHistory, ShowMetadataSnapshot, ShowPlayerProfile, ShowRosterUpdate
from app.schemas.show_sync import (
    CardPriceHistoryPointResponse,
    CardPriceHistoryResponse,
    CardSearchItem,
    CardSearchResponse,
    LiveMarketListingListResponse,
    LiveMarketListingResponse,
    MarketMoverItem,
    MarketMoverListResponse,
    MarketMoverResponse,
    MarketMoversResponse,
    PriceHistoryPointResponse,
    PriceHistoryResponse,
    ShowListingsPagePayload,
    ShowMetadataPayload,
    ShowMetadataResponse,
    ShowPlayerProfileResponse,
    ShowPlayerSearchPayload,
    ShowPlayerSearchResponse,
    ShowRosterUpdateListResponse,
    ShowRosterUpdateResponse,
    ShowRosterUpdatesPayload,
)
from app.services.market_data import MarketDataService
from app.services.show_api import ShowApiAdapter
from app.utils.scoring import clamp, safe_int, tax_adjusted_profit
from app.utils.time import utcnow


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarketQueryFilters:
    min_roi: Optional[float] = None
    min_profit: Optional[int] = None
    max_buy_price: Optional[int] = None
    min_liquidity: Optional[float] = None
    rarity: Optional[str] = None
    series: Optional[str] = None
    team: Optional[str] = None
    position: Optional[str] = None
    sort_by: str = "profit"
    sort_order: str = "desc"
    limit: int = 50


class ShowSyncService:
    """Validates MLB 26 payloads and persists reusable market-supporting data."""

    DEFAULT_SCAN_LIMIT = 2000
    BATCH_SIZE = 50
    BATCH_PAUSE_SECONDS = 0.2

    def __init__(self, settings: Settings, adapter: ShowApiAdapter, market_data_service: MarketDataService):
        self.settings = settings
        self.adapter = adapter
        self.market_data_service = market_data_service

    def compute_listing_metrics(self, best_buy_price: Optional[int], best_sell_price: Optional[int]) -> dict[str, Optional[float]]:
        spread = None
        estimated_profit = None
        roi_percent = None
        if best_buy_price is not None and best_sell_price is not None:
            spread = best_sell_price - best_buy_price
            estimated_profit = tax_adjusted_profit(best_buy_price, best_sell_price, self.settings.market_tax_rate)
            if best_buy_price > 0:
                roi_percent = round((estimated_profit / float(best_buy_price)) * 100.0, 2)
        return {
            "spread": spread,
            "estimated_profit": estimated_profit,
            "roi_percent": roi_percent,
        }

    def sync_listings(self, session: Session, item_type: str = "mlb_card", page_limit: Optional[int] = None) -> dict[str, int]:
        synced = 0
        pages_processed = 0
        batch_number = 0
        batch_items = 0
        observed_at = utcnow()

        for page_payload in self.adapter.fetch_listings_pages(item_type=item_type, page_limit=page_limit):
            page = ShowListingsPagePayload.model_validate(page_payload)
            pages_processed += 1
            for listing in page.listings:
                self._persist_listing(session, listing=listing, source_page=page.page, observed_at=observed_at)
                synced += 1
                batch_items += 1

                if batch_items >= self.BATCH_SIZE:
                    batch_number += 1
                    self._complete_listing_batch(session, batch_number=batch_number, sleep_between_batches=True)
                    batch_items = 0

        if batch_items:
            batch_number += 1
            self._complete_listing_batch(session, batch_number=batch_number, sleep_between_batches=False)

        return {"pages": pages_processed, "listings": synced}

    def _persist_listing(self, session: Session, listing: Any, source_page: Optional[int], observed_at: datetime) -> None:
        item_payload = listing.item.model_dump(mode="json")
        self.market_data_service.upsert_card_from_item(session, item_payload)
        self.market_data_service.record_listing_snapshot(session, listing.model_dump(mode="json"), observed_at=observed_at)

        best_buy = safe_int(listing.best_buy_price)
        best_sell = safe_int(listing.best_sell_price)
        metrics = self.compute_listing_metrics(best_buy, best_sell)
        item_id = listing.item.uuid
        record = session.scalar(select(MarketListing).where(MarketListing.item_id == item_id))
        if record is None:
            record = MarketListing(item_id=item_id)
        record.listing_name = listing.listing_name or listing.item.name
        record.best_buy_price = best_buy
        record.best_sell_price = best_sell
        record.spread = metrics["spread"]
        record.estimated_profit = metrics["estimated_profit"]
        record.roi_percent = metrics["roi_percent"]
        record.source_page = source_page
        record.payload_json = listing.model_dump(mode="json")
        record.last_seen_at = observed_at
        session.add(record)
        session.add(
            PriceHistory(
                uuid=item_id,
                buy_price=best_buy,
                sell_price=best_sell,
                timestamp=observed_at,
            )
        )
        session.flush()

    def _complete_listing_batch(self, session: Session, batch_number: int, sleep_between_batches: bool) -> None:
        logger.info("Processing batch %s", batch_number)
        session.flush()
        session.expunge_all()
        if sleep_between_batches:
            time.sleep(self.BATCH_PAUSE_SECONDS)

    def sync_metadata(self, session: Session) -> ShowMetadataSnapshot:
        payload = ShowMetadataPayload.model_validate(self.adapter.fetch_metadata())
        snapshot = ShowMetadataSnapshot(
            series_json=[entry.model_dump(mode="json") for entry in payload.series],
            brands_json=[entry.model_dump(mode="json") for entry in payload.brands],
            sets_json=list(payload.sets),
            payload_json=payload.model_dump(mode="json"),
            fetched_at=utcnow(),
        )
        session.add(snapshot)
        session.flush()
        return snapshot

    def search_player_profiles(self, session: Session, username: str) -> list[ShowPlayerProfile]:
        payload = ShowPlayerSearchPayload.model_validate(self.adapter.search_player_profiles(username))
        synced_at = utcnow()
        profiles: list[ShowPlayerProfile] = []
        for profile_payload in payload.universal_profiles:
            profile = session.scalar(select(ShowPlayerProfile).where(ShowPlayerProfile.username == profile_payload.username))
            if profile is None:
                profile = ShowPlayerProfile(username=profile_payload.username)
            profile.display_level = profile_payload.display_level
            profile.games_played = safe_int(profile_payload.games_played)
            profile.vanity_json = dict(profile_payload.vanity or {})
            profile.most_played_modes_json = dict(profile_payload.most_played_modes or {})
            profile.lifetime_hitting_stats_json = list(profile_payload.lifetime_hitting_stats or [])
            profile.lifetime_defensive_stats_json = list(profile_payload.lifetime_defensive_stats or [])
            profile.online_data_json = list(profile_payload.online_data or [])
            profile.payload_json = profile_payload.model_dump(mode="json")
            profile.last_synced_at = synced_at
            session.add(profile)
            profiles.append(profile)
        session.flush()
        return profiles

    def sync_roster_updates(self, session: Session) -> dict[str, int]:
        payload = ShowRosterUpdatesPayload.model_validate(self.adapter.fetch_roster_updates_payload())
        synced = 0
        synced_at = utcnow()
        for update_payload in payload.roster_updates:
            payload_json = update_payload.model_dump(mode="json", exclude_none=True)
            remote_id = self._stable_roster_update_id(payload_json)
            record = session.scalar(select(ShowRosterUpdate).where(ShowRosterUpdate.remote_id == remote_id))
            if record is None:
                record = ShowRosterUpdate(remote_id=remote_id)
            record.title = self._first_non_empty(update_payload.title, update_payload.name)
            record.summary = self._first_non_empty(update_payload.summary, update_payload.description)
            record.published_at = self._parse_datetime(
                self._first_non_empty(update_payload.published_at, update_payload.updated_at, update_payload.date)
            )
            record.payload_json = payload_json
            record.last_synced_at = synced_at
            session.add(record)
            synced += 1
        session.flush()
        return {"updates": synced}

    def get_market_listings_response(
        self,
        session: Session,
        *,
        min_roi: Optional[float] = None,
        min_profit: Optional[int] = None,
        max_buy_price: Optional[int] = None,
        rarity: Optional[str] = None,
        series: Optional[str] = None,
        team: Optional[str] = None,
        position: Optional[str] = None,
        sort_by: str = "profit",
        sort_order: str = "desc",
        limit: int = 50,
        force_refresh: bool = False,
    ) -> LiveMarketListingListResponse:
        try:
            filters = MarketQueryFilters(
                min_roi=min_roi,
                min_profit=min_profit,
                max_buy_price=max_buy_price,
                rarity=rarity,
                series=series,
                team=team,
                position=position,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
            )
            rows = self._build_listing_rows(session, force_refresh=force_refresh)
            filtered = self._apply_listing_filters(rows, filters)
            sorted_rows = self._sort_listing_rows(filtered, filters.sort_by, filters.sort_order, default_sort="profit")
            return LiveMarketListingListResponse(count=min(len(sorted_rows), limit), items=sorted_rows[:limit])
        except SQLAlchemyError:
            logger.exception(
                "Database query failed while building market listings response (limit=%s, sort_by=%s, sort_order=%s)",
                limit,
                sort_by,
                sort_order,
            )
            raise

    def get_flip_listings_response(
        self,
        session: Session,
        *,
        min_roi: Optional[float] = None,
        min_profit: Optional[int] = None,
        max_buy_price: Optional[int] = None,
        rarity: Optional[str] = None,
        series: Optional[str] = None,
        team: Optional[str] = None,
        position: Optional[str] = None,
        sort_by: str = "flip_score",
        sort_order: str = "desc",
        limit: int = 25,
        force_refresh: bool = False,
    ) -> LiveMarketListingListResponse:
        try:
            filters = MarketQueryFilters(
                min_roi=min_roi,
                min_profit=min_profit,
                max_buy_price=max_buy_price,
                rarity=rarity,
                series=series,
                team=team,
                position=position,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
            )
            rows = [
                row
                for row in self._build_listing_rows(session, force_refresh=force_refresh)
                if (row.profit_after_tax or 0) > 0 and (row.roi or 0.0) > 0
            ]
            filtered = self._apply_listing_filters(rows, filters)
            sorted_rows = self._sort_listing_rows(filtered, filters.sort_by, filters.sort_order, default_sort="flip_score")
            return LiveMarketListingListResponse(count=min(len(sorted_rows), limit), items=sorted_rows[:limit])
        except SQLAlchemyError:
            logger.exception(
                "Database query failed while building flip listings response (limit=%s, sort_by=%s, sort_order=%s)",
                limit,
                sort_by,
                sort_order,
            )
            raise

    def get_top_flip_listings_response(
        self,
        session: Session,
        *,
        roi_min: Optional[float] = None,
        profit_min: Optional[int] = None,
        liquidity_min: Optional[float] = None,
        rarity: Optional[str] = None,
        team: Optional[str] = None,
        series: Optional[str] = None,
        sort_by: str = "flip_score",
        force_refresh: bool = False,
    ) -> LiveMarketListingListResponse:
        limit = 50
        if force_refresh:
            logger.info("Ignoring force_refresh request; top flips endpoint now serves cached data only")
        try:
            filters = MarketQueryFilters(
                min_roi=roi_min,
                min_profit=profit_min,
                min_liquidity=liquidity_min,
                rarity=rarity,
                series=series,
                team=team,
                sort_by=sort_by,
                sort_order="desc",
                limit=limit,
            )
            if self._has_cached_market_listings(session):
                items = self._top_flip_rows_from_market_listings(session, filters)
            else:
                logger.info("Serving top flips from cached snapshots because warm listing rows are unavailable")
                items = self._top_flip_rows_from_snapshots(session, filters)
            return LiveMarketListingListResponse(count=len(items), items=items)
        except SQLAlchemyError:
            logger.exception(
                "Database query failed while building top flip listings response (sort_by=%s, rarity=%s, team=%s, series=%s)",
                sort_by,
                rarity,
                team,
                series,
            )
            raise

    def get_market_movers_response(self, session: Session, limit: int = 50) -> MarketMoversResponse:
        limit = max(1, min(limit, 50))
        try:
            if self._has_cached_market_listings(session):
                items = self._market_movers_from_market_listings(session, limit=limit)
            else:
                logger.info("Serving market movers from cached snapshots because warm listing rows are unavailable")
                items = self._market_movers_from_snapshots(session, limit=limit)
            return MarketMoversResponse(count=len(items), items=items)
        except SQLAlchemyError:
            logger.exception("Database query failed while building market movers response (limit=%s)", limit)
            raise

    def _has_cached_market_listings(self, session: Session) -> bool:
        return session.scalar(select(MarketListing.id).limit(1)) is not None

    def _top_flip_rows_from_market_listings(
        self,
        session: Session,
        filters: MarketQueryFilters,
    ) -> list[LiveMarketListingResponse]:
        aggregate_subquery = self._latest_market_aggregate_subquery()
        profit_expr = MarketListing.estimated_profit
        roi_expr = MarketListing.roi_percent
        liquidity_expr = aggregate_subquery.c.liquidity_score
        sort_expr = self._top_flip_sort_expression(filters.sort_by, profit_expr, roi_expr, liquidity_expr)
        query = (
            select(
                MarketListing.item_id.label("uuid"),
                func.coalesce(MarketListing.listing_name, Card.name, MarketListing.item_id).label("name"),
                MarketListing.best_buy_price.label("best_buy_price"),
                MarketListing.best_sell_price.label("best_sell_price"),
                MarketListing.spread.label("spread"),
                profit_expr.label("profit_after_tax"),
                roi_expr.label("roi"),
                Card.display_position.label("position"),
                Card.series.label("series"),
                Card.team.label("team"),
                Card.overall.label("overall"),
                Card.rarity.label("rarity"),
                literal(0).label("order_volume"),
                liquidity_expr.label("liquidity_score"),
                MarketListing.last_seen_at.label("last_seen_at"),
            )
            .select_from(MarketListing)
            .outerjoin(Card, Card.item_id == MarketListing.item_id)
            .outerjoin(aggregate_subquery, aggregate_subquery.c.item_id == MarketListing.item_id)
            .where(profit_expr.is_not(None))
            .where(profit_expr > 0)
            .where(roi_expr.is_not(None))
            .where(roi_expr > 0)
            .where(liquidity_expr.is_not(None))
            .where(liquidity_expr > 0)
        )
        query = self._apply_top_flip_sql_filters(
            query,
            filters,
            roi_expr=roi_expr,
            profit_expr=profit_expr,
            liquidity_expr=liquidity_expr,
            rarity_expr=Card.rarity,
            team_expr=Card.team,
            series_expr=Card.series,
        )
        rows = session.execute(
            query.order_by(sort_expr.desc().nullslast(), MarketListing.last_seen_at.desc()).limit(filters.limit)
        ).mappings().all()
        return [self._live_listing_response_from_mapping(row) for row in rows]

    def _top_flip_rows_from_snapshots(
        self,
        session: Session,
        filters: MarketQueryFilters,
    ) -> list[LiveMarketListingResponse]:
        aggregate_subquery = self._latest_market_aggregate_subquery()
        latest_snapshots = self._latest_snapshot_rows_subquery()
        profit_expr = latest_snapshots.c.profit_after_tax
        roi_expr = case(
            (
                latest_snapshots.c.best_buy_price > 0,
                (cast(latest_snapshots.c.profit_after_tax, Float) / cast(latest_snapshots.c.best_buy_price, Float)) * 100.0,
            ),
            else_=None,
        )
        liquidity_expr = aggregate_subquery.c.liquidity_score
        sort_expr = self._top_flip_sort_expression(filters.sort_by, profit_expr, roi_expr, liquidity_expr)
        query = (
            select(
                latest_snapshots.c.item_id.label("uuid"),
                func.coalesce(Card.name, latest_snapshots.c.item_id).label("name"),
                latest_snapshots.c.best_buy_price.label("best_buy_price"),
                latest_snapshots.c.best_sell_price.label("best_sell_price"),
                latest_snapshots.c.spread.label("spread"),
                profit_expr.label("profit_after_tax"),
                roi_expr.label("roi"),
                Card.display_position.label("position"),
                Card.series.label("series"),
                Card.team.label("team"),
                Card.overall.label("overall"),
                Card.rarity.label("rarity"),
                literal(0).label("order_volume"),
                liquidity_expr.label("liquidity_score"),
                latest_snapshots.c.last_seen_at.label("last_seen_at"),
            )
            .select_from(latest_snapshots)
            .outerjoin(Card, Card.item_id == latest_snapshots.c.item_id)
            .outerjoin(aggregate_subquery, aggregate_subquery.c.item_id == latest_snapshots.c.item_id)
            .where(profit_expr.is_not(None))
            .where(profit_expr > 0)
            .where(roi_expr.is_not(None))
            .where(roi_expr > 0)
            .where(liquidity_expr.is_not(None))
            .where(liquidity_expr > 0)
        )
        query = self._apply_top_flip_sql_filters(
            query,
            filters,
            roi_expr=roi_expr,
            profit_expr=profit_expr,
            liquidity_expr=liquidity_expr,
            rarity_expr=Card.rarity,
            team_expr=Card.team,
            series_expr=Card.series,
        )
        rows = session.execute(
            query.order_by(sort_expr.desc().nullslast(), latest_snapshots.c.last_seen_at.desc()).limit(filters.limit)
        ).mappings().all()
        return [self._live_listing_response_from_mapping(row) for row in rows]

    def _market_movers_from_market_listings(self, session: Session, limit: int) -> list[MarketMoverItem]:
        aggregate_subquery = self._latest_market_aggregate_subquery()
        cutoff = utcnow() - timedelta(hours=1)
        previous_history_price = (
            select(PriceHistory.sell_price)
            .where(PriceHistory.uuid == MarketListing.item_id)
            .where(PriceHistory.sell_price.is_not(None))
            .where(PriceHistory.timestamp < MarketListing.last_seen_at)
            .where(PriceHistory.timestamp <= cutoff)
            .order_by(PriceHistory.timestamp.desc())
            .limit(1)
            .scalar_subquery()
        )
        previous_snapshot_price = (
            select(ListingsSnapshot.best_sell_order)
            .where(ListingsSnapshot.item_id == MarketListing.item_id)
            .where(ListingsSnapshot.best_sell_order.is_not(None))
            .where(ListingsSnapshot.observed_at < MarketListing.last_seen_at)
            .where(ListingsSnapshot.observed_at <= cutoff)
            .order_by(ListingsSnapshot.observed_at.desc())
            .limit(1)
            .scalar_subquery()
        )
        previous_price_expr = func.coalesce(previous_history_price, previous_snapshot_price)
        price_change_expr = MarketListing.best_sell_price - previous_price_expr
        change_percent_expr = cast(price_change_expr, Float) / cast(previous_price_expr, Float)
        rows = session.execute(
            select(
                MarketListing.item_id.label("item_id"),
                func.coalesce(MarketListing.listing_name, Card.name, MarketListing.item_id).label("name"),
                MarketListing.best_buy_price.label("best_buy_price"),
                MarketListing.best_sell_price.label("best_sell_price"),
                price_change_expr.label("price_change"),
                change_percent_expr.label("change_percent"),
                aggregate_subquery.c.liquidity_score.label("liquidity_score"),
            )
            .select_from(MarketListing)
            .outerjoin(Card, Card.item_id == MarketListing.item_id)
            .outerjoin(aggregate_subquery, aggregate_subquery.c.item_id == MarketListing.item_id)
            .where(MarketListing.best_sell_price.is_not(None))
            .where(previous_price_expr.is_not(None))
            .where(previous_price_expr != 0)
            .where(func.abs(change_percent_expr) >= 0.10)
            .order_by(func.abs(change_percent_expr).desc(), func.abs(price_change_expr).desc())
            .limit(limit)
        ).mappings().all()
        return self._market_mover_items_from_rows(rows)

    def _market_movers_from_snapshots(self, session: Session, limit: int) -> list[MarketMoverItem]:
        aggregate_subquery = self._latest_market_aggregate_subquery()
        latest_snapshots = self._latest_snapshot_rows_subquery()
        cutoff = utcnow() - timedelta(hours=1)
        previous_history_price = (
            select(PriceHistory.sell_price)
            .where(PriceHistory.uuid == latest_snapshots.c.item_id)
            .where(PriceHistory.sell_price.is_not(None))
            .where(PriceHistory.timestamp < latest_snapshots.c.last_seen_at)
            .where(PriceHistory.timestamp <= cutoff)
            .order_by(PriceHistory.timestamp.desc())
            .limit(1)
            .scalar_subquery()
        )
        previous_snapshot_price = (
            select(ListingsSnapshot.best_sell_order)
            .where(ListingsSnapshot.item_id == latest_snapshots.c.item_id)
            .where(ListingsSnapshot.best_sell_order.is_not(None))
            .where(ListingsSnapshot.observed_at < latest_snapshots.c.last_seen_at)
            .where(ListingsSnapshot.observed_at <= cutoff)
            .order_by(ListingsSnapshot.observed_at.desc())
            .limit(1)
            .scalar_subquery()
        )
        previous_price_expr = func.coalesce(previous_history_price, previous_snapshot_price)
        price_change_expr = latest_snapshots.c.best_sell_price - previous_price_expr
        change_percent_expr = cast(price_change_expr, Float) / cast(previous_price_expr, Float)
        rows = session.execute(
            select(
                latest_snapshots.c.item_id.label("item_id"),
                func.coalesce(Card.name, latest_snapshots.c.item_id).label("name"),
                latest_snapshots.c.best_buy_price.label("best_buy_price"),
                latest_snapshots.c.best_sell_price.label("best_sell_price"),
                price_change_expr.label("price_change"),
                change_percent_expr.label("change_percent"),
                aggregate_subquery.c.liquidity_score.label("liquidity_score"),
            )
            .select_from(latest_snapshots)
            .outerjoin(Card, Card.item_id == latest_snapshots.c.item_id)
            .outerjoin(aggregate_subquery, aggregate_subquery.c.item_id == latest_snapshots.c.item_id)
            .where(latest_snapshots.c.best_sell_price.is_not(None))
            .where(previous_price_expr.is_not(None))
            .where(previous_price_expr != 0)
            .where(func.abs(change_percent_expr) >= 0.10)
            .order_by(func.abs(change_percent_expr).desc(), func.abs(price_change_expr).desc())
            .limit(limit)
        ).mappings().all()
        return self._market_mover_items_from_rows(rows)

    def _apply_top_flip_sql_filters(
        self,
        query,
        filters: MarketQueryFilters,
        *,
        roi_expr,
        profit_expr,
        liquidity_expr,
        rarity_expr,
        team_expr,
        series_expr,
    ):
        min_roi = self._normalize_roi_filter(filters.min_roi)
        if min_roi is not None:
            query = query.where(roi_expr >= min_roi)
        if filters.min_profit is not None:
            query = query.where(profit_expr >= filters.min_profit)
        if filters.min_liquidity is not None:
            query = query.where(liquidity_expr >= filters.min_liquidity)
        if filters.rarity:
            query = query.where(func.lower(rarity_expr) == filters.rarity.strip().lower())
        if filters.team:
            query = query.where(func.lower(team_expr) == filters.team.strip().lower())
        if filters.series:
            query = query.where(func.lower(series_expr) == filters.series.strip().lower())
        return query

    def _top_flip_sort_expression(self, sort_by: str, profit_expr, roi_expr, liquidity_expr):
        normalized_sort = sort_by if sort_by in {"roi", "profit_after_tax", "profit_per_minute", "flip_score", "profit"} else "flip_score"
        if normalized_sort in {"profit", "profit_after_tax"}:
            return profit_expr
        if normalized_sort == "roi":
            return roi_expr
        if normalized_sort == "profit_per_minute":
            return cast(profit_expr, Float) * cast(liquidity_expr, Float)
        return cast(roi_expr, Float) * cast(liquidity_expr, Float)

    def _latest_market_aggregate_subquery(self):
        ranked_aggregates = (
            select(
                MarketHistoryAggregate.item_id.label("item_id"),
                MarketHistoryAggregate.liquidity_score.label("liquidity_score"),
                func.row_number().over(
                    partition_by=MarketHistoryAggregate.item_id,
                    order_by=(MarketHistoryAggregate.updated_at.desc(), MarketHistoryAggregate.id.desc()),
                ).label("rank"),
            )
            .subquery()
        )
        return (
            select(
                ranked_aggregates.c.item_id,
                ranked_aggregates.c.liquidity_score,
            )
            .where(ranked_aggregates.c.rank == 1)
            .subquery()
        )

    def _latest_snapshot_rows_subquery(self):
        ranked_snapshots = (
            select(
                ListingsSnapshot.item_id.label("item_id"),
                ListingsSnapshot.best_buy_order.label("best_buy_price"),
                ListingsSnapshot.best_sell_order.label("best_sell_price"),
                ListingsSnapshot.spread.label("spread"),
                ListingsSnapshot.tax_adjusted_spread.label("profit_after_tax"),
                ListingsSnapshot.observed_at.label("last_seen_at"),
                func.row_number().over(
                    partition_by=ListingsSnapshot.item_id,
                    order_by=(ListingsSnapshot.observed_at.desc(), ListingsSnapshot.id.desc()),
                ).label("rank"),
            )
            .subquery()
        )
        return (
            select(
                ranked_snapshots.c.item_id,
                ranked_snapshots.c.best_buy_price,
                ranked_snapshots.c.best_sell_price,
                ranked_snapshots.c.spread,
                ranked_snapshots.c.profit_after_tax,
                ranked_snapshots.c.last_seen_at,
            )
            .where(ranked_snapshots.c.rank == 1)
            .subquery()
        )

    def _live_listing_response_from_mapping(self, row) -> LiveMarketListingResponse:
        profit_after_tax = row["profit_after_tax"]
        liquidity_score = row["liquidity_score"]
        roi = row["roi"]
        return LiveMarketListingResponse(
            uuid=row["uuid"],
            name=row["name"],
            best_buy_price=row["best_buy_price"],
            best_sell_price=row["best_sell_price"],
            spread=row["spread"],
            profit_after_tax=profit_after_tax,
            roi=round(float(roi), 2) if roi is not None else None,
            position=row["position"],
            series=row["series"],
            team=row["team"],
            overall=row["overall"],
            rarity=row["rarity"],
            order_volume=int(row["order_volume"] or 0),
            liquidity_score=round(float(liquidity_score), 2) if liquidity_score is not None else None,
            profit_per_minute=self._profit_per_minute(profit_after_tax, liquidity_score),
            flip_score=self._ranked_flip_score(roi, liquidity_score),
            last_seen_at=row["last_seen_at"],
        )

    def _market_mover_items_from_rows(self, rows) -> list[MarketMoverItem]:
        items: list[MarketMoverItem] = []
        for row in rows:
            price_change = row["price_change"]
            change_percent = row["change_percent"]
            items.append(
                MarketMoverItem(
                    item_id=row["item_id"],
                    name=row["name"],
                    best_buy_price=row["best_buy_price"],
                    best_sell_price=row["best_sell_price"],
                    price_change=int(price_change),
                    change_percent=round(float(change_percent), 4),
                    liquidity_score=round(float(row["liquidity_score"]), 2) if row["liquidity_score"] is not None else None,
                )
            )
        return items

    def get_market_history_response(self, session: Session, uuid: str, days: int = 1) -> PriceHistoryResponse:
        points = self._history_points_for_item(session, uuid, days)
        card = session.scalar(select(Card).where(Card.item_id == uuid))
        return PriceHistoryResponse(uuid=uuid, name=card.name if card else uuid, days=days, points=points)

    def get_card_search_response(self, session: Session, q: str, limit: int = 50) -> CardSearchResponse:
        query = q.strip().lower()
        if not query:
            return CardSearchResponse(items=[])
        limit = max(1, min(limit, 50))
        try:
            rows = self._build_listing_rows(session)
            items = [
                CardSearchItem(
                    item_id=row.uuid,
                    name=row.name,
                    team=row.team,
                    series=row.series,
                    best_sell_price=row.best_sell_price,
                    best_buy_price=row.best_buy_price,
                )
                for row in rows
                if query in row.name.lower()
                or query in (row.team or "").lower()
                or query in (row.series or "").lower()
            ]
            return CardSearchResponse(items=items[:limit])
        except SQLAlchemyError:
            logger.exception("Database query failed while building card search response for q=%s", q)
            raise

    def get_card_price_history_response(self, session: Session, item_id: str) -> Optional[CardPriceHistoryResponse]:
        try:
            card = session.scalar(select(Card).where(Card.item_id == item_id))
            if card is None:
                return None
            points = self._card_history_points(session, item_id=item_id, limit=200)
            return CardPriceHistoryResponse(item_id=item_id, name=card.name, points=points)
        except SQLAlchemyError:
            logger.exception("Database query failed while building card price history response for item_id=%s", item_id)
            raise

    def get_trending_response(self, session: Session, limit: int = 25) -> MarketMoverListResponse:
        rows = self._build_market_movers(session, window_hours=self.settings.market_trending_window_hours)
        rows = [row for row in rows if abs(row.change_pct or 0.0) >= 3.0]
        rows.sort(key=lambda row: (row.trend_score, abs(row.change_pct or 0.0)), reverse=True)
        return MarketMoverListResponse(count=min(len(rows), limit), items=rows[:limit])

    def get_biggest_movers_response(self, session: Session, limit: int = 25) -> MarketMoverListResponse:
        rows = self._build_market_movers(session, window_hours=self.settings.market_trending_window_hours)
        rows.sort(key=lambda row: abs(row.change_pct or 0.0), reverse=True)
        return MarketMoverListResponse(count=min(len(rows), limit), items=rows[:limit])

    def get_metadata_response(self, session: Session, force_refresh: bool = False) -> ShowMetadataResponse:
        snapshot = self.get_latest_metadata(session)
        if snapshot is None or force_refresh:
            snapshot = self.sync_metadata(session)
        return ShowMetadataResponse(
            series=list(snapshot.series_json or []),
            brands=list(snapshot.brands_json or []),
            sets=list(snapshot.sets_json or []),
            fetched_at=snapshot.fetched_at,
        )

    def get_player_search_response(
        self,
        session: Session,
        username: str,
        force_refresh: bool = True,
    ) -> ShowPlayerSearchResponse:
        username = username.strip()
        if not username:
            return ShowPlayerSearchResponse(count=0, items=[])
        profiles = self.search_player_profiles(session, username) if force_refresh else []
        if not profiles:
            cached = self.get_player_profile(session, username)
            profiles = [cached] if cached is not None else []
        items = [ShowPlayerProfileResponse.model_validate(profile) for profile in profiles]
        return ShowPlayerSearchResponse(count=len(items), items=items)

    def get_roster_updates_response(
        self,
        session: Session,
        limit: int = 50,
        force_refresh: bool = False,
    ) -> ShowRosterUpdateListResponse:
        rows = self.list_roster_updates(session, limit=limit)
        if force_refresh or not rows:
            self.sync_roster_updates(session)
            rows = self.list_roster_updates(session, limit=limit)
        items = [ShowRosterUpdateResponse.model_validate(row) for row in rows[:limit]]
        return ShowRosterUpdateListResponse(count=len(items), items=items)

    def list_market_listings(self, session: Session, limit: int = 50) -> list[MarketListing]:
        return session.scalars(
            select(MarketListing)
            .options(selectinload(MarketListing.card))
            .order_by(MarketListing.last_seen_at.desc())
            .limit(limit)
        ).all()

    def get_latest_metadata(self, session: Session) -> Optional[ShowMetadataSnapshot]:
        return session.scalar(select(ShowMetadataSnapshot).order_by(ShowMetadataSnapshot.fetched_at.desc()))

    def get_player_profile(self, session: Session, username: str) -> Optional[ShowPlayerProfile]:
        return session.scalar(select(ShowPlayerProfile).where(ShowPlayerProfile.username == username))

    def list_roster_updates(self, session: Session, limit: int = 50) -> list[ShowRosterUpdate]:
        return session.scalars(
            select(ShowRosterUpdate)
            .order_by(ShowRosterUpdate.published_at.desc().nullslast(), ShowRosterUpdate.last_synced_at.desc())
            .limit(limit)
        ).all()

    def _build_listing_rows(self, session: Session, force_refresh: bool = False) -> list[LiveMarketListingResponse]:
        if force_refresh:
            logger.info("Ignoring force_refresh request; market endpoints now serve cached data only")
        rows = self.list_market_listings(session, limit=self.DEFAULT_SCAN_LIMIT)
        if rows:
            return self._listing_rows_from_records(session, rows)
        snapshot_rows = self._listing_rows_from_snapshots(session)
        if snapshot_rows:
            logger.info("Serving market endpoint response from cached snapshots because warm listing rows are unavailable")
            return snapshot_rows
        logger.warning("No warm market data available; returning empty cached market response without syncing")
        return []

    def _listing_rows_from_records(self, session: Session, rows: list[MarketListing]) -> list[LiveMarketListingResponse]:
        item_ids = [row.item_id for row in rows]
        stats = self._history_stats_for_items(session, item_ids)
        aggregates = self.market_data_service.get_latest_aggregates(session)
        return [
            self._listing_row_from_record(row, stats.get(row.item_id, {}), aggregates.get(row.item_id))
            for row in rows
        ]

    def _listing_rows_from_snapshots(self, session: Session) -> list[LiveMarketListingResponse]:
        latest_snapshots = self.market_data_service.get_latest_snapshots(session)
        if not latest_snapshots:
            return []
        cards = {
            card.item_id: card
            for card in session.scalars(select(Card).where(Card.item_id.in_(list(latest_snapshots.keys())))).all()
        }
        stats = self._history_stats_for_items(session, list(latest_snapshots.keys()))
        aggregates = self.market_data_service.get_latest_aggregates(session)
        rows: list[LiveMarketListingResponse] = []
        for item_id, snapshot in latest_snapshots.items():
            card = cards.get(item_id)
            rows.append(self._listing_row_from_snapshot(item_id, snapshot, card, stats.get(item_id, {}), aggregates.get(item_id)))
        return rows

    def _apply_listing_filters(self, rows: list[LiveMarketListingResponse], filters: MarketQueryFilters) -> list[LiveMarketListingResponse]:
        min_roi = self._normalize_roi_filter(filters.min_roi)
        items: list[LiveMarketListingResponse] = []
        for row in rows:
            if min_roi is not None and (row.roi or 0.0) < min_roi:
                continue
            if filters.min_profit is not None and (row.profit_after_tax or 0) < filters.min_profit:
                continue
            if filters.max_buy_price is not None and (row.best_buy_price or 0) > filters.max_buy_price:
                continue
            if filters.min_liquidity is not None and (row.liquidity_score or 0.0) < filters.min_liquidity:
                continue
            if filters.rarity and not self._match_text(row.rarity, filters.rarity):
                continue
            if filters.series and not self._match_text(row.series, filters.series):
                continue
            if filters.team and not self._match_text(row.team, filters.team):
                continue
            if filters.position and not self._match_text(row.position, filters.position):
                continue
            items.append(row)
        return items

    def _sort_listing_rows(
        self,
        rows: list[LiveMarketListingResponse],
        sort_by: str,
        sort_order: str,
        *,
        default_sort: str,
    ) -> list[LiveMarketListingResponse]:
        field = self._coerce_sort_field(sort_by, default_sort)
        reverse = str(sort_order).lower() != "asc"

        def key(row: LiveMarketListingResponse):
            mapping = {
                "name": row.name.lower(),
                "buy_price": row.best_buy_price or 0,
                "sell_price": row.best_sell_price or 0,
                "spread": row.spread or 0,
                "profit": row.profit_after_tax or 0,
                "profit_after_tax": row.profit_after_tax or 0,
                "profit_per_minute": row.profit_per_minute or 0.0,
                "roi": row.roi or 0.0,
                "flip_score": row.flip_score or 0.0,
                "order_volume": row.order_volume,
                "last_seen": row.last_seen_at,
            }
            return mapping[field]

        return sorted(rows, key=key, reverse=reverse)

    def _history_points_for_item(self, session: Session, uuid: str, days: int) -> list[PriceHistoryPointResponse]:
        since = utcnow() - timedelta(days=days)
        rows = session.scalars(
            select(PriceHistory)
            .where(PriceHistory.uuid == uuid)
            .where(PriceHistory.timestamp >= since)
            .order_by(PriceHistory.timestamp.asc())
        ).all()
        if rows:
            return [PriceHistoryPointResponse(timestamp=row.timestamp, buy_price=row.buy_price, sell_price=row.sell_price) for row in rows]

        snapshots = session.scalars(
            select(ListingsSnapshot)
            .where(ListingsSnapshot.item_id == uuid)
            .where(ListingsSnapshot.observed_at >= since)
            .order_by(ListingsSnapshot.observed_at.asc())
        ).all()
        return [
            PriceHistoryPointResponse(
                timestamp=snapshot.observed_at,
                buy_price=snapshot.best_buy_order,
                sell_price=snapshot.best_sell_order,
            )
            for snapshot in snapshots
        ]

    def _card_history_points(self, session: Session, *, item_id: str, limit: int) -> list[CardPriceHistoryPointResponse]:
        rows = session.scalars(
            select(PriceHistory)
            .where(PriceHistory.uuid == item_id)
            .order_by(PriceHistory.timestamp.desc())
            .limit(limit)
        ).all()
        if rows:
            ordered_rows = list(reversed(rows))
            return [
                CardPriceHistoryPointResponse(
                    timestamp=row.timestamp,
                    best_buy_price=row.buy_price,
                    best_sell_price=row.sell_price,
                    volume=None,
                )
                for row in ordered_rows
            ]

        snapshots = session.scalars(
            select(ListingsSnapshot)
            .where(ListingsSnapshot.item_id == item_id)
            .order_by(ListingsSnapshot.observed_at.desc())
            .limit(limit)
        ).all()
        ordered_snapshots = list(reversed(snapshots))
        return [
            CardPriceHistoryPointResponse(
                timestamp=snapshot.observed_at,
                best_buy_price=snapshot.best_buy_order,
                best_sell_price=snapshot.best_sell_order,
                volume=None,
            )
            for snapshot in ordered_snapshots
        ]

    def _build_market_movers(self, session: Session, window_hours: int) -> list[MarketMoverResponse]:
        series_by_item = self._history_series_for_items(session, window_hours=window_hours)
        if not series_by_item:
            return []
        cards = {
            card.item_id: card
            for card in session.scalars(select(Card).where(Card.item_id.in_(list(series_by_item.keys())))).all()
        }
        movers: list[MarketMoverResponse] = []
        for item_id, points in series_by_item.items():
            if len(points) < 2:
                continue
            previous_price = points[0][2] if points[0][2] is not None else points[0][1]
            current_price = points[-1][2] if points[-1][2] is not None else points[-1][1]
            if previous_price in (None, 0) or current_price is None:
                continue
            change_amount = current_price - previous_price
            change_pct = round((change_amount / float(previous_price)) * 100.0, 2)
            change_events = self._change_events(points)
            trend_score = round(abs(change_pct) * 0.7 + min(change_events * 8.0, 30.0) + min(len(points) * 1.5, 20.0), 2)
            card = cards.get(item_id)
            movers.append(
                MarketMoverResponse(
                    uuid=item_id,
                    name=card.name if card else item_id,
                    current_price=current_price,
                    previous_price=previous_price,
                    change_amount=change_amount,
                    change_pct=change_pct,
                    trend_score=trend_score,
                    position=card.display_position if card else None,
                    series=card.series if card else None,
                    team=card.team if card else None,
                    rarity=card.rarity if card else None,
                    points=len(points),
                    last_seen_at=points[-1][0],
                )
            )
        return movers

    def _history_series_for_items(self, session: Session, item_ids: Optional[list[str]] = None, window_hours: int = 24) -> dict[str, list[tuple[datetime, Optional[int], Optional[int]]]]:
        since = utcnow() - timedelta(hours=window_hours)
        rows_query = select(PriceHistory).where(PriceHistory.timestamp >= since).order_by(PriceHistory.uuid.asc(), PriceHistory.timestamp.asc())
        if item_ids:
            rows_query = rows_query.where(PriceHistory.uuid.in_(item_ids))
        rows = session.scalars(rows_query).all()
        series_by_item: dict[str, list[tuple[datetime, Optional[int], Optional[int]]]] = defaultdict(list)
        for row in rows:
            series_by_item[row.uuid].append((row.timestamp, row.buy_price, row.sell_price))
        if series_by_item:
            return series_by_item

        snapshots_query = select(ListingsSnapshot).where(ListingsSnapshot.observed_at >= since).order_by(ListingsSnapshot.item_id.asc(), ListingsSnapshot.observed_at.asc())
        if item_ids:
            snapshots_query = snapshots_query.where(ListingsSnapshot.item_id.in_(item_ids))
        snapshots = session.scalars(snapshots_query).all()
        for snapshot in snapshots:
            series_by_item[snapshot.item_id].append((snapshot.observed_at, snapshot.best_buy_order, snapshot.best_sell_order))
        return series_by_item

    def _history_stats_for_items(self, session: Session, item_ids: list[str]) -> dict[str, dict[str, int]]:
        if not item_ids:
            return {}
        series_by_item = self._history_series_for_items(session, item_ids=item_ids, window_hours=self.settings.market_trending_window_hours)
        stats: dict[str, dict[str, int]] = {}
        for item_id, points in series_by_item.items():
            change_events = self._change_events(points)
            order_volume = max(len(points), change_events * 2)
            stats[item_id] = {
                "points": len(points),
                "change_events": change_events,
                "order_volume": order_volume,
            }
        return stats

    def _historical_price_before_window(
        self,
        points: list[tuple[datetime, Optional[int], Optional[int]]],
        *,
        current_timestamp: datetime,
        hours_back: int,
    ) -> Optional[int]:
        if not points:
            return None
        target_time = current_timestamp - timedelta(hours=hours_back)
        fallback_price: Optional[int] = None
        target_price: Optional[int] = None
        for timestamp, buy_price, sell_price in points:
            if timestamp >= current_timestamp:
                break
            candidate_price = sell_price
            if candidate_price is None:
                continue
            fallback_price = candidate_price
            if timestamp <= target_time:
                target_price = candidate_price
        return target_price if target_price is not None else fallback_price

    def _listing_row_from_record(
        self,
        record: MarketListing,
        stats: dict[str, int],
        aggregate: Optional[MarketHistoryAggregate] = None,
    ) -> LiveMarketListingResponse:
        card = record.card
        order_volume = int(stats.get("order_volume", 0))
        flip_score = self._flip_score(
            profit=record.estimated_profit,
            roi=record.roi_percent,
            spread=record.spread,
            order_volume=order_volume,
        )
        return LiveMarketListingResponse(
            uuid=record.item_id,
            name=record.listing_name or (card.name if card else record.item_id),
            best_buy_price=record.best_buy_price,
            best_sell_price=record.best_sell_price,
            spread=record.spread,
            profit_after_tax=record.estimated_profit,
            roi=record.roi_percent,
            position=card.display_position if card else None,
            series=card.series if card else None,
            team=card.team if card else None,
            overall=card.overall if card else None,
            rarity=card.rarity if card else None,
            order_volume=order_volume,
            liquidity_score=aggregate.liquidity_score if aggregate else None,
            profit_per_minute=self._profit_per_minute(record.estimated_profit, aggregate.liquidity_score if aggregate else None),
            flip_score=flip_score,
            last_seen_at=record.last_seen_at,
        )

    def _listing_row_from_snapshot(
        self,
        item_id: str,
        snapshot: ListingsSnapshot,
        card: Optional[Card],
        stats: dict[str, int],
        aggregate: Optional[MarketHistoryAggregate] = None,
    ) -> LiveMarketListingResponse:
        metrics = self.compute_listing_metrics(snapshot.best_buy_order, snapshot.best_sell_order)
        order_volume = int(stats.get("order_volume", 0))
        profit = int(metrics["estimated_profit"]) if metrics["estimated_profit"] is not None else snapshot.tax_adjusted_spread
        roi = metrics["roi_percent"]
        spread = int(metrics["spread"]) if metrics["spread"] is not None else snapshot.spread
        return LiveMarketListingResponse(
            uuid=item_id,
            name=card.name if card else item_id,
            best_buy_price=snapshot.best_buy_order,
            best_sell_price=snapshot.best_sell_order,
            spread=spread,
            profit_after_tax=profit,
            roi=roi,
            position=card.display_position if card else None,
            series=card.series if card else None,
            team=card.team if card else None,
            overall=card.overall if card else None,
            rarity=card.rarity if card else None,
            order_volume=order_volume,
            liquidity_score=aggregate.liquidity_score if aggregate else None,
            profit_per_minute=self._profit_per_minute(profit, aggregate.liquidity_score if aggregate else None),
            flip_score=self._flip_score(profit=profit, roi=roi, spread=spread, order_volume=order_volume),
            last_seen_at=snapshot.observed_at,
        )

    def _flip_score(
        self,
        *,
        profit: Optional[int],
        roi: Optional[float],
        spread: Optional[int],
        order_volume: int,
    ) -> float:
        profit_score = clamp(((profit or 0) / 1000.0) * 100.0)
        roi_score = clamp(roi or 0.0)
        volume_score = clamp(order_volume * 5.0)
        spread_score = clamp(((spread or 0) / 800.0) * 100.0)
        return round((profit_score * 0.35) + (roi_score * 0.30) + (volume_score * 0.20) + (spread_score * 0.15), 2)

    def _ranked_flip_score(self, roi: Optional[float], liquidity_score: Optional[float]) -> float:
        return round((roi or 0.0) * (liquidity_score or 0.0), 2)

    def _profit_per_minute(self, profit: Optional[int], liquidity_score: Optional[float]) -> Optional[float]:
        if profit is None or liquidity_score is None:
            return None
        return round(float(profit) * liquidity_score, 2)

    def _normalize_roi_filter(self, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        return round(value * 100.0, 4) if 0 < value < 1 else value

    def _coerce_sort_field(self, sort_by: str, default_sort: str) -> str:
        valid_fields = {"name", "buy_price", "sell_price", "spread", "profit", "profit_after_tax", "profit_per_minute", "roi", "flip_score", "order_volume", "last_seen"}
        return sort_by if sort_by in valid_fields else default_sort

    def _match_text(self, value: Optional[str], query: str) -> bool:
        if value is None:
            return False
        return value.strip().lower() == query.strip().lower()

    def _change_events(self, points: list[tuple[datetime, Optional[int], Optional[int]]]) -> int:
        changes = 0
        previous: Optional[tuple[Optional[int], Optional[int]]] = None
        for _, buy_price, sell_price in points:
            state = (buy_price, sell_price)
            if previous is not None and state != previous:
                changes += 1
            previous = state
        return changes

    def _stable_roster_update_id(self, payload: dict[str, Any]) -> str:
        candidate = self._first_non_empty(payload.get("id"), payload.get("update_id"), payload.get("slug"), payload.get("uuid"))
        if candidate:
            return str(candidate)
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return digest[:40]

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        text = str(value).strip()
        if not text:
            return None
        normalized = text.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _first_non_empty(self, *values: Any) -> Optional[str]:
        for value in values:
            if value not in (None, ""):
                return str(value)
        return None
