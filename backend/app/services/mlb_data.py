"""MLB stats syncing and rolling-stat computations."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional

from sqlalchemy import and_, delete, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Card, LineupStatus, PlayerStatsDaily, PlayerStatsRolling, ProbableStarter
from app.services.mlb_stats import MLBStatsAdapter
from app.utils.scoring import safe_float, safe_int
from app.utils.time import utcnow


class MLBDataService:
    """Keeps player season stats, rolling windows, probable starters, and lineups current."""

    def __init__(self, settings: Settings, adapter: MLBStatsAdapter):
        self.settings = settings
        self.adapter = adapter

    def sync_player_stats(self, session: Session, stat_date: Optional[date] = None) -> int:
        stat_date = stat_date or utcnow().date()
        season_year = stat_date.year if stat_date.month >= 3 else stat_date.year - 1
        cards = session.scalars(select(Card).where(Card.is_live_series.is_(True))).all()
        player_ids = []
        for card in cards:
            if card.mlb_player_id:
                player_ids.append(card.mlb_player_id)
            else:
                person = self._resolve_player(card)
                if person and person.get("id"):
                    card.mlb_player_id = int(person["id"])
                    session.add(card)
                    player_ids.append(card.mlb_player_id)
        player_ids = sorted(set(player_ids))
        if not player_ids:
            return 0
        people = self.adapter.fetch_people_with_season_stats(player_ids, season_year)
        upserted = 0
        for person in people:
            row = self._build_daily_row(person, stat_date, season_year)
            if row is None:
                continue
            existing = session.scalar(
                select(PlayerStatsDaily)
                .where(PlayerStatsDaily.mlb_player_id == row.mlb_player_id)
                .where(PlayerStatsDaily.stat_date == stat_date)
            )
            if existing is None:
                existing = PlayerStatsDaily(mlb_player_id=row.mlb_player_id, stat_date=stat_date, player_name=row.player_name, season_year=season_year)
            for field_name in (
                "player_name",
                "season_year",
                "games",
                "avg",
                "obp",
                "slg",
                "ops",
                "iso",
                "hr",
                "rbi",
                "bb_rate",
                "k_rate",
                "era",
                "whip",
                "k_per_9",
                "bb_per_9",
                "saves",
                "holds",
                "innings",
                "source_json",
            ):
                setattr(existing, field_name, getattr(row, field_name))
            session.add(existing)
            upserted += 1
        self.recompute_rolling_windows(session, stat_date)
        return upserted

    def recompute_rolling_windows(self, session: Session, as_of_date: date, windows=(7, 15, 30)) -> int:
        rows = session.scalars(
            select(PlayerStatsDaily)
            .where(PlayerStatsDaily.stat_date <= as_of_date)
            .order_by(PlayerStatsDaily.mlb_player_id.asc(), PlayerStatsDaily.stat_date.desc())
        ).all()
        grouped: Dict[int, List[PlayerStatsDaily]] = defaultdict(list)
        for row in rows:
            grouped[row.mlb_player_id].append(row)

        recomputed = 0
        for player_id, player_rows in grouped.items():
            for window in windows:
                sample = [row for row in player_rows if (as_of_date - row.stat_date).days < window][:window]
                if not sample:
                    continue
                existing = session.scalar(
                    select(PlayerStatsRolling)
                    .where(PlayerStatsRolling.mlb_player_id == player_id)
                    .where(PlayerStatsRolling.window_days == window)
                    .where(PlayerStatsRolling.as_of_date == as_of_date)
                )
                if existing is None:
                    existing = PlayerStatsRolling(mlb_player_id=player_id, window_days=window, as_of_date=as_of_date)
                existing.avg = self._avg(sample, "avg")
                existing.obp = self._avg(sample, "obp")
                existing.slg = self._avg(sample, "slg")
                existing.ops = self._avg(sample, "ops")
                existing.iso = self._avg(sample, "iso")
                existing.hr = int(sum(row.hr or 0 for row in sample))
                existing.bb_rate = self._avg(sample, "bb_rate")
                existing.k_rate = self._avg(sample, "k_rate")
                existing.era = self._avg(sample, "era")
                existing.whip = self._avg(sample, "whip")
                existing.k_per_9 = self._avg(sample, "k_per_9")
                existing.bb_per_9 = self._avg(sample, "bb_per_9")
                existing.saves = int(sum(row.saves or 0 for row in sample))
                existing.holds = int(sum(row.holds or 0 for row in sample))
                existing.innings = round(sum(row.innings or 0 for row in sample), 2)
                session.add(existing)
                recomputed += 1
        return recomputed

    def sync_game_day_context(self, session: Session, game_date: Optional[date] = None) -> Dict[str, int]:
        game_date = game_date or utcnow().date()
        probable_games = self.adapter.fetch_probable_starters(game_date)
        lineup_games = self.adapter.fetch_lineups(game_date)

        session.execute(delete(ProbableStarter).where(ProbableStarter.game_date == game_date))
        session.execute(delete(LineupStatus).where(LineupStatus.game_date == game_date))

        starters = 0
        for game in probable_games:
            starters += self._persist_probable_pitchers(session, game_date, game)

        lineups = 0
        for game in lineup_games:
            lineups += self._persist_lineups(session, game_date, game)

        return {"probable_starters": starters, "lineups": lineups}

    def _resolve_player(self, card: Card) -> Optional[Dict]:
        people = self.adapter.search_people(card.name)
        if not people:
            return None
        if card.team:
            for person in people:
                current_team = (person.get("currentTeam") or {}).get("name")
                if current_team and card.team.lower() in current_team.lower():
                    return person
        return people[0]

    def _build_daily_row(self, person: Dict, stat_date: date, season_year: int) -> Optional[PlayerStatsDaily]:
        player_id = person.get("id")
        if not player_id:
            return None
        hitting_stats, pitching_stats = self._extract_stats(person)
        plate_appearances = safe_float(hitting_stats.get("plateAppearances")) or 0.0
        innings = self._innings_to_float(pitching_stats.get("inningsPitched"))
        bb_rate = (safe_float(hitting_stats.get("baseOnBalls")) or 0.0) / plate_appearances if plate_appearances else None
        k_rate = (safe_float(hitting_stats.get("strikeOuts")) or 0.0) / plate_appearances if plate_appearances else None
        pitcher_walks = safe_float(pitching_stats.get("baseOnBalls")) or 0.0
        pitcher_ks = safe_float(pitching_stats.get("strikeOuts")) or 0.0
        k_per_9 = (pitcher_ks * 9.0 / innings) if innings else None
        bb_per_9 = (pitcher_walks * 9.0 / innings) if innings else None
        avg = safe_float(hitting_stats.get("avg"))
        slg = safe_float(hitting_stats.get("slg"))
        iso = (slg - avg) if avg is not None and slg is not None else None
        return PlayerStatsDaily(
            player_name=person.get("fullName") or "Unknown",
            mlb_player_id=int(player_id),
            stat_date=stat_date,
            season_year=season_year,
            games=safe_int((hitting_stats or pitching_stats).get("gamesPlayed")),
            avg=avg,
            obp=safe_float(hitting_stats.get("obp")),
            slg=slg,
            ops=safe_float(hitting_stats.get("ops")),
            iso=iso,
            hr=safe_int(hitting_stats.get("homeRuns")),
            rbi=safe_int(hitting_stats.get("rbi")),
            bb_rate=bb_rate,
            k_rate=k_rate,
            era=safe_float(pitching_stats.get("era")),
            whip=safe_float(pitching_stats.get("whip")),
            k_per_9=k_per_9,
            bb_per_9=bb_per_9,
            saves=safe_int(pitching_stats.get("saves")),
            holds=safe_int(pitching_stats.get("holds")),
            innings=innings,
            source_json=person,
        )

    def _extract_stats(self, person: Dict) -> tuple[Dict, Dict]:
        hitting: Dict = {}
        pitching: Dict = {}
        for entry in person.get("stats", []):
            group = ((entry.get("group") or {}).get("displayName") or "").lower()
            splits = entry.get("splits", [])
            if not splits:
                continue
            if group == "hitting":
                hitting = splits[0].get("stat", {})
            elif group == "pitching":
                pitching = splits[0].get("stat", {})
        return hitting, pitching

    def _persist_probable_pitchers(self, session: Session, game_date: date, game: Dict) -> int:
        created = 0
        for side in ("home", "away"):
            team_payload = ((game.get("teams") or {}).get(side) or {})
            probable = team_payload.get("probablePitcher") or {}
            if probable.get("id") is None:
                continue
            session.add(
                ProbableStarter(
                    game_date=game_date,
                    team=(team_payload.get("team") or {}).get("name"),
                    mlb_player_id=int(probable["id"]),
                    confirmed=bool(probable),
                    opponent=((game.get("teams") or {}).get("away" if side == "home" else "home") or {}).get("team", {}).get("name"),
                )
            )
            created += 1
        return created

    def _persist_lineups(self, session: Session, game_date: date, game: Dict) -> int:
        created = 0
        for side in ("home", "away"):
            lineup = ((game.get("lineups") or {}).get(side) or [])
            for index, player in enumerate(lineup, start=1):
                person = player.get("person") or {}
                if person.get("id") is None:
                    continue
                session.add(
                    LineupStatus(
                        game_date=game_date,
                        mlb_player_id=int(person["id"]),
                        team=((game.get("teams") or {}).get(side) or {}).get("team", {}).get("name"),
                        lineup_spot=index,
                        starting=True,
                        confirmed=True,
                        opponent=((game.get("teams") or {}).get("away" if side == "home" else "home") or {}).get("team", {}).get("name"),
                        handedness_context=None,
                        status="starting",
                    )
                )
                created += 1
        return created

    def _innings_to_float(self, value) -> Optional[float]:
        if value in (None, ""):
            return None
        text = str(value)
        if "." not in text:
            return float(text)
        whole, fraction = text.split(".", 1)
        if fraction == "1":
            return float(whole) + (1.0 / 3.0)
        if fraction == "2":
            return float(whole) + (2.0 / 3.0)
        try:
            return float(text)
        except ValueError:
            return None

    def _avg(self, rows: List[PlayerStatsDaily], field_name: str) -> Optional[float]:
        values = [getattr(row, field_name) for row in rows if getattr(row, field_name) is not None]
        if not values:
            return None
        return round(sum(values) / len(values), 4)
