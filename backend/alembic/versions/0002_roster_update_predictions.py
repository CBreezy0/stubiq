"""add roster update predictions table

Revision ID: 0002_roster_update_predictions
Revises: 0001_initial_schema
Create Date: 2026-03-11 00:30:00.000000
"""

from __future__ import annotations

from alembic import op

from app.database import Base
from app.models import load_all_models

revision = "0002_roster_update_predictions"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    load_all_models()
    bind = op.get_bind()
    Base.metadata.tables["roster_update_predictions"].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    load_all_models()
    bind = op.get_bind()
    Base.metadata.tables["roster_update_predictions"].drop(bind=bind, checkfirst=True)
