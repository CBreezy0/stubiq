"""Time helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


UTC = timezone.utc



def utcnow() -> datetime:
    return datetime.now(tz=UTC)



def hours_between(later: datetime, earlier: datetime) -> float:
    return (later - earlier).total_seconds() / 3600.0



def within_hours(target: datetime, now: datetime, window_hours: float) -> bool:
    delta = abs((target - now).total_seconds())
    return delta <= window_hours * 3600.0



def add_hours(now: datetime, hours: float) -> datetime:
    return now + timedelta(hours=hours)
