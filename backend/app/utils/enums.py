"""Enum types shared across the application."""

from __future__ import annotations

from enum import Enum


class MarketPhase(str, Enum):
    EARLY_ACCESS = "EARLY_ACCESS"
    FULL_LAUNCH_SUPPLY_SHOCK = "FULL_LAUNCH_SUPPLY_SHOCK"
    STABILIZATION = "STABILIZATION"
    PRE_ATTRIBUTE_UPDATE = "PRE_ATTRIBUTE_UPDATE"
    POST_ATTRIBUTE_UPDATE = "POST_ATTRIBUTE_UPDATE"
    CONTENT_DROP = "CONTENT_DROP"
    STUB_SALE = "STUB_SALE"
    LATE_CYCLE = "LATE_CYCLE"


class RecommendationAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    FLIP = "FLIP"
    LOCK = "LOCK"
    GRIND = "GRIND"
    WATCH = "WATCH"
    AVOID = "AVOID"
    IGNORE = "IGNORE"


class RecommendationType(str, Enum):
    MARKET = "MARKET"
    COLLECTION = "COLLECTION"
    ROSTER_UPDATE = "ROSTER_UPDATE"
    PORTFOLIO = "PORTFOLIO"
    GRIND = "GRIND"
    ORCHESTRATED = "ORCHESTRATED"


class TransactionAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    LOCK = "LOCK"
    IMPORT = "IMPORT"
    REMOVE = "REMOVE"
    QUICKSELL = "QUICKSELL"


class UpdateType(str, Enum):
    ATTRIBUTE_UPDATE = "ATTRIBUTE_UPDATE"
    CONTENT_DROP = "CONTENT_DROP"
    ROSTER_REFRESH = "ROSTER_REFRESH"


class AuthProvider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    APPLE = "apple"


class ConnectionProvider(str, Enum):
    XBOX = "xbox"
    PLAYSTATION = "playstation"


class ConnectionStatus(str, Enum):
    NOT_CONNECTED = "not_connected"
    CONNECTED = "connected"
    EXPIRED = "expired"
    ERROR = "error"
    RECONNECT_REQUIRED = "reconnect_required"
