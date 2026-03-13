"""Mock adapters for isolated strategy and service tests."""

from __future__ import annotations

from datetime import date


class MockShowApiAdapter:
    def fetch_items(self, item_type=None, page_limit=None):
        return []

    def fetch_listings(self, item_type="mlb_card", page_limit=None):
        return []

    def fetch_listings_pages(self, item_type="mlb_card", page_limit=None):
        return [{"page": 1, "per_page": 0, "total_pages": 1, "listings": []}]

    def fetch_inventory(self, item_type=None):
        return []

    def fetch_metadata(self):
        return {}

    def search_player_profiles(self, username: str):
        return {"universal_profiles": []}

    def fetch_roster_updates_payload(self):
        return {"roster_updates": []}

    def fetch_roster_updates(self):
        return []


class MockMLBStatsAdapter:
    def search_people(self, name: str):
        return []

    def fetch_people_with_season_stats(self, person_ids, season_year: int, batch_size: int = 50):
        return []

    def fetch_probable_starters(self, game_date: date):
        return []

    def fetch_lineups(self, game_date: date):
        return []
