"""Market data sync, snapshots, and aggregate helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from statistics import mean, pstdev
from typing import Dict, List, Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Card, ListingsSnapshot, MarketHistoryAggregate, ShowMetadataSnapshot, StrategyRecommendation, SystemSetting
from app.services.show_api import ShowApiAdapter
from app.utils.enums import MarketPhase
from app.utils.scoring import quicksell_value_for_overall, safe_int, tax_adjusted_profit
from app.utils.team_maps import TEAM_METADATA
from app.utils.time import utcnow


@dataclass
class CardMarketContext:
    card: Card
    snapshot: Optional[ListingsSnapshot]
    aggregate: Optional[MarketHistoryAggregate]


class MarketDataService:
    """Coordinates card catalog sync and historical market snapshot storage."""

    ITEMS_CACHE_KEY = "show_items_full_sync"

    def __init__(self, settings: Settings, adapter: ShowApiAdapter):
        self.settings = settings
        self.adapter = adapter

    def sync_catalog_and_market(self, session: Session, current_phase: MarketPhase) -> Dict[str, int]:
        observed_at = utcnow()
        items = self._load_items_for_sync(session, observed_at)
        listings = self.adapter.fetch_listings()
        metadata = self._load_metadata_for_sync(session, observed_at)

        print("Fetched items:", len(items))
        print("Fetched listings:", len(listings))

        synced_cards = 0
        for item in items:
            card = self._upsert_card(session, item)
            if metadata:
                card.metadata_json.setdefault("metadata", metadata)
            synced_cards += 1
        session.flush()

        for listing in listings:
            self._record_snapshot(session, listing, observed_at)
        session.flush()
        self.compute_market_aggregates(session, current_phase, observed_at)
        return {"cards": synced_cards, "listings": len(listings)}

    def upsert_card_from_item(self, session: Session, item: Dict) -> Card:
        return self._upsert_card(session, item)

    def _load_items_for_sync(self, session: Session, as_of: datetime) -> List[Dict]:
        has_cards = session.scalar(select(Card.id).limit(1)) is not None
        if has_cards and not self._items_cache_stale(session, as_of):
            return []
        items = self.adapter.fetch_items(item_type="mlb_card")
        self._touch_items_cache(session, as_of, len(items))
        return items

    def _load_metadata_for_sync(self, session: Session, as_of: datetime) -> Dict:
        latest = session.scalar(select(ShowMetadataSnapshot).order_by(ShowMetadataSnapshot.fetched_at.desc()).limit(1))
        cache_cutoff = as_of - timedelta(hours=self.settings.show_metadata_cache_hours)
        if latest is not None and self._coerce_utc(latest.fetched_at) >= cache_cutoff:
            return latest.payload_json
        payload = self.adapter.fetch_metadata()
        if payload:
            session.add(
                ShowMetadataSnapshot(
                    series_json=list(payload.get("series", [])),
                    brands_json=list(payload.get("brands", [])),
                    sets_json=list(payload.get("sets", [])),
                    payload_json=payload,
                    fetched_at=as_of,
                )
            )
        return payload

    def _items_cache_stale(self, session: Session, as_of: datetime) -> bool:
        setting = session.get(SystemSetting, self.ITEMS_CACHE_KEY)
        if setting is None:
            return True
        last_synced_at = (setting.value_json or {}).get("last_synced_at")
        if not last_synced_at:
            return True
        try:
            parsed = datetime.fromisoformat(str(last_synced_at).replace("Z", "+00:00"))
        except ValueError:
            return True
        parsed = self._coerce_utc(parsed)
        return parsed < as_of - timedelta(hours=self.settings.show_items_cache_hours)

    def _touch_items_cache(self, session: Session, as_of: datetime, count: int) -> None:
        setting = session.get(SystemSetting, self.ITEMS_CACHE_KEY)
        if setting is None:
            setting = SystemSetting(key=self.ITEMS_CACHE_KEY)
        setting.value_json = {"last_synced_at": as_of.isoformat(), "count": count}
        setting.description = "Tracks the last full MLB items sync to avoid refetching the full item catalog every market cycle."
        session.add(setting)

    def record_listing_snapshot(self, session: Session, listing: Dict, observed_at: Optional[datetime] = None) -> ListingsSnapshot:
        session.flush()
        return self._record_snapshot(session, listing, observed_at or utcnow())

    def _upsert_card(self, session: Session, item: Dict) -> Card:
        item_id = str(item.get("uuid") or item.get("id") or item.get("item_id") or "")
        if not item_id:
            raise ValueError("Item payload missing stable identifier")
        card = session.scalar(select(Card).where(Card.item_id == item_id))
        if card is None:
            card = Card(item_id=item_id, name=item.get("name") or item_id)
        team_name = item.get("team")
        team_meta = TEAM_METADATA.get(team_name or "", {})
        overall = safe_int(item.get("ovr"))
        card.name = item.get("name") or card.name
        card.mlb_player_id = safe_int(item.get("mlb_player_id")) or card.mlb_player_id
        card.series = item.get("series")
        card.team = team_name
        card.division = team_meta.get("division") or item.get("division")
        card.league = team_meta.get("league") or item.get("league")
        card.overall = overall
        card.rarity = item.get("rarity")
        card.display_position = item.get("display_position")
        card.is_pitcher = not bool(item.get("is_hitter", True)) if item.get("is_hitter") is not None else None
        card.is_live_series = ((item.get("series") or "").lower() == "live") or bool(item.get("is_live_set"))
        card.quicksell_value = safe_int(item.get("quicksell_value")) or quicksell_value_for_overall(overall, self.settings.quicksell_tiers)
        card.is_sellable = item.get("is_sellable")
        merged = dict(card.metadata_json or {})
        merged.update(item)
        card.metadata_json = merged
        session.add(card)
        return card

    def _record_snapshot(self, session: Session, listing: Dict, observed_at: datetime) -> ListingsSnapshot:
        item = listing.get("item", {})
        item_id = str(item.get("uuid") or item.get("id") or item.get("item_id") or "")
        if not item_id:
            raise ValueError("Listing payload missing item identifier")
        if session.scalar(select(Card).where(Card.item_id == item_id)) is None:
            self._upsert_card(session, item)
        best_buy = safe_int(listing.get("best_buy_price") or listing.get("best_buy_order"))
        best_sell = safe_int(listing.get("best_sell_price") or listing.get("best_sell_order"))
        snapshot = ListingsSnapshot(
            item_id=item_id,
            buy_now=best_sell,
            sell_now=best_buy,
            best_buy_order=best_buy,
            best_sell_order=best_sell,
            spread=(best_sell - best_buy) if best_buy is not None and best_sell is not None else None,
            tax_adjusted_spread=tax_adjusted_profit(best_buy, best_sell, self.settings.market_tax_rate) if best_buy and best_sell else None,
            observed_at=observed_at,
        )
        session.add(snapshot)
        return snapshot

    def compute_market_aggregates(self, session: Session, current_phase: MarketPhase, as_of: Optional[datetime] = None) -> None:
        as_of = as_of or utcnow()
        item_ids = session.scalars(select(Card.item_id)).all()
        for item_id in item_ids:
            snapshots = session.scalars(
                select(ListingsSnapshot)
                .where(ListingsSnapshot.item_id == item_id)
                .where(ListingsSnapshot.observed_at >= as_of - timedelta(hours=24))
                .order_by(ListingsSnapshot.observed_at.desc())
            ).all()
            snapshots = self._eligible_market_snapshots(snapshots, current_phase, as_of)
            if not snapshots:
                continue
            avg_15m = self._average_price(snapshots, as_of - timedelta(minutes=15))
            avg_1h = self._average_price(snapshots, as_of - timedelta(hours=1))
            avg_6h = self._average_price(snapshots, as_of - timedelta(hours=6))
            avg_24h = self._average_price(snapshots, as_of - timedelta(hours=24))
            prices_24h = [snapshot.best_sell_order for snapshot in snapshots if snapshot.best_sell_order]
            volatility = 0.0
            if len(prices_24h) >= 2 and avg_24h:
                volatility = min((pstdev(prices_24h) / avg_24h) * 100.0, 100.0)
            spreads = [snapshot.tax_adjusted_spread for snapshot in snapshots if snapshot.tax_adjusted_spread is not None]
            avg_spread = mean(spreads) if spreads else 0.0
            liquidity = max(0.0, min(100.0, len(snapshots) * 4.0 + max(0.0, 35.0 - avg_spread / 200.0)))

            aggregate = session.scalar(
                select(MarketHistoryAggregate)
                .where(MarketHistoryAggregate.item_id == item_id)
                .where(MarketHistoryAggregate.phase == current_phase)
            )
            if aggregate is None:
                aggregate = MarketHistoryAggregate(item_id=item_id, phase=current_phase)
            aggregate.avg_price_15m = avg_15m
            aggregate.avg_price_1h = avg_1h
            aggregate.avg_price_6h = avg_6h
            aggregate.avg_price_24h = avg_24h
            aggregate.volatility_score = round(volatility, 2)
            aggregate.liquidity_score = round(liquidity, 2)
            session.add(aggregate)

    def build_market_observation(self, session: Session, as_of: Optional[datetime] = None) -> Dict[str, float]:
        as_of = as_of or utcnow()
        latest_snapshots = self.get_latest_snapshots(session)
        if not latest_snapshots:
            return {"recent_market_drop_pct": 0.0, "recent_supply_growth_pct": 0.0}

        one_hour_ago = as_of - timedelta(hours=1)
        twenty_four_hours_ago = as_of - timedelta(hours=24)
        recent = session.scalars(select(ListingsSnapshot).where(ListingsSnapshot.observed_at >= one_hour_ago)).all()
        prior = session.scalars(
            select(ListingsSnapshot)
            .where(ListingsSnapshot.observed_at >= twenty_four_hours_ago)
            .where(ListingsSnapshot.observed_at < one_hour_ago)
        ).all()
        recent_prices = [snapshot.best_sell_order for snapshot in recent if snapshot.best_sell_order]
        prior_prices = [snapshot.best_sell_order for snapshot in prior if snapshot.best_sell_order]
        recent_avg = mean(recent_prices) if recent_prices else 0.0
        prior_avg = mean(prior_prices) if prior_prices else recent_avg
        recent_market_drop_pct = ((recent_avg - prior_avg) / prior_avg) if prior_avg else 0.0
        recent_unique = len({snapshot.item_id for snapshot in recent})
        prior_unique = len({snapshot.item_id for snapshot in prior})
        recent_supply_growth_pct = ((recent_unique - prior_unique) / prior_unique) if prior_unique else 0.0
        return {
            "recent_market_drop_pct": recent_market_drop_pct,
            "recent_supply_growth_pct": recent_supply_growth_pct,
        }

    def list_market_contexts(self, session: Session) -> List[CardMarketContext]:
        latest_snapshots = self.get_latest_snapshots(session)
        latest_aggregates = self.get_latest_aggregates(session)
        cards = session.scalars(select(Card)).all()
        return [CardMarketContext(card, latest_snapshots.get(card.item_id), latest_aggregates.get(card.item_id)) for card in cards]

    def get_latest_snapshots(
        self,
        session: Session,
        item_ids: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, ListingsSnapshot]:
        if item_ids is not None and not item_ids:
            return {}
        subquery = select(ListingsSnapshot.item_id, func.max(ListingsSnapshot.observed_at).label("observed_at"))
        if item_ids is not None:
            subquery = subquery.where(ListingsSnapshot.item_id.in_(list(item_ids)))
        subquery = subquery.group_by(ListingsSnapshot.item_id).subquery()
        query = (
            select(ListingsSnapshot)
            .join(
                subquery,
                and_(
                    ListingsSnapshot.item_id == subquery.c.item_id,
                    ListingsSnapshot.observed_at == subquery.c.observed_at,
                ),
            )
            .order_by(ListingsSnapshot.observed_at.desc(), ListingsSnapshot.id.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        rows = session.execute(query).scalars().all()
        return {row.item_id: row for row in rows}

    def get_latest_aggregates(
        self,
        session: Session,
        item_ids: Optional[Sequence[str]] = None,
    ) -> Dict[str, MarketHistoryAggregate]:
        if item_ids is not None and not item_ids:
            return {}
        subquery = select(MarketHistoryAggregate.item_id, func.max(MarketHistoryAggregate.updated_at).label("updated_at"))
        if item_ids is not None:
            subquery = subquery.where(MarketHistoryAggregate.item_id.in_(list(item_ids)))
        subquery = subquery.group_by(MarketHistoryAggregate.item_id).subquery()
        query = select(MarketHistoryAggregate).join(
            subquery,
            and_(
                MarketHistoryAggregate.item_id == subquery.c.item_id,
                MarketHistoryAggregate.updated_at == subquery.c.updated_at,
            ),
        )
        rows = session.execute(query).scalars().all()
        return {row.item_id: row for row in rows}

    def get_card_context(self, session: Session, item_id: str) -> Optional[CardMarketContext]:
        card = session.scalar(select(Card).where(Card.item_id == item_id))
        if not card:
            return None
        snapshot = self.get_latest_snapshots(session).get(item_id)
        aggregate = self.get_latest_aggregates(session).get(item_id)
        return CardMarketContext(card=card, snapshot=snapshot, aggregate=aggregate)

    def get_recent_recommendations(self, session: Session, item_id: str, limit: int = 5) -> List[StrategyRecommendation]:
        return session.scalars(
            select(StrategyRecommendation)
            .where(StrategyRecommendation.item_id == item_id)
            .order_by(StrategyRecommendation.generated_at.desc())
            .limit(limit)
        ).all()

    def _average_price(self, snapshots: Sequence[ListingsSnapshot], window_start: datetime) -> Optional[float]:
        window_start = self._coerce_utc(window_start)
        prices = [
            snapshot.best_sell_order
            for snapshot in snapshots
            if self._coerce_utc(snapshot.observed_at) >= window_start and snapshot.best_sell_order
        ]
        return round(mean(prices), 2) if prices else None

    def _eligible_market_snapshots(
        self,
        snapshots: Sequence[ListingsSnapshot],
        current_phase: MarketPhase,
        as_of: datetime,
    ) -> List[ListingsSnapshot]:
        if not self.settings.feature_flags.launch_phase_logic_enabled:
            return list(snapshots)
        if current_phase == MarketPhase.EARLY_ACCESS:
            return list(snapshots)
        full_launch_cutover = datetime.combine(self.settings.full_launch_start_date, time.min, tzinfo=timezone.utc)
        as_of = self._coerce_utc(as_of)
        if as_of < full_launch_cutover:
            return list(snapshots)
        filtered = [snapshot for snapshot in snapshots if self._coerce_utc(snapshot.observed_at) >= full_launch_cutover]
        return filtered or list(snapshots)

    def _coerce_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
