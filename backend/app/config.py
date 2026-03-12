"""Application configuration and feature flags."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import lru_cache
import getpass
import json
import os
from typing import Any, Dict, Optional, Tuple

from .utils.enums import MarketPhase


DEFAULT_STRATEGY_WEIGHTS: Dict[str, float] = {
    "stub_growth_score": 0.30,
    "collection_progress_score": 0.25,
    "downside_protection_score": 0.20,
    "liquidity_score": 0.15,
    "lineup_utility_score": 0.10,
}

DEFAULT_ENGINE_THRESHOLDS: Dict[str, float] = {
    "floor_buy_buffer": 0.08,
    "strong_fill_velocity": 70.0,
    "high_liquidity": 65.0,
    "high_gatekeeper_price": 90000.0,
    "division_completion_boost_pct": 0.70,
    "reasonable_division_cost": 175000.0,
    "pre_update_hours": 48.0,
    "post_update_hours": 24.0,
    "content_drop_drop_pct": 0.12,
    "launch_shock_drop_pct": 0.18,
    "low_risk_profit_min": 250.0,
    "bulk_watch_price_cap": 800.0,
    "watch_84_price_cap": 5500.0,
    "portfolio_concentration_pct": 0.25,
    "full_launch_supply_shock_days": 3.0,
    "late_cycle_days": 210.0,
    "early_access_reference_markup_cap_pct": 0.18,
    "early_access_watch_floor_score_min": 82.0,
    "early_access_buy_floor_score_min": 96.0,
    "full_launch_floor_score_min": 72.0,
    "trend_compression_score_min": 58.0,
    "launch_window_hours": 48.0,
    "launch_grind_ev_edge_pct": 0.05,
    "floor_endpoint_score_min": 70.0,
    "collection_team_reward_value": 15000.0,
    "collection_division_reward_value": 45000.0,
    "collection_gatekeeper_value_divisor": 3000.0,
    "collection_reward_value_divisor": 2500.0,
    "collection_remaining_cost_penalty_rate": 0.0002,
    "collection_completion_score_weight": 45.0,
    "collection_early_access_penalty": 15.0,
    "collection_close_completion_bonus": 12.0,
    "collection_low_remaining_cost_bonus": 8.0,
    "collection_owned_gatekeeper_priority_bonus": 10.0,
}

DEFAULT_QUICKSELL_TIERS: Dict[str, int] = {
    "0-64": 5,
    "65-74": 25,
    "75-79": 100,
    "80-84": 400,
    "85-89": 3000,
    "90-99": 10000,
}

LAUNCH_DATE_DEFAULTS: Dict[int, Tuple[date, date]] = {
    25: (date(2025, 3, 14), date(2025, 3, 18)),
    26: (date(2026, 3, 13), date(2026, 3, 17)),
}


@dataclass(frozen=True)
class FeatureFlags:
    red_diamond_enabled: bool
    wbc_content_enabled: bool
    pxp2_enabled: bool
    mini_seasons_9_inning_enabled: bool
    launch_phase_logic_enabled: bool


@dataclass(frozen=True)
class Settings:
    app_name: str
    environment: str
    debug: bool
    dev_mode: bool
    testing: bool
    auto_create_schema: bool
    auto_seed_dev_data: bool
    scheduler_enabled: bool
    database_url: str
    game_year: int
    show_api_base_url: str
    mlb_stats_api_base_url: str
    market_phase_override: Optional[MarketPhase]
    request_timeout_seconds: int
    market_tax_rate: float
    market_snapshot_interval_minutes: int
    strategy_refresh_interval_minutes: int
    lineup_refresh_interval_minutes: int
    probable_starters_refresh_interval_minutes: int
    daily_stats_refresh_hour_utc: int
    default_page_size: int
    max_page_size: int
    early_access_start_date: date
    full_launch_start_date: date
    stabilization_days_after_launch: int
    strategy_weights: Dict[str, float]
    engine_thresholds: Dict[str, float]
    quicksell_tiers: Dict[str, int]
    jwt_secret_key: str
    jwt_refresh_secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    google_client_id: Optional[str]
    google_client_secret: Optional[str]
    apple_client_id: Optional[str]
    xbox_client_id: Optional[str]
    xbox_client_secret: Optional[str]
    playstation_client_id: Optional[str]
    playstation_client_secret: Optional[str]
    enable_mock_console_connections: bool
    auth_rate_limit_max_requests: int
    auth_rate_limit_window_seconds: int
    feature_flags: FeatureFlags



def _get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}



def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)



def _get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)



def _get_json_env(name: str, default: Dict[str, Any]) -> Dict[str, Any]:
    value = os.getenv(name)
    if value is None:
        return dict(default)
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError(f"{name} must decode to an object")
    merged = dict(default)
    merged.update(parsed)
    return merged



def _default_launch_dates(game_year: int) -> Tuple[date, date]:
    if game_year in LAUNCH_DATE_DEFAULTS:
        return LAUNCH_DATE_DEFAULTS[game_year]
    fallback = date(date.today().year, 3, 15)
    return fallback, fallback



def _get_date_env(name: str, default: date) -> date:
    value = os.getenv(name)
    if value is None:
        return default
    return date.fromisoformat(value)



def _default_database_url() -> str:
    default_user = getpass.getuser()
    return f"postgresql://{default_user}@localhost/mlbshow"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    game_year = _get_int_env("GAME_YEAR", 26)
    default_early_access, default_full_launch = _default_launch_dates(game_year)
    show_api_base_url = os.getenv("SHOW_API_BASE_URL", "https://mlb25.theshow.com/apis")
    market_phase_override = os.getenv("MARKET_PHASE_OVERRIDE")

    return Settings(
        app_name=os.getenv("APP_NAME", "MLB The Show Diamond Dynasty Intelligence API"),
        environment=os.getenv("ENVIRONMENT", "development"),
        debug=_get_bool_env("DEBUG", False),
        dev_mode=_get_bool_env("DEV_MODE", True),
        testing=_get_bool_env("TESTING", False),
        auto_create_schema=_get_bool_env("AUTO_CREATE_SCHEMA", True),
        auto_seed_dev_data=_get_bool_env("AUTO_SEED_DEV_DATA", False),
        scheduler_enabled=_get_bool_env("SCHEDULER_ENABLED", True),
        database_url=os.getenv("DATABASE_URL", _default_database_url()),
        game_year=game_year,
        show_api_base_url=show_api_base_url,
        mlb_stats_api_base_url=os.getenv("MLB_STATS_API_BASE_URL", "https://statsapi.mlb.com/api/v1"),
        market_phase_override=MarketPhase(market_phase_override) if market_phase_override else None,
        request_timeout_seconds=_get_int_env("REQUEST_TIMEOUT_SECONDS", 20),
        market_tax_rate=_get_float_env("MARKET_TAX_RATE", 0.10),
        market_snapshot_interval_minutes=_get_int_env("MARKET_SNAPSHOT_INTERVAL_MINUTES", 10),
        strategy_refresh_interval_minutes=_get_int_env("STRATEGY_REFRESH_INTERVAL_MINUTES", 60),
        lineup_refresh_interval_minutes=_get_int_env("LINEUP_REFRESH_INTERVAL_MINUTES", 60),
        probable_starters_refresh_interval_minutes=_get_int_env(
            "PROBABLE_STARTERS_REFRESH_INTERVAL_MINUTES",
            180,
        ),
        daily_stats_refresh_hour_utc=_get_int_env("DAILY_STATS_REFRESH_HOUR_UTC", 10),
        default_page_size=_get_int_env("DEFAULT_PAGE_SIZE", 25),
        max_page_size=_get_int_env("MAX_PAGE_SIZE", 200),
        early_access_start_date=_get_date_env("EARLY_ACCESS_START_DATE", default_early_access),
        full_launch_start_date=_get_date_env("FULL_LAUNCH_START_DATE", default_full_launch),
        stabilization_days_after_launch=_get_int_env("STABILIZATION_DAYS_AFTER_LAUNCH", 7),
        strategy_weights=_get_json_env("STRATEGY_WEIGHTS_JSON", DEFAULT_STRATEGY_WEIGHTS),
        engine_thresholds=_get_json_env("ENGINE_THRESHOLDS_JSON", DEFAULT_ENGINE_THRESHOLDS),
        quicksell_tiers=_get_json_env("QUICKSELL_TIERS_JSON", DEFAULT_QUICKSELL_TIERS),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me"),
        jwt_refresh_secret_key=os.getenv("JWT_REFRESH_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")),
        access_token_expire_minutes=_get_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 30),
        refresh_token_expire_days=_get_int_env("REFRESH_TOKEN_EXPIRE_DAYS", 30),
        google_client_id=os.getenv("GOOGLE_CLIENT_ID"),
        google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        apple_client_id=os.getenv("APPLE_CLIENT_ID"),
        xbox_client_id=os.getenv("XBOX_CLIENT_ID"),
        xbox_client_secret=os.getenv("XBOX_CLIENT_SECRET"),
        playstation_client_id=os.getenv("PLAYSTATION_CLIENT_ID"),
        playstation_client_secret=os.getenv("PLAYSTATION_CLIENT_SECRET"),
        enable_mock_console_connections=_get_bool_env("ENABLE_MOCK_CONSOLE_CONNECTIONS", True),
        auth_rate_limit_max_requests=_get_int_env("AUTH_RATE_LIMIT_MAX_REQUESTS", 10),
        auth_rate_limit_window_seconds=_get_int_env("AUTH_RATE_LIMIT_WINDOW_SECONDS", 60),
        feature_flags=FeatureFlags(
            red_diamond_enabled=_get_bool_env("RED_DIAMOND_ENABLED", True),
            wbc_content_enabled=_get_bool_env("WBC_CONTENT_ENABLED", True),
            pxp2_enabled=_get_bool_env("PXP2_ENABLED", True),
            mini_seasons_9_inning_enabled=_get_bool_env("MINI_SEASONS_9_INNING_ENABLED", True),
            launch_phase_logic_enabled=_get_bool_env("LAUNCH_PHASE_LOGIC_ENABLED", True),
        ),
    )
