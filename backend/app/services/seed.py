"""Local development seed data."""

from __future__ import annotations

from datetime import timedelta
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Card,
    ListingsSnapshot,
    MarketHistoryAggregate,
    MarketPhaseHistory,
    PlayerStatsDaily,
    PlayerStatsRolling,
    PortfolioPosition,
    ProgramReward,
    RosterUpdateCalendar,
    User,
    UserSettings,
)
from app.security.passwords import hash_password
from app.utils.enums import AuthProvider, MarketPhase, UpdateType
from app.utils.time import utcnow


SEED_CARDS: List[Dict] = [
    {
        "item_id": "live-ohtani-26",
        "name": "Shohei Ohtani",
        "mlb_player_id": 660271,
        "series": "Live",
        "team": "Dodgers",
        "division": "NL West",
        "league": "NL",
        "overall": 92,
        "rarity": "Diamond",
        "display_position": "DH",
        "is_pitcher": False,
        "is_live_series": True,
        "quicksell_value": 10000,
        "is_sellable": True,
    },
    {
        "item_id": "live-judge-26",
        "name": "Aaron Judge",
        "mlb_player_id": 592450,
        "series": "Live",
        "team": "Yankees",
        "division": "AL East",
        "league": "AL",
        "overall": 91,
        "rarity": "Diamond",
        "display_position": "RF",
        "is_pitcher": False,
        "is_live_series": True,
        "quicksell_value": 10000,
        "is_sellable": True,
    },
    {
        "item_id": "live-riley-greene-26",
        "name": "Riley Greene",
        "mlb_player_id": 682985,
        "series": "Live",
        "team": "Tigers",
        "division": "AL Central",
        "league": "AL",
        "overall": 84,
        "rarity": "Gold",
        "display_position": "CF",
        "is_pitcher": False,
        "is_live_series": True,
        "quicksell_value": 400,
        "is_sellable": True,
    },
    {
        "item_id": "live-abbott-26",
        "name": "Andrew Abbott",
        "mlb_player_id": 671096,
        "series": "Live",
        "team": "Reds",
        "division": "NL Central",
        "league": "NL",
        "overall": 79,
        "rarity": "Silver",
        "display_position": "SP",
        "is_pitcher": True,
        "is_live_series": True,
        "quicksell_value": 100,
        "is_sellable": True,
    },
    {
        "item_id": "live-floor-bulk-26",
        "name": "Bulk Watch Hitter",
        "mlb_player_id": 999001,
        "series": "Live",
        "team": "Royals",
        "division": "AL Central",
        "league": "AL",
        "overall": 76,
        "rarity": "Silver",
        "display_position": "2B",
        "is_pitcher": False,
        "is_live_series": True,
        "quicksell_value": 100,
        "is_sellable": True,
    },
    {
        "item_id": "event-scarcity-26",
        "name": "Event Scarcity Bat",
        "series": "Event",
        "team": "Free Agents",
        "division": None,
        "league": None,
        "overall": 97,
        "rarity": "Diamond",
        "display_position": "SS",
        "is_pitcher": False,
        "is_live_series": False,
        "quicksell_value": 10000,
        "is_sellable": True,
    },
    {
        "item_id": "br-reward-26",
        "name": "BR Reward Arm",
        "series": "Battle Royale",
        "team": "Legends",
        "division": None,
        "league": None,
        "overall": 99,
        "rarity": "Diamond",
        "display_position": "CP",
        "is_pitcher": True,
        "is_live_series": False,
        "quicksell_value": 10000,
        "is_sellable": True,
    },
]


SEED_USER_EMAIL = "demo@example.com"
SEED_USER_PASSWORD = "Password123!"
SEED_USER_DISPLAY_NAME = "Demo Trader"


SEED_PROGRAM_REWARDS: List[Dict] = [
    {
        "program_name": "Team Affinity Launch",
        "mode_name": "Team Affinity Grind",
        "reward_type": "packs",
        "reward_item_id": None,
        "reward_stub_value_estimate": 14000,
        "source_json": {"estimated_hours": 2.5},
    },
    {
        "program_name": "WBC Mini Seasons",
        "mode_name": "WBC Mini Seasons",
        "reward_type": "packs",
        "reward_item_id": None,
        "reward_stub_value_estimate": 18000,
        "source_json": {"estimated_hours": 2.2},
    },
    {
        "program_name": "Conquest Launch Map",
        "mode_name": "Conquest",
        "reward_type": "packs",
        "reward_item_id": None,
        "reward_stub_value_estimate": 9000,
        "source_json": {"estimated_hours": 1.1},
    },
]


def _ensure_seed_user(session: Session) -> User:
    user = session.scalar(select(User).where(User.email == SEED_USER_EMAIL))
    if user is None:
        user = User(
            email=SEED_USER_EMAIL,
            display_name=SEED_USER_DISPLAY_NAME,
            auth_provider=AuthProvider.EMAIL,
            password_hash=hash_password(SEED_USER_PASSWORD),
            is_active=True,
            is_verified=True,
            last_login_at=utcnow(),
        )
        session.add(user)
        session.flush()
    settings_row = session.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    if settings_row is None:
        session.add(UserSettings(user_id=user.id))
        session.flush()
    return user


def seed_dev_data(session: Session) -> Dict[str, int]:
    seed_user = _ensure_seed_user(session)
    if session.scalar(select(Card.id).limit(1)) is not None:
        return {"seeded": 0}

    now = utcnow()
    for card_data in SEED_CARDS:
        session.add(Card(metadata_json=dict(card_data), **card_data))
    session.flush()

    snapshots = [
        ("live-ohtani-26", 160000, 190000, 24),
        ("live-judge-26", 145000, 172000, 24),
        ("live-riley-greene-26", 4200, 5200, 12),
        ("live-abbott-26", 260, 420, 10),
        ("live-floor-bulk-26", 105, 160, 8),
        ("event-scarcity-26", 78000, 92000, 15),
        ("br-reward-26", 115000, 138000, 16),
    ]
    for item_id, best_buy, best_sell, hours_back in snapshots:
        for offset in (hours_back, max(hours_back // 2, 1), 1):
            observed_at = now - timedelta(hours=offset)
            drift = (hours_back - offset) * 50
            session.add(
                ListingsSnapshot(
                    item_id=item_id,
                    buy_now=best_sell - drift,
                    sell_now=best_buy - drift,
                    best_buy_order=best_buy - drift,
                    best_sell_order=best_sell - drift,
                    spread=(best_sell - best_buy),
                    tax_adjusted_spread=int((best_sell - drift) * 0.9) - (best_buy - drift),
                    observed_at=observed_at,
                )
            )
    session.flush()

    aggregate_rows = [
        ("live-ohtani-26", 186000.0, 184000.0, 178000.0, 176000.0, 52.0, 78.0),
        ("live-judge-26", 170500.0, 168000.0, 164500.0, 160000.0, 48.0, 73.0),
        ("live-riley-greene-26", 5100.0, 5000.0, 4700.0, 4300.0, 45.0, 68.0),
        ("live-abbott-26", 410.0, 360.0, 320.0, 290.0, 37.0, 66.0),
        ("live-floor-bulk-26", 150.0, 145.0, 138.0, 130.0, 25.0, 60.0),
        ("event-scarcity-26", 90000.0, 88500.0, 86000.0, 81000.0, 60.0, 52.0),
    ]
    for row in aggregate_rows:
        session.add(
            MarketHistoryAggregate(
                item_id=row[0],
                phase=MarketPhase.STABILIZATION,
                avg_price_15m=row[1],
                avg_price_1h=row[2],
                avg_price_6h=row[3],
                avg_price_24h=row[4],
                volatility_score=row[5],
                liquidity_score=row[6],
            )
        )

    session.add_all(
        [
            PlayerStatsDaily(
                player_name="Riley Greene",
                mlb_player_id=682985,
                stat_date=now.date(),
                season_year=now.year,
                games=20,
                avg=0.301,
                obp=0.364,
                slg=0.602,
                ops=0.966,
                iso=0.301,
                hr=7,
                rbi=18,
                bb_rate=0.093,
                k_rate=0.221,
                era=None,
                whip=None,
                k_per_9=None,
                bb_per_9=None,
                saves=None,
                holds=None,
                innings=None,
                source_json={},
            ),
            PlayerStatsDaily(
                player_name="Andrew Abbott",
                mlb_player_id=671096,
                stat_date=now.date(),
                season_year=now.year,
                games=4,
                avg=None,
                obp=None,
                slg=None,
                ops=None,
                iso=None,
                hr=None,
                rbi=None,
                bb_rate=None,
                k_rate=0.30,
                era=2.18,
                whip=0.98,
                k_per_9=10.4,
                bb_per_9=2.1,
                saves=0,
                holds=0,
                innings=24.2,
                source_json={},
            ),
            PlayerStatsDaily(
                player_name="Shohei Ohtani",
                mlb_player_id=660271,
                stat_date=now.date(),
                season_year=now.year,
                games=22,
                avg=0.313,
                obp=0.402,
                slg=0.655,
                ops=1.057,
                iso=0.342,
                hr=8,
                rbi=19,
                bb_rate=0.114,
                k_rate=0.245,
                era=None,
                whip=None,
                k_per_9=None,
                bb_per_9=None,
                saves=None,
                holds=None,
                innings=None,
                source_json={},
            ),
        ]
    )
    session.add_all(
        [
            PlayerStatsRolling(mlb_player_id=682985, window_days=7, as_of_date=now.date(), avg=0.345, obp=0.412, slg=0.690, ops=1.102, iso=0.345, hr=4, bb_rate=0.10, k_rate=0.19, era=None, whip=None, k_per_9=None, bb_per_9=None, saves=None, holds=None, innings=None),
            PlayerStatsRolling(mlb_player_id=682985, window_days=15, as_of_date=now.date(), avg=0.322, obp=0.390, slg=0.650, ops=1.040, iso=0.328, hr=6, bb_rate=0.095, k_rate=0.21, era=None, whip=None, k_per_9=None, bb_per_9=None, saves=None, holds=None, innings=None),
            PlayerStatsRolling(mlb_player_id=671096, window_days=7, as_of_date=now.date(), avg=None, obp=None, slg=None, ops=None, iso=None, hr=None, bb_rate=0.06, k_rate=0.31, era=2.05, whip=0.94, k_per_9=10.8, bb_per_9=2.0, saves=0, holds=0, innings=18.0),
            PlayerStatsRolling(mlb_player_id=671096, window_days=15, as_of_date=now.date(), avg=None, obp=None, slg=None, ops=None, iso=None, hr=None, bb_rate=0.07, k_rate=0.29, era=2.48, whip=1.02, k_per_9=10.1, bb_per_9=2.4, saves=0, holds=0, innings=31.2),
        ]
    )

    session.add_all(
        [
            PortfolioPosition(
                user_id=seed_user.id,
                item_id="live-ohtani-26",
                card_name="Shohei Ohtani",
                quantity=1,
                avg_acquisition_cost=155000,
                current_market_value=190000,
                quicksell_value=10000,
                locked_for_collection=False,
                duplicate_count=0,
                source="seed",
            ),
            PortfolioPosition(
                user_id=seed_user.id,
                item_id="event-scarcity-26",
                card_name="Event Scarcity Bat",
                quantity=2,
                avg_acquisition_cost=62000,
                current_market_value=92000,
                quicksell_value=10000,
                locked_for_collection=False,
                duplicate_count=1,
                source="seed",
            ),
            PortfolioPosition(
                user_id=seed_user.id,
                item_id="live-riley-greene-26",
                card_name="Riley Greene",
                quantity=10,
                avg_acquisition_cost=3600,
                current_market_value=5200,
                quicksell_value=400,
                locked_for_collection=False,
                duplicate_count=9,
                source="seed",
            ),
        ]
    )

    for reward in SEED_PROGRAM_REWARDS:
        session.add(ProgramReward(**reward))

    session.add(MarketPhaseHistory(phase=MarketPhase.STABILIZATION, phase_start=now - timedelta(days=2), phase_end=None, notes="Seeded phase history"))
    session.add(
        RosterUpdateCalendar(
            update_type=UpdateType.ATTRIBUTE_UPDATE,
            update_date=now + timedelta(days=2),
            notes="Seeded update window for development and tests",
        )
    )
    return {"seeded": len(SEED_CARDS)}
