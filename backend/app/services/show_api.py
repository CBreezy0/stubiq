"""MLB The Show API adapter with dynamic game-year base URLs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base_http import BaseHttpAdapter


class ShowApiAdapter(BaseHttpAdapter):
    """Adapter for The Show marketplace endpoints."""

    def fetch_items(self, item_type: Optional[str] = None, page_limit: Optional[int] = None) -> List[Dict[str, Any]]:
        return self._fetch_paginated_collection(
            "items.json",
            "items",
            base_params=self._type_params(item_type),
            page_limit=page_limit,
        )

    def fetch_listings(self, item_type: Optional[str] = "mlb_card", page_limit: Optional[int] = None) -> List[Dict[str, Any]]:
        return self._fetch_paginated_collection(
            "listings.json",
            "listings",
            base_params=self._type_params(item_type),
            page_limit=page_limit,
        )

    def fetch_listings_pages(self, item_type: Optional[str] = "mlb_card", page_limit: Optional[int] = None) -> List[Dict[str, Any]]:
        return self._fetch_paginated_pages(
            "listings.json",
            base_params=self._type_params(item_type),
            page_limit=page_limit,
        )

    def fetch_inventory(self, item_type: Optional[str] = None) -> List[Dict[str, Any]]:
        payload = self.optional_get_json(
            ["inventory", "inventory.json"],
            params=self._type_params(item_type),
            default={},
        ) or {}
        return payload.get("inventory", payload if isinstance(payload, list) else [])

    def fetch_metadata(self) -> Dict[str, Any]:
        return self.optional_get_json(["meta_data.json", "metadata.json", "metadata", "meta"], default={}) or {}

    def search_player_profiles(self, username: str) -> Dict[str, Any]:
        return self.get_json("player_search.json", params={"username": username})

    def fetch_roster_updates_payload(self) -> Dict[str, Any]:
        payload = self.optional_get_json(["roster_updates.json", "roster_updates", "updates/roster"], default={}) or {}
        return payload if isinstance(payload, dict) else {"roster_updates": payload}

    def fetch_roster_updates(self) -> List[Dict[str, Any]]:
        payload = self.fetch_roster_updates_payload()
        return payload.get("roster_updates", payload if isinstance(payload, list) else [])

    def fetch_roster_update(self, update_id: int | str) -> Any:
        return self.optional_get_json(["roster_update.json", "roster_update"], params={"id": update_id}, default=None)

    def _fetch_paginated_collection(
        self,
        path: str,
        key: str,
        base_params: Optional[Dict[str, Any]] = None,
        page_limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for page_payload in self._fetch_paginated_pages(path, base_params=base_params, page_limit=page_limit):
            results.extend(page_payload.get(key, []))
        return results

    def _fetch_paginated_pages(
        self,
        path: str,
        base_params: Optional[Dict[str, Any]] = None,
        page_limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        first_page = self.get_json(path, params=self._page_params(base_params, 1))
        total_pages = int(first_page.get("total_pages", 1) or 1)
        if page_limit is not None:
            total_pages = min(total_pages, page_limit)
        pages = [first_page]
        for page in range(2, total_pages + 1):
            pages.append(self.get_json(path, params=self._page_params(base_params, page)))
        return pages

    def _page_params(self, base_params: Optional[Dict[str, Any]], page: int) -> Dict[str, Any]:
        params = dict(base_params or {})
        params["page"] = page
        return params

    def _type_params(self, item_type: Optional[str]) -> Optional[Dict[str, Any]]:
        if not item_type:
            return None
        return {"type": item_type}
