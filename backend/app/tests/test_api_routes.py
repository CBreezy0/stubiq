from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from fastapi.testclient import TestClient

from app.models import MarketListing, PriceHistory, ShowMetadataSnapshot, ShowRosterUpdate
from app.utils.time import utcnow


def _signup(client: TestClient, email: str = "api-user@example.com", password: str = "Password123!", display_name: str = "API User"):
    response = client.post(
        "/auth/signup",
        json={"email": email, "password": password, "display_name": display_name, "platform": "ios"},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    headers = {"Authorization": f"Bearer {payload['access_token']}"}
    return payload, headers



def test_health_route(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["game_year"] == 26
    assert "database_url" not in payload



def test_healthz_route(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}



def test_readyz_route(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"database": "connected"}



def test_dashboard_summary_route(client):
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    payload = response.json()
    assert "market_phase" in payload
    assert "top_flips" in payload
    assert "collection_priorities" in payload



def test_market_endpoints(client):
    listings = client.get("/market/listings")
    flips = client.get("/market/flips")
    top_flips = client.get(
        "/flips/top",
        params={
            "roi_min": 1,
            "profit_min": 100,
            "liquidity_min": 50,
            "sort_by": "profit_per_minute",
        },
    )
    filtered_top_flips = client.get(
        "/flips/top",
        params={
            "rarity": "Diamond",
            "team": "Dodgers",
            "series": "Live",
            "sort_by": "roi",
        },
    )
    strategy_flips = client.get("/market/strategy-flips")
    floors = client.get("/market/floors")
    assert listings.status_code == 200
    assert flips.status_code == 200
    assert top_flips.status_code == 200
    assert filtered_top_flips.status_code == 200
    assert strategy_flips.status_code == 200
    assert floors.status_code == 200
    assert listings.json()["items"]
    assert {"uuid", "name", "best_buy_price", "best_sell_price", "spread", "profit_after_tax", "roi"}.issubset(listings.json()["items"][0])
    if top_flips.json()["items"]:
        top_items = top_flips.json()["items"]
        assert len(top_items) <= 50
        assert {"liquidity_score", "flip_score", "roi", "profit_per_minute"}.issubset(top_items[0])
        assert all((item["roi"] or 0) >= 1 for item in top_items)
        assert all((item["profit_after_tax"] or 0) >= 100 for item in top_items)
        assert all((item["liquidity_score"] or 0) >= 50 for item in top_items)
        scores = [item["profit_per_minute"] for item in top_items]
        assert scores == sorted(scores, reverse=True)
    if filtered_top_flips.json()["items"]:
        filtered_items = filtered_top_flips.json()["items"]
        assert all(item["rarity"] == "Diamond" for item in filtered_items)
        assert all(item["team"] == "Dodgers" for item in filtered_items)
        assert all(item["series"] == "Live" for item in filtered_items)
        roi_scores = [item["roi"] for item in filtered_items]
        assert roi_scores == sorted(roi_scores, reverse=True)


def test_market_movers_endpoint(client, monkeypatch):
    from app.api.routes import market as market_routes
    from app.schemas.show_sync import MarketMoverItem, MarketMoversResponse

    def fake_load_cached_response(cache_key, model_type):
        assert cache_key == "market:movers"
        return MarketMoversResponse(
            count=1,
            items=[
                MarketMoverItem(
                    item_id="live-riley-greene-26",
                    name="Riley Greene",
                    best_buy_price=None,
                    best_sell_price=7000,
                    price_change=2000,
                    change_percent=0.4,
                    liquidity_score=None,
                )
            ],
        )

    monkeypatch.setattr(market_routes, "load_cached_response", fake_load_cached_response)

    response = client.get("/market/movers")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["items"]
    assert {"item_id", "name", "best_buy_price", "best_sell_price", "price_change", "change_percent", "liquidity_score"}.issubset(payload["items"][0])
    target = payload["items"][0]
    assert target["item_id"] == "live-riley-greene-26"
    assert target["best_sell_price"] == 7000
    assert target["price_change"] == 2000
    assert target["change_percent"] > 0.10


def test_market_listings_service_caps_limit_before_loading(app, monkeypatch):
    service = app.state.show_sync_service
    captured = {}

    def fake_build_listing_rows(session, force_refresh=False, limit=50):
        captured["limit"] = limit
        return []

    monkeypatch.setattr(service, "_build_listing_rows", fake_build_listing_rows)

    with app.state.session_factory() as session:
        response = service.get_market_listings_response(session, limit=200)

    assert captured["limit"] == 50
    assert response.count == 0
    assert response.items == []


def test_market_endpoint_limit_caps(client, app, monkeypatch):
    from app.api.routes import flips as flips_routes
    from app.api.routes import market as market_routes
    from app.schemas.cards import CardSummaryResponse
    from app.schemas.market import MarketOpportunityListResponse, MarketOpportunityResponse
    from app.schemas.show_sync import (
        LiveMarketListingListResponse,
        LiveMarketListingResponse,
        MarketMoverItem,
        MarketMoverListResponse,
        MarketMoversResponse,
    )
    from app.utils.enums import MarketPhase, RecommendationAction

    now = utcnow()
    captured_limits = {}

    def make_flip(index: int) -> LiveMarketListingResponse:
        return LiveMarketListingResponse(
            uuid=f"card-{index}",
            name=f"Card {index}",
            best_buy_price=1000 + index,
            best_sell_price=1500 + index,
            spread=500,
            profit_after_tax=350 + index,
            roi=10.0 + index,
            rarity="Diamond",
            team="Dodgers",
            series="Live",
            liquidity_score=75.0,
            profit_per_minute=200.0 + index,
            flip_score=200.0 + index,
            last_seen_at=now,
        )

    def make_floor(index: int) -> MarketOpportunityResponse:
        return MarketOpportunityResponse(
            item_id=f"floor-{index}",
            card=CardSummaryResponse(
                item_id=f"floor-{index}",
                name=f"Floor Card {index}",
                is_live_series=True,
                latest_best_sell_order=1000 + index,
                observed_at=now,
            ),
            action=RecommendationAction.WATCH,
            expected_profit_per_flip=100,
            fill_velocity_score=0.0,
            liquidity_score=0.0,
            risk_score=0.0,
            floor_proximity_score=75.0,
            market_phase=MarketPhase.STABILIZATION,
            confidence=0.8,
            rationale="cached",
        )

    def fake_flips_cache(cache_key, model_type):
        assert cache_key == "flips:top"
        items = [make_flip(index) for index in range(40)]
        return LiveMarketListingListResponse(count=len(items), items=items)

    def fake_market_cache(cache_key, model_type):
        if cache_key == "market:movers":
            items = [
                MarketMoverItem(
                    item_id=f"mover-{index}",
                    name=f"Mover {index}",
                    best_buy_price=None,
                    best_sell_price=2000 + index,
                    price_change=250 + index,
                    change_percent=0.5 + (index / 100.0),
                    liquidity_score=None,
                )
                for index in range(40)
            ]
            return MarketMoversResponse(count=len(items), items=items)
        if cache_key == "market:floors":
            items = [make_floor(index) for index in range(40)]
            return MarketOpportunityListResponse(phase=MarketPhase.STABILIZATION, count=len(items), items=items)
        return None

    def fake_market_listings_response(db, **params):
        captured_limits["market_listings"] = params["limit"]
        return LiveMarketListingListResponse(count=0, items=[])

    def fake_trending_response(db, limit):
        captured_limits["market_trending"] = limit
        return MarketMoverListResponse(count=0, items=[])

    monkeypatch.setattr(flips_routes, "load_cached_response", fake_flips_cache)
    monkeypatch.setattr(market_routes, "load_cached_response", fake_market_cache)
    monkeypatch.setattr(app.state.show_sync_service, "get_market_listings_response", fake_market_listings_response)
    monkeypatch.setattr(app.state.show_sync_service, "get_trending_response", fake_trending_response)

    listings_response = client.get("/market/listings", params={"limit": 200})
    top_flips_response = client.get("/flips/top", params={"limit": 50})
    movers_response = client.get("/market/movers", params={"limit": 50})
    floors_response = client.get("/market/floors", params={"limit": 100})
    trending_response = client.get("/market/trending", params={"limit": 100})

    assert listings_response.status_code == 200
    assert top_flips_response.status_code == 200
    assert movers_response.status_code == 200
    assert floors_response.status_code == 200
    assert trending_response.status_code == 200

    assert captured_limits["market_listings"] == 50
    assert captured_limits["market_trending"] == 25
    assert top_flips_response.json()["count"] == 25
    assert movers_response.json()["count"] == 25
    assert floors_response.json()["count"] == 25


def test_card_price_history_endpoint(client, app):
    now = utcnow()
    with app.state.session_factory() as session:
        session.query(PriceHistory).filter(PriceHistory.uuid == "live-riley-greene-26").delete()
        for index in range(205):
            session.add(
                PriceHistory(
                    uuid="live-riley-greene-26",
                    buy_price=4000 + index,
                    sell_price=5000 + index,
                    timestamp=now - timedelta(minutes=205 - index),
                )
            )
        session.commit()

    response = client.get("/cards/live-riley-greene-26/history")
    assert response.status_code == 200
    payload = response.json()
    assert payload["item_id"] == "live-riley-greene-26"
    assert len(payload["points"]) == 200
    assert {"timestamp", "best_buy_price", "best_sell_price", "volume"}.issubset(payload["points"][0])
    assert payload["points"][0]["timestamp"] < payload["points"][-1]["timestamp"]
    assert payload["points"][0]["volume"] is None



def test_portfolio_add_and_remove(client):
    _, headers = _signup(client)
    add_response = client.post(
        "/portfolio/manual-add",
        headers=headers,
        json={
            "item_id": "custom-card-1",
            "card_name": "Custom Card",
            "quantity": 2,
            "avg_acquisition_cost": 1500,
            "locked_for_collection": False,
            "source": "manual",
        },
    )
    assert add_response.status_code == 200
    assert any(item["item_id"] == "custom-card-1" for item in add_response.json()["items"])

    remove_response = client.post(
        "/portfolio/manual-remove",
        headers=headers,
        json={"item_id": "custom-card-1", "quantity": 1, "remove_all": False},
    )
    assert remove_response.status_code == 200
    remaining = next(item for item in remove_response.json()["items"] if item["item_id"] == "custom-card-1")
    assert remaining["quantity"] == 1



def test_settings_market_phase_override(client):
    response = client.post("/settings/market-phase", json={"phase": "CONTENT_DROP", "notes": "test override"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["override_phase"] == "CONTENT_DROP"



def test_jobs_run_now(client):
    response = client.post("/jobs/run-now", json={"job_name": "recommendations_refresh"})
    assert response.status_code == 200
    assert response.json()["accepted_jobs"] == ["recommendations_refresh"]



def test_settings_engine_thresholds_get_and_patch(client, app):
    signup_payload, headers = _signup(client, email="settings-user@example.com")

    get_response = client.get("/settings/engine-thresholds", headers=headers)
    assert get_response.status_code == 200
    initial = get_response.json()
    assert "floor_buy_margin" in initial
    assert "flip_profit_minimum" in initial

    patch_response = client.patch(
        "/settings/engine-thresholds",
        headers=headers,
        json={
            "flip_profit_minimum": 50000,
            "collection_lock_penalty": 22.5,
            "gatekeeper_hold_weight": 14.0,
        },
    )
    assert patch_response.status_code == 200
    patched = patch_response.json()
    assert patched["flip_profit_minimum"] == 50000
    assert patched["collection_lock_penalty"] == 22.5
    assert patched["gatekeeper_hold_weight"] == 14.0
    assert patched["updated_at"] is not None

    get_after = client.get("/settings/engine-thresholds", headers=headers)
    assert get_after.status_code == 200
    refreshed = get_after.json()
    assert refreshed["flip_profit_minimum"] == 50000

    with app.state.session_factory() as session:
        user = app.state.user_service.get_user_by_id(session, signup_payload["user"]["id"])
        live_thresholds = app.state.recommendation_service._engine_thresholds(session, user)
        assert live_thresholds["low_risk_profit_min"] == 50000
        assert live_thresholds["collection_early_access_penalty"] == 22.5
        assert live_thresholds["collection_owned_gatekeeper_priority_bonus"] == 14.0



def test_investments_player_analysis_route(client):
    response = client.get('/investments/player/Riley%20Greene')
    assert response.status_code == 200
    payload = response.json()
    assert payload['player_name'] == 'Riley Greene'
    assert payload['item_id'] == 'live-riley-greene-26'



def test_user_scoped_defaults_without_seed(app):
    with TestClient(app) as client:
        _, headers = _signup(client, email="empty-user@example.com")

        portfolio_response = client.get("/portfolio", headers=headers)
        assert portfolio_response.status_code == 200
        assert portfolio_response.json() == {
            "total_positions": 0,
            "total_market_value": 0,
            "total_cost_basis": 0,
            "total_unrealized_profit": 0,
            "items": [],
        }

        remove_response = client.post(
            "/portfolio/manual-remove",
            headers=headers,
            json={"item_id": "missing-card", "quantity": 1, "remove_all": False},
        )
        assert remove_response.status_code == 200
        assert remove_response.json()["items"] == []

        settings_response = client.get("/settings/engine-thresholds", headers=headers)
        assert settings_response.status_code == 200
        payload = settings_response.json()
        assert payload["updated_at"] is not None
        assert set(payload) == {
            "floor_buy_margin",
            "launch_supply_crash_threshold",
            "flip_profit_minimum",
            "grind_market_edge",
            "collection_lock_penalty",
            "gatekeeper_hold_weight",
            "updated_at",
        }


def test_show_sync_content_routes(client, app, monkeypatch):
    with app.state.session_factory() as session:
        session.add(
            ShowMetadataSnapshot(
                series_json=[{"series_id": 1, "name": "Live"}],
                brands_json=[{"brand_id": 5, "name": "Diamond Dynasty"}],
                sets_json=["CORE"],
                payload_json={"series": [{"series_id": 1, "name": "Live"}], "brands": [{"brand_id": 5, "name": "Diamond Dynasty"}], "sets": ["CORE"]},
                fetched_at=utcnow(),
            )
        )
        session.add(
            ShowRosterUpdate(
                remote_id="7",
                title="April Attribute Update",
                summary="Boosted contact vs RHP.",
                published_at=utcnow(),
                payload_json={"id": 7, "title": "April Attribute Update"},
                last_synced_at=utcnow(),
            )
        )
        session.commit()

    monkeypatch.setattr(
        app.state.show_sync_service.adapter,
        "search_player_profiles",
        lambda username: {
            "universal_profiles": [
                {
                    "username": username,
                    "display_level": "Gold 50",
                    "games_played": 123,
                    "vanity": {"nameplate_equipped": "plate", "icon_equipped": "icon"},
                    "most_played_modes": {"dd_time": "9999"},
                    "lifetime_hitting_stats": [{"HR": 5.2}],
                    "lifetime_defensive_stats": [{"ERA": 3.11}],
                    "online_data": [{"year": "2026", "wins": "17"}],
                }
            ]
        },
    )

    metadata_response = client.get("/metadata")
    player_search_response = client.get("/player-search", params={"username": "Scann"})
    roster_updates_response = client.get("/roster-updates")

    assert metadata_response.status_code == 200
    assert metadata_response.json()["series"][0]["name"] == "Live"

    assert player_search_response.status_code == 200
    payload = player_search_response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["username"] == "Scann"

    assert roster_updates_response.status_code == 200
    assert roster_updates_response.json()["items"][0]["remote_id"] == "7"


def test_market_filters_route(client):
    response = client.get('/market/flips', params={'min_profit': 5000, 'rarity': 'Diamond', 'sort_by': 'roi'})
    assert response.status_code == 200
    payload = response.json()
    for item in payload['items']:
        assert (item['profit_after_tax'] or 0) >= 5000
        assert item['rarity'] == 'Diamond'


def test_market_history_and_movers_routes(client, app):
    with app.state.session_factory() as session:
        session.add_all([
            PriceHistory(uuid='live-riley-greene-26', buy_price=4200, sell_price=5200, timestamp=utcnow() - timedelta(hours=23)),
            PriceHistory(uuid='live-riley-greene-26', buy_price=5100, sell_price=6200, timestamp=utcnow()),
            PriceHistory(uuid='live-ohtani-26', buy_price=160000, sell_price=190000, timestamp=utcnow() - timedelta(hours=23)),
            PriceHistory(uuid='live-ohtani-26', buy_price=150000, sell_price=175000, timestamp=utcnow()),
        ])
        session.commit()

    history_response = client.get('/market/history/live-riley-greene-26', params={'days': 1})
    trending_response = client.get('/market/trending')
    movers_response = client.get('/market/biggest-movers')

    assert history_response.status_code == 200
    assert len(history_response.json()['points']) >= 2

    assert trending_response.status_code == 200
    assert 'items' in trending_response.json()

    assert movers_response.status_code == 200
    assert 'items' in movers_response.json()


def test_inventory_routes(client):
    _, headers = _signup(client, email='inventory-user@example.com')

    unauthorized = client.get('/inventory/me')
    assert unauthorized.status_code == 401

    import_response = client.post(
        '/inventory/import',
        headers=headers,
        json={
            'replace_existing': True,
            'items': [
                {'item_uuid': 'live-riley-greene-26', 'quantity': 3, 'is_sellable': True},
                {'item_uuid': 'live-ohtani-26', 'quantity': 1, 'is_sellable': False},
            ],
        },
    )
    assert import_response.status_code == 200
    assert import_response.json()['imported_count'] == 2

    inventory_response = client.get('/inventory/me', headers=headers)
    assert inventory_response.status_code == 200
    payload = inventory_response.json()
    assert payload['count'] == 2
    assert payload['total_quantity'] == 4
    assert {item['item_uuid'] for item in payload['items']} == {'live-riley-greene-26', 'live-ohtani-26'}
