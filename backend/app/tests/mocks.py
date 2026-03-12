"""Mock adapters for isolated strategy and service tests."""

from __future__ import annotations

from datetime import date


class MockShowApiAdapter:
    def fetch_items(self):
        return []

    def fetch_listings(self):
        return []

    def fetch_inventory(self):
        return []

    def fetch_metadata(self):
        return {}

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
