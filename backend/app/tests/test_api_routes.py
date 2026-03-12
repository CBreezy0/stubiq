from __future__ import annotations

from fastapi.testclient import TestClient


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



def test_dashboard_summary_route(client):
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    payload = response.json()
    assert "market_phase" in payload
    assert "top_flips" in payload
    assert "collection_priorities" in payload



def test_market_endpoints(client):
    flips = client.get("/market/flips")
    floors = client.get("/market/floors")
    assert flips.status_code == 200
    assert floors.status_code == 200



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
