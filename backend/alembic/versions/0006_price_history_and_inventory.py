"""add price history and user inventory tables

Revision ID: 0006_price_history_and_inventory
Revises: 0005_show_sync_tables
Create Date: 2026-03-13 20:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006_price_history_and_inventory"
down_revision = "0005_show_sync_tables"
branch_labels = None
depends_on = None


def _bind():
    return op.get_bind()


def _inspect():
    return sa.inspect(_bind())


def _table_exists(table_name: str) -> bool:
    return table_name in set(_inspect().get_table_names())


def _index_names(table_name: str) -> set[str]:
    return {index["name"] for index in _inspect().get_indexes(table_name) if index.get("name")}


def _create_price_history() -> None:
    if _table_exists("price_history"):
        return
    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.String(length=128), nullable=False),
        sa.Column("buy_price", sa.Integer(), nullable=True),
        sa.Column("sell_price", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["uuid"], ["cards.item_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_price_history_uuid", "price_history", ["uuid"], unique=False)
    op.create_index("ix_price_history_timestamp", "price_history", ["timestamp"], unique=False)


def _create_user_inventory() -> None:
    if _table_exists("user_inventory"):
        return
    op.create_table(
        "user_inventory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("item_uuid", sa.String(length=128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_sellable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["item_uuid"], ["cards.item_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "item_uuid", name="uq_user_inventory_user_item"),
    )
    op.create_index("ix_user_inventory_user_id", "user_inventory", ["user_id"], unique=False)
    op.create_index("ix_user_inventory_item_uuid", "user_inventory", ["item_uuid"], unique=False)
    op.create_index("ix_user_inventory_synced_at", "user_inventory", ["synced_at"], unique=False)


def upgrade() -> None:
    _create_price_history()
    _create_user_inventory()


def downgrade() -> None:
    if _table_exists("user_inventory"):
        indexes = _index_names("user_inventory")
        for index_name in [
            "ix_user_inventory_synced_at",
            "ix_user_inventory_item_uuid",
            "ix_user_inventory_user_id",
        ]:
            if index_name in indexes:
                op.drop_index(index_name, table_name="user_inventory")
        op.drop_table("user_inventory")

    if _table_exists("price_history"):
        indexes = _index_names("price_history")
        for index_name in [
            "ix_price_history_timestamp",
            "ix_price_history_uuid",
        ]:
            if index_name in indexes:
                op.drop_index(index_name, table_name="price_history")
        op.drop_table("price_history")
