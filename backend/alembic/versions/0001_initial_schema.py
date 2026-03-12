"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-11 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

from app.database import Base
from app.models import load_all_models

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    load_all_models()
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    load_all_models()
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
