"""add precomputed market analytics cache tables

Revision ID: 0007_precomputed_market_analytics
Revises: 0006_price_history_and_inventory
Create Date: 2026-03-14 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_precomputed_market_analytics"
down_revision = "0006_price_history_and_inventory"
branch_labels = None
depends_on = None


marketphase_enum = sa.Enum(
    "EARLY_ACCESS",
    "FULL_LAUNCH_SUPPLY_SHOCK",
    "STABILIZATION",
    "PRE_ATTRIBUTE_UPDATE",
    "POST_ATTRIBUTE_UPDATE",
    "CONTENT_DROP",
    "STUB_SALE",
    "LATE_CYCLE",
    name="marketphase",
    create_type=False,
)


def _bind():
    return op.get_bind()


def _inspect():
    return sa.inspect(_bind())


def _table_exists(table_name: str) -> bool:
    return table_name in set(_inspect().get_table_names())


def _index_names(table_name: str) -> set[str]:
    return {index["name"] for index in _inspect().get_indexes(table_name) if index.get("name")}


def _create_top_flips() -> None:
    if _table_exists("top_flips"):
        return
    op.create_table(
        "top_flips",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("buy_price", sa.Integer(), nullable=True),
        sa.Column("sell_price", sa.Integer(), nullable=True),
        sa.Column("profit", sa.Integer(), nullable=True),
        sa.Column("roi", sa.Float(), nullable=True),
        sa.Column("profit_per_min", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["cards.item_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_id", name="uq_top_flips_item"),
    )
    op.create_index("ix_top_flips_item_id", "top_flips", ["item_id"], unique=False)
    op.create_index("ix_top_flips_name", "top_flips", ["name"], unique=False)
    op.create_index("ix_top_flips_buy_price", "top_flips", ["buy_price"], unique=False)
    op.create_index("ix_top_flips_sell_price", "top_flips", ["sell_price"], unique=False)
    op.create_index("ix_top_flips_profit", "top_flips", ["profit"], unique=False)
    op.create_index("ix_top_flips_roi", "top_flips", ["roi"], unique=False)
    op.create_index("ix_top_flips_profit_per_min", "top_flips", ["profit_per_min"], unique=False)
    op.create_index("ix_top_flips_updated_at", "top_flips", ["updated_at"], unique=False)


def _create_market_movers() -> None:
    if _table_exists("market_movers"):
        return
    op.create_table(
        "market_movers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("current_price", sa.Integer(), nullable=True),
        sa.Column("previous_price", sa.Integer(), nullable=True),
        sa.Column("change_percent", sa.Float(), nullable=True),
        sa.Column("volume", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["cards.item_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_id", name="uq_market_movers_item"),
    )
    op.create_index("ix_market_movers_item_id", "market_movers", ["item_id"], unique=False)
    op.create_index("ix_market_movers_name", "market_movers", ["name"], unique=False)
    op.create_index("ix_market_movers_current_price", "market_movers", ["current_price"], unique=False)
    op.create_index("ix_market_movers_change_percent", "market_movers", ["change_percent"], unique=False)
    op.create_index("ix_market_movers_updated_at", "market_movers", ["updated_at"], unique=False)


def _create_floor_opportunities() -> None:
    if _table_exists("floor_opportunities"):
        return
    op.create_table(
        "floor_opportunities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("floor_price", sa.Integer(), nullable=True),
        sa.Column("expected_value", sa.Float(), nullable=True),
        sa.Column("roi", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["cards.item_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_id", name="uq_floor_opportunities_item"),
    )
    op.create_index("ix_floor_opportunities_item_id", "floor_opportunities", ["item_id"], unique=False)
    op.create_index("ix_floor_opportunities_name", "floor_opportunities", ["name"], unique=False)
    op.create_index("ix_floor_opportunities_floor_price", "floor_opportunities", ["floor_price"], unique=False)
    op.create_index("ix_floor_opportunities_expected_value", "floor_opportunities", ["expected_value"], unique=False)
    op.create_index("ix_floor_opportunities_roi", "floor_opportunities", ["roi"], unique=False)
    op.create_index("ix_floor_opportunities_updated_at", "floor_opportunities", ["updated_at"], unique=False)


def _create_market_phase() -> None:
    if _table_exists("market_phase"):
        return
    op.create_table(
        "market_phase",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("phase", marketphase_enum, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_phase_phase", "market_phase", ["phase"], unique=False)
    op.create_index("ix_market_phase_updated_at", "market_phase", ["updated_at"], unique=False)


def upgrade() -> None:
    _create_top_flips()
    _create_market_movers()
    _create_floor_opportunities()
    _create_market_phase()


def downgrade() -> None:
    if _table_exists("market_phase"):
        indexes = _index_names("market_phase")
        for index_name in [
            "ix_market_phase_updated_at",
            "ix_market_phase_phase",
        ]:
            if index_name in indexes:
                op.drop_index(index_name, table_name="market_phase")
        op.drop_table("market_phase")

    if _table_exists("floor_opportunities"):
        indexes = _index_names("floor_opportunities")
        for index_name in [
            "ix_floor_opportunities_updated_at",
            "ix_floor_opportunities_roi",
            "ix_floor_opportunities_expected_value",
            "ix_floor_opportunities_floor_price",
            "ix_floor_opportunities_name",
            "ix_floor_opportunities_item_id",
        ]:
            if index_name in indexes:
                op.drop_index(index_name, table_name="floor_opportunities")
        op.drop_table("floor_opportunities")

    if _table_exists("market_movers"):
        indexes = _index_names("market_movers")
        for index_name in [
            "ix_market_movers_updated_at",
            "ix_market_movers_change_percent",
            "ix_market_movers_current_price",
            "ix_market_movers_name",
            "ix_market_movers_item_id",
        ]:
            if index_name in indexes:
                op.drop_index(index_name, table_name="market_movers")
        op.drop_table("market_movers")

    if _table_exists("top_flips"):
        indexes = _index_names("top_flips")
        for index_name in [
            "ix_top_flips_updated_at",
            "ix_top_flips_profit_per_min",
            "ix_top_flips_roi",
            "ix_top_flips_profit",
            "ix_top_flips_sell_price",
            "ix_top_flips_buy_price",
            "ix_top_flips_name",
            "ix_top_flips_item_id",
        ]:
            if index_name in indexes:
                op.drop_index(index_name, table_name="top_flips")
        op.drop_table("top_flips")
