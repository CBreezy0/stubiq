"""Database engine and session helpers."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


engine: Optional[Engine] = None
SessionLocal = sessionmaker(autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)



def create_db_engine(database_url: str, echo: bool = False) -> Engine:
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    elif database_url.startswith("postgresql") and "neon.tech" in database_url and "sslmode=" not in database_url:
        connect_args["sslmode"] = "require"
    return create_engine(
        database_url,
        future=True,
        echo=echo,
        pool_pre_ping=True,
        connect_args=connect_args,
    )



def create_session_factory(bind_engine: Engine):
    SessionLocal.configure(bind=bind_engine)
    return SessionLocal



def configure_database(database_url: str | None = None, echo: bool = False) -> Engine:
    global DATABASE_URL, engine

    target_url = database_url or DATABASE_URL
    if not target_url:
        raise RuntimeError("DATABASE_URL is not configured.")

    DATABASE_URL = target_url
    engine = create_db_engine(target_url, echo=echo)
    SessionLocal.configure(bind=engine)
    return engine


if DATABASE_URL:
    configure_database(DATABASE_URL)



def init_schema(bind_engine: Engine | None = None):
    from .models import load_all_models

    load_all_models()
    target_engine = bind_engine or engine
    if target_engine is None:
        raise RuntimeError("DATABASE_URL is not configured.")
    Base.metadata.create_all(bind=target_engine)



def get_db(request: Request) -> Generator[Session, None, None]:
    session_factory = getattr(request.app.state, "session_factory", None) or SessionLocal
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
