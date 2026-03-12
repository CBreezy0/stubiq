"""Database connectivity health helpers."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app import database as database_module



def check_database(bind_engine: Engine | None = None) -> None:
    target_engine = bind_engine or database_module.engine
    if target_engine is None:
        raise RuntimeError("Database engine is not configured.")
    with target_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
