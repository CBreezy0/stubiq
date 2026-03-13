from __future__ import annotations

from sqlalchemy import select

from app.models import Card, ListingsSnapshot, MarketListing, ShowMetadataSnapshot, ShowPlayerProfile, ShowRosterUpdate
from app.services.market_data import MarketDataService
from app.services.show_sync import ShowSyncService


class StubShowApiAdapter:
    def fetch_listings_pages(self, item_type: str = "mlb_card", page_limit=None):
        return [
            {
                "page": 1,
                "per_page": 25,
                "total_pages": 1,
                "listings": [
                    {
                        "listing_name": "Test Player",
                        "best_sell_price": 1400,
                        "best_buy_price": 1000,
                        "item": {
                            "uuid": "test-card-1",
                            "type": "mlb_card",
                            "name": "Test Player",
                            "rarity": "Gold",
                            "team": "Yankees",
                            "team_short_name": "NYY",
                            "ovr": 84,
                            "series": "Live",
                            "series_year": 2026,
                            "display_position": "RF",
                            "set_name": "CORE",
                        },
                    }
                ],
            }
        ]

    def fetch_metadata(self):
        return {
            "series": [{"series_id": 1, "name": "Live"}],
            "brands": [{"brand_id": 5, "name": "Diamond Dynasty"}],
            "sets": ["CORE"],
        }

    def search_player_profiles(self, username: str):
        return {
            "universal_profiles": [
                {
                    "username": username,
                    "display_level": "Gold 50",
                    "games_played": 123,
                    "vanity": {"nameplate_equipped": "plate", "icon_equipped": "icon"},
                    "most_played_modes": {"dd_time": "9999", "rtts_time": "10"},
                    "lifetime_hitting_stats": [{"HR": 5.2}, {"Avg": 0.301}],
                    "lifetime_defensive_stats": [{"K": 9.4}, {"ERA": 3.11}],
                    "online_data": [{"year": "2026", "wins": "17"}],
                }
            ]
        }

    def fetch_roster_updates_payload(self):
        return {
            "roster_updates": [
                {
                    "id": 7,
                    "title": "April Attribute Update",
                    "summary": "Boosted contact vs RHP for breakout hitters.",
                    "published_at": "2026-04-10T15:00:00Z",
                }
            ]
        }


class EmptyRosterAdapter(StubShowApiAdapter):
    def fetch_roster_updates_payload(self):
        return {"roster_updates": []}


def _service(app):
    settings = app.state.settings
    adapter = StubShowApiAdapter()
    market_data_service = MarketDataService(settings, adapter)
    return ShowSyncService(settings, adapter, market_data_service)


def test_sync_listings_persists_current_listing_and_snapshot(app, session):
    service = _service(app)

    result = service.sync_listings(session)
    session.commit()

    assert result == {"pages": 1, "listings": 1}

    card = session.scalar(select(Card).where(Card.item_id == "test-card-1"))
    assert card is not None
    assert card.name == "Test Player"
    assert card.is_live_series is True

    current_listing = session.scalar(select(MarketListing).where(MarketListing.item_id == "test-card-1"))
    assert current_listing is not None
    assert current_listing.best_buy_price == 1000
    assert current_listing.best_sell_price == 1400
    assert current_listing.spread == 400
    assert current_listing.estimated_profit == 260
    assert current_listing.roi_percent == 26.0

    snapshot = session.scalar(select(ListingsSnapshot).where(ListingsSnapshot.item_id == "test-card-1"))
    assert snapshot is not None
    assert snapshot.tax_adjusted_spread == 260


def test_sync_metadata_persists_snapshot(app, session):
    service = _service(app)

    snapshot = service.sync_metadata(session)
    session.commit()

    loaded = session.scalar(select(ShowMetadataSnapshot).where(ShowMetadataSnapshot.id == snapshot.id))
    assert loaded is not None
    assert loaded.series_json[0]["name"] == "Live"
    assert loaded.brands_json[0]["name"] == "Diamond Dynasty"
    assert loaded.sets_json == ["CORE"]


def test_search_player_profiles_caches_results(app, session):
    service = _service(app)

    profiles = service.search_player_profiles(session, "Scann")
    session.commit()

    assert len(profiles) == 1
    cached = session.scalar(select(ShowPlayerProfile).where(ShowPlayerProfile.username == "Scann"))
    assert cached is not None
    assert cached.display_level == "Gold 50"
    assert cached.games_played == 123
    assert cached.online_data_json[0]["year"] == "2026"


def test_sync_roster_updates_persists_entries(app, session):
    service = _service(app)

    result = service.sync_roster_updates(session)
    session.commit()

    assert result == {"updates": 1}
    record = session.scalar(select(ShowRosterUpdate).where(ShowRosterUpdate.remote_id == "7"))
    assert record is not None
    assert record.title == "April Attribute Update"
    assert record.summary == "Boosted contact vs RHP for breakout hitters."


def test_sync_roster_updates_handles_empty_payload(app, session):
    settings = app.state.settings
    adapter = EmptyRosterAdapter()
    service = ShowSyncService(settings, adapter, MarketDataService(settings, adapter))

    result = service.sync_roster_updates(session)
    session.commit()

    assert result == {"updates": 0}
    assert session.scalars(select(ShowRosterUpdate)).all() == []


def test_compute_listing_metrics(app):
    service = _service(app)

    metrics = service.compute_listing_metrics(1500, 2000)

    assert metrics == {
        "spread": 500,
        "estimated_profit": 300,
        "roi_percent": 20.0,
    }
