"""add MLB The Show sync tables for listings metadata player search and roster updates

Revision ID: 0005_show_sync_tables
Revises: 0004_apple_auth_console_sec
Create Date: 2026-03-13 18:15:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_show_sync_tables"
down_revision = "0004_apple_auth_console_sec"
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


def _create_market_listings() -> None:
    if _table_exists("market_listings"):
        return
    op.create_table(
        "market_listings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.String(length=128), nullable=False),
        sa.Column("listing_name", sa.String(length=255), nullable=True),
        sa.Column("best_sell_price", sa.Integer(), nullable=True),
        sa.Column("best_buy_price", sa.Integer(), nullable=True),
        sa.Column("spread", sa.Integer(), nullable=True),
        sa.Column("estimated_profit", sa.Integer(), nullable=True),
        sa.Column("roi_percent", sa.Float(), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["cards.item_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_id", name="uq_market_listings_item"),
    )
    op.create_index("ix_market_listings_item_id", "market_listings", ["item_id"], unique=False)
    op.create_index("ix_market_listings_listing_name", "market_listings", ["listing_name"], unique=False)
    op.create_index("ix_market_listings_last_seen_at", "market_listings", ["last_seen_at"], unique=False)


def _create_show_metadata_snapshots() -> None:
    if _table_exists("show_metadata_snapshots"):
        return
    op.create_table(
        "show_metadata_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("series_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("brands_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("sets_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("payload_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_show_metadata_snapshots_fetched_at", "show_metadata_snapshots", ["fetched_at"], unique=False)


def _create_show_player_profiles() -> None:
    if _table_exists("show_player_profiles"):
        return
    op.create_table(
        "show_player_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("display_level", sa.String(length=64), nullable=True),
        sa.Column("games_played", sa.Integer(), nullable=True),
        sa.Column("vanity_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("most_played_modes_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("lifetime_hitting_stats_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("lifetime_defensive_stats_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("online_data_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("payload_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uq_show_player_profiles_username"),
    )
    op.create_index("ix_show_player_profiles_username", "show_player_profiles", ["username"], unique=False)
    op.create_index("ix_show_player_profiles_last_synced_at", "show_player_profiles", ["last_synced_at"], unique=False)


def _create_show_roster_updates() -> None:
    if _table_exists("show_roster_updates"):
        return
    op.create_table(
        "show_roster_updates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("remote_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("remote_id", name="uq_show_roster_updates_remote_id"),
    )
    op.create_index("ix_show_roster_updates_remote_id", "show_roster_updates", ["remote_id"], unique=False)
    op.create_index("ix_show_roster_updates_title", "show_roster_updates", ["title"], unique=False)
    op.create_index("ix_show_roster_updates_published_at", "show_roster_updates", ["published_at"], unique=False)
    op.create_index("ix_show_roster_updates_last_synced_at", "show_roster_updates", ["last_synced_at"], unique=False)


def upgrade() -> None:
    _create_market_listings()
    _create_show_metadata_snapshots()
    _create_show_player_profiles()
    _create_show_roster_updates()


def downgrade() -> None:
    if _table_exists("show_roster_updates"):
        indexes = _index_names("show_roster_updates")
        for index_name in [
            "ix_show_roster_updates_last_synced_at",
            "ix_show_roster_updates_published_at",
            "ix_show_roster_updates_title",
            "ix_show_roster_updates_remote_id",
        ]:
            if index_name in indexes:
                op.drop_index(index_name, table_name="show_roster_updates")
        op.drop_table("show_roster_updates")

    if _table_exists("show_player_profiles"):
        indexes = _index_names("show_player_profiles")
        for index_name in [
            "ix_show_player_profiles_last_synced_at",
            "ix_show_player_profiles_username",
        ]:
            if index_name in indexes:
                op.drop_index(index_name, table_name="show_player_profiles")
        op.drop_table("show_player_profiles")

    if _table_exists("show_metadata_snapshots"):
        indexes = _index_names("show_metadata_snapshots")
        if "ix_show_metadata_snapshots_fetched_at" in indexes:
            op.drop_index("ix_show_metadata_snapshots_fetched_at", table_name="show_metadata_snapshots")
        op.drop_table("show_metadata_snapshots")

    if _table_exists("market_listings"):
        indexes = _index_names("market_listings")
        for index_name in [
            "ix_market_listings_last_seen_at",
            "ix_market_listings_listing_name",
            "ix_market_listings_item_id",
        ]:
            if index_name in indexes:
                op.drop_index(index_name, table_name="market_listings")
        op.drop_table("market_listings")
