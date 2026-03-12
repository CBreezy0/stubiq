from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.services.seed import seed_dev_data


@pytest.fixture()
def test_settings(tmp_path):
    db_path = tmp_path / "test.db"
    settings = replace(
        get_settings(),
        database_url=f"sqlite:///{db_path}",
        testing=True,
        auto_create_schema=True,
        auto_seed_dev_data=False,
        scheduler_enabled=False,
        debug=False,
        dev_mode=True,
        enable_mock_console_connections=True,
        jwt_secret_key="test-jwt-secret-for-backend-auth-suite-32chars",
        jwt_refresh_secret_key="test-refresh-secret-for-backend-auth-suite-32chars",
    )
    return settings


@pytest.fixture()
def app(test_settings):
    return create_app(test_settings)


@pytest.fixture()
def client(app):
    with TestClient(app) as client:
        with app.state.session_factory() as session:
            seed_dev_data(session)
            session.commit()
        yield client


@pytest.fixture()
def session(app):
    with TestClient(app):
        with app.state.session_factory() as session:
            seed_dev_data(session)
            session.commit()
            yield session
