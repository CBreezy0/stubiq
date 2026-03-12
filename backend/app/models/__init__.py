"""ORM models for the Diamond Dynasty intelligence system."""

from __future__ import annotations

from app.database import Base
from .auth import AuthAuditLog, RefreshToken
from .connection import UserConnection
from .domain import (
    Card,
    LineupStatus,
    ListingsSnapshot,
    MarketHistoryAggregate,
    MarketPhaseHistory,
    PlayerStatsDaily,
    PlayerStatsRolling,
    PortfolioPosition,
    ProbableStarter,
    ProgramReward,
    RosterUpdateCalendar,
    RosterUpdatePrediction,
    StrategyRecommendation,
    SystemSetting,
    Transaction,
)
from .user import User, UserSettings


def load_all_models():
    """Import hook used by metadata initialization and Alembic."""
    return [
        User,
        UserSettings,
        RefreshToken,
        AuthAuditLog,
        UserConnection,
        Card,
        ListingsSnapshot,
        MarketHistoryAggregate,
        PlayerStatsDaily,
        PlayerStatsRolling,
        LineupStatus,
        ProbableStarter,
        RosterUpdateCalendar,
        PortfolioPosition,
        Transaction,
        ProgramReward,
        MarketPhaseHistory,
        RosterUpdatePrediction,
        StrategyRecommendation,
        SystemSetting,
    ]


__all__ = [
    "Base",
    "User",
    "UserSettings",
    "RefreshToken",
    "AuthAuditLog",
    "UserConnection",
    "Card",
    "ListingsSnapshot",
    "MarketHistoryAggregate",
    "PlayerStatsDaily",
    "PlayerStatsRolling",
    "LineupStatus",
    "ProbableStarter",
    "RosterUpdateCalendar",
    "PortfolioPosition",
    "Transaction",
    "ProgramReward",
    "MarketPhaseHistory",
    "RosterUpdatePrediction",
    "StrategyRecommendation",
    "SystemSetting",
    "load_all_models",
]
