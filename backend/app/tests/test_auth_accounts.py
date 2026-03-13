from __future__ import annotations

from fastapi.testclient import TestClient

from app.models import AuthAuditLog
from app.services.apple_auth_service import AppleIdentity
from app.services.auth_service import GoogleIdentity



def _headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}



def _signup(client: TestClient, email: str, password: str = "Password123!", display_name: str = "Test User") -> dict:
    response = client.post(
        "/auth/signup",
        json={"email": email, "password": password, "display_name": display_name, "device_name": "iPhone", "platform": "ios"},
    )
    assert response.status_code == 201, response.text
    return response.json()



def test_auth_signup_options_preflight(client):
    response = client.options(
        "/auth/signup",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-methods"]
    assert response.headers["access-control-allow-origin"] in {"*", "http://localhost:3000"}


def test_auth_signup_options_without_preflight_headers(client):
    response = client.options("/auth/signup")
    assert response.status_code == 200


def test_signup(client):
    payload = _signup(client, "signup@example.com")
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["refresh_token"]
    assert payload["user"]["email"] == "signup@example.com"

    me = client.get("/auth/me", headers=_headers(payload["access_token"]))
    assert me.status_code == 200
    assert me.json()["id"] == payload["user"]["id"]



def test_login(client):
    _signup(client, "login@example.com", password="MyPassword123!")
    response = client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "MyPassword123!", "platform": "ios"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["email"] == "login@example.com"
    assert payload["access_token"]
    assert payload["refresh_token"]



def test_invalid_login(client):
    _signup(client, "invalid-login@example.com", password="CorrectPassword123!")
    response = client.post(
        "/auth/login",
        json={"email": "invalid-login@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."



def test_google_sign_in_create_user(client, app, monkeypatch):
    monkeypatch.setattr(
        app.state.auth_service.google_verifier,
        "verify",
        lambda raw_id_token: GoogleIdentity(
            sub="google-sub-1",
            email="google-create@example.com",
            display_name="Google Create",
            avatar_url="https://example.com/avatar.png",
            email_verified=True,
        ),
    )

    response = client.post(
        "/auth/google",
        json={"id_token": "test-google-token", "device_name": "iPhone", "platform": "ios"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["email"] == "google-create@example.com"
    assert payload["user"]["auth_provider"] == "google"
    assert payload["user"]["is_verified"] is True



def test_google_sign_in_existing_user(client, app, monkeypatch):
    signup_payload = _signup(client, "google-existing@example.com")
    monkeypatch.setattr(
        app.state.auth_service.google_verifier,
        "verify",
        lambda raw_id_token: GoogleIdentity(
            sub="google-sub-existing",
            email="google-existing@example.com",
            display_name="Google Existing",
            avatar_url=None,
            email_verified=True,
        ),
    )

    response = client.post("/auth/google", json={"id_token": "existing-google-token"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["id"] == signup_payload["user"]["id"]
    assert payload["user"]["auth_provider"] == "email"

    with app.state.session_factory() as session:
        user = app.state.user_service.get_user_by_id(session, signup_payload["user"]["id"])
        assert user is not None
        assert user.google_sub == "google-sub-existing"



def test_access_protected_route_without_token(client):
    response = client.get("/portfolio")
    assert response.status_code == 401



def test_portfolio_scoped_to_user(client):
    first = _signup(client, "portfolio-a@example.com")
    second = _signup(client, "portfolio-b@example.com")

    add_response = client.post(
        "/portfolio/manual-add",
        headers=_headers(first["access_token"]),
        json={
            "item_id": "scoped-card-1",
            "card_name": "Scoped Card",
            "quantity": 3,
            "avg_acquisition_cost": 2000,
            "locked_for_collection": False,
            "source": "manual",
        },
    )
    assert add_response.status_code == 200

    second_portfolio = client.get("/portfolio", headers=_headers(second["access_token"]))
    assert second_portfolio.status_code == 200
    assert second_portfolio.json()["items"] == []

    first_portfolio = client.get("/portfolio", headers=_headers(first["access_token"]))
    assert first_portfolio.status_code == 200
    assert [item["item_id"] for item in first_portfolio.json()["items"]] == ["scoped-card-1"]



def test_settings_scoped_to_user(client):
    first = _signup(client, "settings-a@example.com")
    second = _signup(client, "settings-b@example.com")

    patch_response = client.patch(
        "/settings/engine-thresholds",
        headers=_headers(first["access_token"]),
        json={"flip_profit_minimum": 7777, "floor_buy_margin": 0.15},
    )
    assert patch_response.status_code == 200

    first_settings = client.get("/settings/engine-thresholds", headers=_headers(first["access_token"]))
    second_settings = client.get("/settings/engine-thresholds", headers=_headers(second["access_token"]))
    assert first_settings.status_code == 200
    assert second_settings.status_code == 200
    assert first_settings.json()["flip_profit_minimum"] == 7777
    assert second_settings.json()["flip_profit_minimum"] != 7777
    assert second_settings.json()["floor_buy_margin"] != 0.15



def test_connection_create_read_delete(client):
    signup_payload = _signup(client, "connections@example.com")
    headers = _headers(signup_payload["access_token"])

    start_response = client.post("/connections/xbox/start", headers=headers)
    assert start_response.status_code == 200
    start_payload = start_response.json()
    assert start_payload["provider"] == "xbox"
    assert start_payload["mode"] == "mock"
    assert start_payload["session_token"]

    complete_response = client.post(
        "/connections/xbox/complete",
        headers=headers,
        json={
            "session_token": start_payload["session_token"],
            "provider_account_id": "xbox-account-123",
            "display_name": "Chris123",
            "gamertag_or_psn": "Chris123",
        },
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "connected"

    list_response = client.get("/connections", headers=headers)
    assert list_response.status_code == 200
    items = {item["provider"]: item for item in list_response.json()["items"]}
    assert items["xbox"]["status"] == "connected"
    assert items["playstation"]["status"] == "not_connected"

    delete_response = client.delete("/connections/xbox", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "not_connected"



def test_refresh_token_flow(client, app):
    signup_payload = _signup(client, "refresh@example.com")
    old_refresh_token = signup_payload["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh_token, "device_name": "iPhone", "platform": "ios"},
    )
    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert refreshed["refresh_token"] != old_refresh_token
    assert refreshed["access_token"] != signup_payload["access_token"]

    reused_old_token = client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
    assert reused_old_token.status_code == 401

    rotated_token_after_reuse = client.post("/auth/refresh", json={"refresh_token": refreshed["refresh_token"]})
    assert rotated_token_after_reuse.status_code == 401

    logout_response = client.post("/auth/logout", json={"refresh_token": refreshed["refresh_token"]})
    assert logout_response.status_code == 200
    assert logout_response.json()["success"] is True

    with app.state.session_factory() as session:
        reuse_events = session.query(AuthAuditLog).filter(AuthAuditLog.event_type == "refresh_token_reuse_detected").all()
        assert reuse_events



def test_apple_sign_in_create_user(client, app, monkeypatch):
    monkeypatch.setattr(
        app.state.auth_service.apple_verifier,
        "verify",
        lambda identity_token: AppleIdentity(
            sub="apple-sub-1",
            email="apple-create@example.com",
            email_verified=True,
            is_private_email=False,
        ),
    )

    response = client.post(
        "/auth/apple",
        json={
            "identity_token": "apple-identity-token",
            "authorization_code": "apple-auth-code",
            "device_name": "iPhone",
            "platform": "ios",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["email"] == "apple-create@example.com"
    assert payload["user"]["auth_provider"] == "apple"
    assert payload["user"]["is_verified"] is True



def test_apple_sign_in_existing_user(client, app, monkeypatch):
    signup_payload = _signup(client, "apple-existing@example.com")
    monkeypatch.setattr(
        app.state.auth_service.apple_verifier,
        "verify",
        lambda identity_token: AppleIdentity(
            sub="apple-sub-existing",
            email="apple-existing@example.com",
            email_verified=True,
            is_private_email=True,
        ),
    )

    response = client.post(
        "/auth/apple",
        json={"identity_token": "existing-apple-token", "authorization_code": "existing-auth-code"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["id"] == signup_payload["user"]["id"]
    assert payload["user"]["auth_provider"] == "email"

    with app.state.session_factory() as session:
        user = app.state.user_service.get_user_by_id(session, signup_payload["user"]["id"])
        assert user is not None
        assert user.apple_sub == "apple-sub-existing"



def test_connection_callback_persists_connected_state(client):
    signup_payload = _signup(client, "connection-callback@example.com")
    headers = _headers(signup_payload["access_token"])

    start_response = client.post("/connections/playstation/start", headers=headers)
    assert start_response.status_code == 200
    session_token = start_response.json()["session_token"]

    callback_response = client.post(
        "/connections/playstation/callback",
        headers=headers,
        json={
            "code": "provider-oauth-code",
            "session_token": session_token,
            "redirect_uri": "showintel://connections/playstation",
            "metadata_json": {"source": "ios"},
        },
    )
    assert callback_response.status_code == 200
    payload = callback_response.json()
    assert payload["provider"] == "playstation"
    assert payload["status"] == "connected"
    assert payload["metadata_json"]["mode"] == "mock"
    assert payload["metadata_json"]["source"] == "ios"



def test_revoke_sessions_revokes_all_refresh_tokens(client):
    signup_payload = _signup(client, "revoke@example.com")
    login_response = client.post(
        "/auth/login",
        json={"email": "revoke@example.com", "password": "Password123!", "device_name": "iPad", "platform": "ios"},
    )
    assert login_response.status_code == 200
    second_session = login_response.json()

    revoke_response = client.post("/auth/revoke-sessions", headers=_headers(signup_payload["access_token"]))
    assert revoke_response.status_code == 200
    assert revoke_response.json()["success"] is True
    assert revoke_response.json()["revoked_count"] >= 2

    first_refresh = client.post("/auth/refresh", json={"refresh_token": signup_payload["refresh_token"]})
    second_refresh = client.post("/auth/refresh", json={"refresh_token": second_session["refresh_token"]})
    assert first_refresh.status_code == 401
    assert second_refresh.status_code == 401
