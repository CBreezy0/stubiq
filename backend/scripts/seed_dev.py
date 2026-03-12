"""Seed the local development database with sample market intelligence data."""

from __future__ import annotations

from app.config import get_settings
from app.database import create_db_engine, create_session_factory, init_schema
from app.services.seed import seed_dev_data


if __name__ == "__main__":
    settings = get_settings()
    engine = create_db_engine(settings.database_url, echo=settings.debug)
    init_schema(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        result = seed_dev_data(session)
        session.commit()
        print(result)
