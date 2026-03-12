"""Optional database seeding helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Card
from app.services.seed import seed_dev_data



def seed_if_empty(session: Session) -> bool:
    if session.query(Card).count() == 0:
        print("Database empty, seeding demo data.")
        seed_dev_data(session)
        return True
    return False
