from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.models import Card, ListingsSnapshot, MarketHistoryAggregate
from app.services.market_data import MarketDataService
from app.utils.enums import MarketPhase


def test_post_launch_aggregate_excludes_early_access_baseline(app, session):
    settings = app.state.settings
    service = MarketDataService(settings, adapter=None)
    session.add(
        Card(
            item_id="card-agg-1",
            name="Launch Card",
            is_live_series=True,
            quicksell_value=400,
            metadata_json={},
        )
    )
    session.add_all(
        [
            ListingsSnapshot(
                item_id="card-agg-1",
                best_buy_order=1900,
                best_sell_order=2000,
                buy_now=2000,
                sell_now=1900,
                spread=100,
                tax_adjusted_spread=-100,
                observed_at=datetime(2026, 3, 16, 18, 0, tzinfo=timezone.utc),
            ),
            ListingsSnapshot(
                item_id="card-agg-1",
                best_buy_order=900,
                best_sell_order=1000,
                buy_now=1000,
                sell_now=900,
                spread=100,
                tax_adjusted_spread=0,
                observed_at=datetime(2026, 3, 17, 12, 0, tzinfo=timezone.utc),
            ),
        ]
    )
    session.commit()

    service.compute_market_aggregates(
        session,
        MarketPhase.FULL_LAUNCH_SUPPLY_SHOCK,
        as_of=datetime(2026, 3, 17, 13, 0, tzinfo=timezone.utc),
    )
    session.commit()

    aggregate = session.scalar(
        select(MarketHistoryAggregate)
        .where(MarketHistoryAggregate.item_id == "card-agg-1")
        .where(MarketHistoryAggregate.phase == MarketPhase.FULL_LAUNCH_SUPPLY_SHOCK)
    )
    assert aggregate is not None
    assert aggregate.avg_price_24h == 1000.0
