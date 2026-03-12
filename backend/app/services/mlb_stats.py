"""Real MLB data adapter using the public MLB Stats API where available."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, List

from .base_http import BaseHttpAdapter


class MLBStatsAdapter(BaseHttpAdapter):
    """Adapter for season stats, probable starters, and related MLB signals."""

    def search_people(self, name: str) -> List[Dict[str, Any]]:
        payload = self.get_json("people/search", params={"names": name})
        return payload.get("people", [])

    def fetch_people_with_season_stats(self, person_ids: Iterable[int], season_year: int, batch_size: int = 50) -> List[Dict[str, Any]]:
        person_ids = list(person_ids)
        people: List[Dict[str, Any]] = []
        for index in range(0, len(person_ids), batch_size):
            batch = person_ids[index : index + batch_size]
            payload = self.get_json(
                "people",
                params={
                    "personIds": ",".join(str(person_id) for person_id in batch),
                    "hydrate": f"stats(group=[hitting,pitching],type=[season],season={season_year})",
                },
            )
            people.extend(payload.get("people", []))
        return people

    def fetch_probable_starters(self, game_date: date) -> List[Dict[str, Any]]:
        payload = self.get_json(
            "schedule",
            params={
                "sportId": 1,
                "date": game_date.isoformat(),
                "hydrate": "probablePitcher(note),team,linescore,flags",
            },
        )
        games = payload.get("dates", [])
        return games[0].get("games", []) if games else []

    def fetch_lineups(self, game_date: date) -> List[Dict[str, Any]]:
        payload = self.optional_get_json(
            ["schedule"],
            params={"sportId": 1, "date": game_date.isoformat(), "hydrate": "lineups"},
            default={},
        ) or {}
        games = payload.get("dates", [])
        return games[0].get("games", []) if games else []

    def fetch_injuries(self) -> List[Dict[str, Any]]:
        payload = self.optional_get_json(["injuries", "injury"], default={}) or {}
        return payload.get("injuries", payload if isinstance(payload, list) else [])

    def fetch_handedness_splits(self, person_ids: Iterable[int], season_year: int) -> Dict[int, Dict[str, Any]]:
        person_ids = list(person_ids)
        if not person_ids:
            return {}
        payload = self.optional_get_json(
            ["people"],
            params={
                "personIds": ",".join(str(person_id) for person_id in person_ids),
                "hydrate": f"stats(group=[hitting,pitching],type=[statSplits],season={season_year})",
            },
            default={},
        ) or {}
        return {person["id"]: person for person in payload.get("people", [])}
