"""Persistence and parsing layer for MLB The Show marketplace-adjacent endpoints."""

from __future__ import annotations

from collections import defaultdict
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.config import Settings
from app.models import Card, ListingsSnapshot, MarketHistoryAggregate, MarketListing, PriceHistory, ShowMetadataSnapshot, ShowPlayerProfile, ShowRosterUpdate
from app.schemas.show_sync import (
    LiveMarketListingListResponse,
    LiveMarketListingResponse,
    MarketMoverListResponse,
    MarketMoverResponse,
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
        pages = self.adapter.fetch_listings_pages(item_type=item_type, page_limit=page_limit)
        synced = 0
        observed_at = utcnow()

        for page_payload in pages:
            page = ShowListingsPagePayload.model_validate(page_payload)
            for listing in page.listings:
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
                record.source_page = page.page
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
                synced += 1

        session.flush()
        return {"pages": len(pages), "listings": synced}

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

    def get_top_flip_listings_response(self, session: Session, force_refresh: bool = False) -> LiveMarketListingListResponse:
        limit = 50
        try:
            rows = [
                row.model_copy(
                    update={
                        "flip_score": self._ranked_flip_score(row.roi, row.liquidity_score),
                    }
                )
                for row in self._build_listing_rows(session, force_refresh=force_refresh)
                if (row.profit_after_tax or 0) > 0 and (row.roi or 0.0) > 0 and (row.liquidity_score or 0.0) > 0
            ]
            rows.sort(
                key=lambda row: ((row.flip_score or 0.0), (row.roi or 0.0), (row.liquidity_score or 0.0)),
                reverse=True,
            )
            return LiveMarketListingListResponse(count=min(len(rows), limit), items=rows[:limit])
        except SQLAlchemyError:
            logger.exception("Database query failed while building top flip listings response")
            raise

    def get_market_history_response(self, session: Session, uuid: str, days: int = 1) -> PriceHistoryResponse:
        points = self._history_points_for_item(session, uuid, days)
        card = session.scalar(select(Card).where(Card.item_id == uuid))
        return PriceHistoryResponse(uuid=uuid, name=card.name if card else uuid, days=days, points=points)

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
            self.sync_listings(session)
        rows = self.list_market_listings(session, limit=self.DEFAULT_SCAN_LIMIT)
        if rows:
            return self._listing_rows_from_records(session, rows)
        snapshot_rows = self._listing_rows_from_snapshots(session)
        if snapshot_rows:
            return snapshot_rows
        self.sync_listings(session)
        rows = self.list_market_listings(session, limit=self.DEFAULT_SCAN_LIMIT)
        return self._listing_rows_from_records(session, rows)

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

    def _normalize_roi_filter(self, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        return round(value * 100.0, 4) if value <= 1 else value

    def _coerce_sort_field(self, sort_by: str, default_sort: str) -> str:
        valid_fields = {"name", "buy_price", "sell_price", "spread", "profit", "roi", "flip_score", "order_volume", "last_seen"}
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
