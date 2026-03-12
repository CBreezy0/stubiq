"""HTTP client helpers with retries."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BaseHttpAdapter:
    """Shared resilient HTTP adapter for remote API integrations."""

    def __init__(self, base_url: str, timeout_seconds: int = 20):
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.4,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({"User-Agent": "mlb-show-market-intelligence/1.0"})
        return session

    def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        response = self.session.get(urljoin(self.base_url, path.lstrip("/")), params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def optional_get_json(self, paths: Iterable[str], params: Optional[Dict[str, Any]] = None, default=None) -> Any:
        for path in paths:
            try:
                return self.get_json(path, params=params)
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 404:
                    continue
                raise
            except ValueError:
                continue
        return default
