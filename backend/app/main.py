"""Application factory for the Diamond Dynasty market intelligence backend."""

from __future__ import annotations

import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect
from sqlalchemy.engine import make_url

from app.api.routes.auth import router as auth_router
from app.api.routes.cards import router as cards_router
from app.api.routes.collections import router as collections_router
from app.api.routes.connections import router as connections_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.grind import router as grind_router
from app.api.routes.health import router as health_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.investments import router as investments_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.market import router as market_router
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.settings import router as settings_router
from app.api.routes.show_data import router as show_data_router
from app.api.routes.users import router as users_router
from app.config import Settings, get_settings
from app.database import configure_database, create_session_factory, init_schema
from app.jobs import SchedulerManager
from app.services.db_health import check_database
from app.services.db_seed import seed_if_empty
from app.security.rate_limit import RateLimiter
from app.services import (
    AppleTokenVerifierService,
    AuthAuditService,
    AuthService,
    ConfigStore,
    ConnectionService,
    InventoryService,
    GoogleTokenVerifierService,
    MarketDataService,
    MLBDataService,
    PortfolioService,
    RecommendationService,
    ShowApiAdapter,
    ShowSyncService,
    MLBStatsAdapter,
    TokenService,
    UserService,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def _safe_database_url(database_url: str) -> str:
    try:
        return make_url(database_url).render_as_string(hide_password=True)
    except Exception:
        return database_url



def create_app(settings: Optional[Settings] = None) -> FastAPI:
    settings = settings or get_settings()
    logger.info("Connecting to PostgreSQL database: %s", _safe_database_url(settings.database_url))
    engine = configure_database(settings.database_url, echo=settings.debug)
    session_factory = create_session_factory(engine)
    show_adapter = ShowApiAdapter(settings.show_api_base_url, timeout_seconds=settings.request_timeout_seconds)
    mlb_adapter = MLBStatsAdapter(settings.mlb_stats_api_base_url, timeout_seconds=settings.request_timeout_seconds)
    config_store = ConfigStore()
    auth_audit_service = AuthAuditService()
    token_service = TokenService(settings, auth_audit_service)
    user_service = UserService(settings)
    auth_service = AuthService(
        user_service,
        token_service,
        GoogleTokenVerifierService(settings.google_client_id),
        AppleTokenVerifierService(settings.apple_client_id),
        auth_audit_service,
    )
    connection_service = ConnectionService(settings, token_service)
    auth_rate_limiter = RateLimiter()
    market_data_service = MarketDataService(settings, show_adapter)
    show_sync_service = ShowSyncService(settings, show_adapter, market_data_service)
    portfolio_service = PortfolioService(market_data_service)
    inventory_service = InventoryService(market_data_service)
    mlb_data_service = MLBDataService(settings, mlb_adapter)
    recommendation_service = RecommendationService(settings, config_store, market_data_service, portfolio_service, user_service)
    scheduler_manager = SchedulerManager(settings, session_factory, market_data_service, mlb_data_service, recommendation_service)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        check_database(engine)
        if "neon.tech" in settings.database_url:
            logger.info("Connected to Neon PostgreSQL successfully.")
        else:
            logger.info("Connected to database successfully.")

        if settings.auto_create_schema:
            init_schema(engine)

        table_count = len(inspect(engine).get_table_names())
        logger.info("Detected %d tables in database.", table_count)

        if settings.auto_seed_dev_data:
            with session_factory() as session:
                if seed_if_empty(session):
                    session.commit()
        if settings.scheduler_enabled and not settings.testing:
            scheduler_manager.start()
        try:
            yield
        finally:
            scheduler_manager.shutdown()

    app = FastAPI(
        title=settings.app_name,
        description="Production-grade MLB The Show Diamond Dynasty market intelligence backend.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info('CORS enabled for origins: %s', ', '.join(settings.cors_allow_origins))
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.config_store = config_store
    app.state.auth_audit_service = auth_audit_service
    app.state.token_service = token_service
    app.state.user_service = user_service
    app.state.auth_service = auth_service
    app.state.connection_service = connection_service
    app.state.auth_rate_limiter = auth_rate_limiter
    app.state.market_data_service = market_data_service
    app.state.show_sync_service = show_sync_service
    app.state.portfolio_service = portfolio_service
    app.state.inventory_service = inventory_service
    app.state.mlb_data_service = mlb_data_service
    app.state.recommendation_service = recommendation_service
    app.state.scheduler_manager = scheduler_manager

    @app.get("/")
    def root():
        return {
            "message": settings.app_name,
            "game_year": settings.game_year,
            "show_api_base_url": settings.show_api_base_url,
            "scheduler_enabled": settings.scheduler_enabled,
        }

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(connections_router)
    app.include_router(health_router)
    app.include_router(dashboard_router)
    app.include_router(market_router)
    app.include_router(investments_router)
    app.include_router(collections_router)
    app.include_router(portfolio_router)
    app.include_router(inventory_router)
    app.include_router(grind_router)
    app.include_router(cards_router)
    app.include_router(settings_router)
    app.include_router(show_data_router)
    app.include_router(jobs_router)
    return app


app = create_app()
