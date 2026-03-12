from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models import ListingsSnapshot
from app.services.liquidity_ranker import LiquidityRanker
from app.services.seed import seed_dev_data
from app.utils.time import utcnow


def _listing(item_id: str, price: int) -> dict:
    return {
        "item": {
            "item_id": item_id,
            "id": item_id,
            "name": f"Card {item_id}",
            "series": "Live",
            "ovr": 84,
            "is_live_set": True,
        },
        "best_buy_order": price - 100,
        "best_sell_order": price,
    }


def test_scheduler_registers_fast_market_scan(app):
    scheduler_manager = app.state.scheduler_manager
    scheduler_manager.settings = replace(scheduler_manager.settings, scheduler_enabled=True)

    scheduler_manager.start()
    try:
        job = scheduler_manager.scheduler.get_job("fast_market_scan")
        assert job is not None
        assert job.id == "fast_market_scan"
    finally:
        scheduler_manager.shutdown()


def test_liquidity_ranker_orders_by_recent_activity(session):
    now = utcnow()
    for _ in range(3):
        session.add(
            ListingsSnapshot(
                item_id="hot-card",
                buy_now=1200,
                sell_now=1000,
                best_buy_order=1000,
                best_sell_order=1200,
                spread=200,
                tax_adjusted_spread=80,
                observed_at=now,
            )
        )
    for _ in range(2):
        session.add(
            ListingsSnapshot(
                item_id="warm-card",
                buy_now=900,
                sell_now=800,
                best_buy_order=800,
                best_sell_order=900,
                spread=100,
                tax_adjusted_spread=10,
                observed_at=now,
            )
        )
    session.add(
        ListingsSnapshot(
            item_id="cold-card",
            buy_now=700,
            sell_now=600,
            best_buy_order=600,
            best_sell_order=700,
            spread=100,
            tax_adjusted_spread=30,
            observed_at=now,
        )
    )
    session.commit()

    top_cards = LiquidityRanker.get_top_liquid_cards(session, limit=3)

    assert top_cards[:3] == ["hot-card", "warm-card", "cold-card"]


def test_fast_market_scan_falls_back_to_top_200_without_liquidity_history(app, monkeypatch):
    with TestClient(app):
        listings = [_listing(f"scan-card-{index}", 1000 + index) for index in range(350)]
        monkeypatch.setattr(app.state.market_data_service.adapter, "fetch_listings", lambda: listings)

        with app.state.session_factory() as session:
            before = session.scalar(select(func.count()).select_from(ListingsSnapshot)) or 0

        app.state.scheduler_manager.fast_market_scan()

        with app.state.session_factory() as session:
            after = session.scalar(select(func.count()).select_from(ListingsSnapshot)) or 0

        assert after - before == 200


def test_fast_market_scan_filters_to_most_liquid_cards(app, monkeypatch):
    with TestClient(app):
        with app.state.session_factory() as session:
            seed_dev_data(session)
            session.commit()
            now = utcnow()
            for index in range(220):
                session.add(
                    ListingsSnapshot(
                        item_id=f"scan-card-{index}",
                        buy_now=1200 + index,
                        sell_now=1000 + index,
                        best_buy_order=1000 + index,
                        best_sell_order=1200 + index,
                        spread=200,
                        tax_adjusted_spread=80,
                        observed_at=now,
                    )
                )
            session.commit()

        listings = [_listing(f"scan-card-{index}", 1500 + index) for index in range(350)]
        monkeypatch.setattr(app.state.market_data_service.adapter, "fetch_listings", lambda: listings)

        with app.state.session_factory() as session:
            before = session.scalar(select(func.count()).select_from(ListingsSnapshot)) or 0

        app.state.scheduler_manager.fast_market_scan()

        with app.state.session_factory() as session:
            after = session.scalar(select(func.count()).select_from(ListingsSnapshot)) or 0

        assert after - before == 200
