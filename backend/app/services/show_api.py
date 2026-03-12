"""MLB The Show API adapter with dynamic game-year base URLs."""

from __future__ import annotations

from typing import Any, Dict, List

from .base_http import BaseHttpAdapter


class ShowApiAdapter(BaseHttpAdapter):
    """Adapter for The Show marketplace endpoints."""

    def fetch_items(self) -> List[Dict[str, Any]]:
        return self._fetch_paginated_collection("items.json", "items")

    def fetch_listings(self) -> List[Dict[str, Any]]:
        return self._fetch_paginated_collection("listings.json", "listings")

    def fetch_inventory(self) -> List[Dict[str, Any]]:
        payload = self.optional_get_json(["inventory", "inventory.json"], default={}) or {}
        return payload.get("inventory", payload if isinstance(payload, list) else [])

    def fetch_metadata(self) -> Dict[str, Any]:
        return self.optional_get_json(["metadata.json", "metadata", "meta"], default={}) or {}

    def fetch_roster_updates(self) -> List[Dict[str, Any]]:
        payload = self.optional_get_json(["roster_updates", "roster_updates.json", "updates/roster"], default={}) or {}
        return payload.get("roster_updates", payload if isinstance(payload, list) else [])

    def _fetch_paginated_collection(self, path: str, key: str) -> List[Dict[str, Any]]:
        first_page = self.get_json(path, params={"page": 1})
        total_pages = int(first_page.get("total_pages", 1) or 1)
        results = list(first_page.get(key, []))
        for page in range(2, total_pages + 1):
            payload = self.get_json(path, params={"page": page})
            results.extend(payload.get(key, []))
        return results
