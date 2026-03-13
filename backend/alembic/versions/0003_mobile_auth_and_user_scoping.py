"""add mobile auth, user settings, and user-scoped portfolio

Revision ID: 0003_mobile_auth_user_scope
Revises: 0002_roster_update_predictions
Create Date: 2026-03-12 00:00:00.000000
"""

from __future__ import annotations

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision = "0003_mobile_auth_user_scope"
down_revision = "0002_roster_update_predictions"
branch_labels = None
depends_on = None

LEGACY_USER_ID = "00000000-0000-0000-0000-000000000001"
LEGACY_USER_EMAIL = "legacy-portfolio@local.dev"


def _inspect():
    return sa.inspect(op.get_bind())



def _table_exists(table_name: str) -> bool:
    return table_name in set(_inspect().get_table_names())



def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in _inspect().get_columns(table_name)}



def _unique_constraint_names(table_name: str) -> set[str]:
    return {constraint["name"] for constraint in _inspect().get_unique_constraints(table_name) if constraint.get("name")}



def _index_names(table_name: str) -> set[str]:
    return {index["name"] for index in _inspect().get_indexes(table_name) if index.get("name")}



def _has_foreign_key(table_name: str, constrained_column: str) -> bool:
    return any(constrained_column in fk.get("constrained_columns", []) for fk in _inspect().get_foreign_keys(table_name))



def _scalar(sql: str, **params):
    return op.get_bind().execute(sa.text(sql), params).scalar()



def _postgres_enum_labels(enum_name: str) -> set[str]:
    if op.get_bind().dialect.name != "postgresql":
        return set()
    rows = op.get_bind().execute(
        sa.text(
            """
            SELECT enumlabel
            FROM pg_enum
            JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
            WHERE pg_type.typname = :enum_name
            """
        ),
        {"enum_name": enum_name},
    ).fetchall()
    return {row[0] for row in rows}



def _enum_seed_value(enum_name: str, preferred: str, fallback: str) -> str:
    labels = _postgres_enum_labels(enum_name)
    if preferred in labels:
        return preferred
    if fallback in labels:
        return fallback
    return preferred



def _create_tables() -> None:
    auth_provider_enum = sa.Enum("EMAIL", "GOOGLE", name="authprovider")
    connection_provider_enum = sa.Enum("XBOX", "PLAYSTATION", name="connectionprovider")
    connection_status_enum = sa.Enum(
        "NOT_CONNECTED",
        "CONNECTED",
        "EXPIRED",
        "ERROR",
        "RECONNECT_REQUIRED",
        name="connectionstatus",
    )

    if not _table_exists("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=True),
            sa.Column("avatar_url", sa.String(length=1024), nullable=True),
            sa.Column("auth_provider", auth_provider_enum, nullable=False),
            sa.Column("google_sub", sa.String(length=255), nullable=True),
            sa.Column("password_hash", sa.String(length=255), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("is_verified", sa.Boolean(), nullable=False),
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email", name="uq_users_email"),
            sa.UniqueConstraint("google_sub", name="uq_users_google_sub"),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=False)
        op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=False)
        op.create_index("ix_users_auth_provider", "users", ["auth_provider"], unique=False)

    if not _table_exists("user_settings"):
        op.create_table(
            "user_settings",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("floor_buy_margin", sa.Float(), nullable=False),
            sa.Column("launch_supply_crash_threshold", sa.Float(), nullable=False),
            sa.Column("flip_profit_minimum", sa.Float(), nullable=False),
            sa.Column("grind_market_edge", sa.Float(), nullable=False),
            sa.Column("collection_lock_penalty", sa.Float(), nullable=False),
            sa.Column("gatekeeper_hold_weight", sa.Float(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", name="uq_user_settings_user"),
        )
        op.create_index("ix_user_settings_user_id", "user_settings", ["user_id"], unique=False)

    if not _table_exists("refresh_tokens"):
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("token_hash", sa.String(length=128), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("device_name", sa.String(length=255), nullable=True),
            sa.Column("platform", sa.String(length=64), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        )
        op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)
        op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=False)
        op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"], unique=False)
        op.create_index("ix_refresh_tokens_revoked_at", "refresh_tokens", ["revoked_at"], unique=False)

    if not _table_exists("user_connections"):
        op.create_table(
            "user_connections",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("provider", connection_provider_enum, nullable=False),
            sa.Column("provider_account_id", sa.String(length=255), nullable=True),
            sa.Column("display_name", sa.String(length=255), nullable=True),
            sa.Column("gamertag_or_psn", sa.String(length=255), nullable=True),
            sa.Column("status", connection_status_enum, nullable=False),
            sa.Column("access_token_encrypted", sa.Text(), nullable=True),
            sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "provider", name="uq_user_connection_user_provider"),
        )
        op.create_index("ix_user_connections_user_id", "user_connections", ["user_id"], unique=False)
        op.create_index("ix_user_connections_provider", "user_connections", ["provider"], unique=False)
        op.create_index("ix_user_connections_status", "user_connections", ["status"], unique=False)



def _ensure_legacy_user() -> None:
    now = datetime.now(timezone.utc)
    exists = _scalar("SELECT id FROM users WHERE id = :user_id", user_id=LEGACY_USER_ID)
    if not exists:
        users = sa.table(
            "users",
            sa.column("id", sa.String()),
            sa.column("email", sa.String()),
            sa.column("display_name", sa.String()),
            sa.column("avatar_url", sa.String()),
            sa.column("auth_provider", sa.String()),
            sa.column("google_sub", sa.String()),
            sa.column("password_hash", sa.String()),
            sa.column("is_active", sa.Boolean()),
            sa.column("is_verified", sa.Boolean()),
            sa.column("last_login_at", sa.DateTime(timezone=True)),
            sa.column("created_at", sa.DateTime(timezone=True)),
            sa.column("updated_at", sa.DateTime(timezone=True)),
        )
        op.bulk_insert(
            users,
            [
                {
                    "id": LEGACY_USER_ID,
                    "email": LEGACY_USER_EMAIL,
                    "display_name": "Legacy Portfolio",
                    "avatar_url": None,
                    "auth_provider": _enum_seed_value("authprovider", "EMAIL", "email"),
                    "google_sub": None,
                    "password_hash": None,
                    "is_active": True,
                    "is_verified": False,
                    "last_login_at": None,
                    "created_at": now,
                    "updated_at": now,
                }
            ],
        )
    exists_settings = _scalar("SELECT id FROM user_settings WHERE user_id = :user_id", user_id=LEGACY_USER_ID)
    if not exists_settings:
        user_settings = sa.table(
            "user_settings",
            sa.column("user_id", sa.String()),
            sa.column("floor_buy_margin", sa.Float()),
            sa.column("launch_supply_crash_threshold", sa.Float()),
            sa.column("flip_profit_minimum", sa.Float()),
            sa.column("grind_market_edge", sa.Float()),
            sa.column("collection_lock_penalty", sa.Float()),
            sa.column("gatekeeper_hold_weight", sa.Float()),
            sa.column("created_at", sa.DateTime(timezone=True)),
            sa.column("updated_at", sa.DateTime(timezone=True)),
        )
        op.bulk_insert(
            user_settings,
            [
                {
                    "user_id": LEGACY_USER_ID,
                    "floor_buy_margin": 0.08,
                    "launch_supply_crash_threshold": 0.18,
                    "flip_profit_minimum": 250.0,
                    "grind_market_edge": 0.05,
                    "collection_lock_penalty": 15.0,
                    "gatekeeper_hold_weight": 10.0,
                    "created_at": now,
                    "updated_at": now,
                }
            ],
        )



def _backfill_portfolio_positions() -> None:
    if not _table_exists("portfolio_positions"):
        return

    columns = _column_names("portfolio_positions")
    if "user_id" not in columns:
        with op.batch_alter_table("portfolio_positions") as batch_op:
            batch_op.add_column(sa.Column("user_id", sa.String(length=36), nullable=True))

    if _scalar("SELECT COUNT(*) FROM portfolio_positions"):
        _ensure_legacy_user()
        op.execute(sa.text("UPDATE portfolio_positions SET user_id = :user_id WHERE user_id IS NULL").bindparams(user_id=LEGACY_USER_ID))

    columns = _column_names("portfolio_positions")
    indexes = _index_names("portfolio_positions")
    unique_constraints = _unique_constraint_names("portfolio_positions")
    has_fk = _has_foreign_key("portfolio_positions", "user_id")
    nullable = next(column["nullable"] for column in _inspect().get_columns("portfolio_positions") if column["name"] == "user_id")

    with op.batch_alter_table("portfolio_positions") as batch_op:
        if "uq_portfolio_position_user_item" not in unique_constraints:
            if "uq_portfolio_position_item" in unique_constraints:
                batch_op.drop_constraint("uq_portfolio_position_item", type_="unique")
            batch_op.create_unique_constraint("uq_portfolio_position_user_item", ["user_id", "item_id"])
        if "ix_portfolio_positions_user_id" not in indexes:
            batch_op.create_index("ix_portfolio_positions_user_id", ["user_id"], unique=False)
        if not has_fk:
            batch_op.create_foreign_key(
                "fk_portfolio_positions_user_id_users",
                "users",
                ["user_id"],
                ["id"],
                ondelete="CASCADE",
            )
        if nullable:
            batch_op.alter_column("user_id", existing_type=sa.String(length=36), nullable=False)



def _backfill_transactions() -> None:
    if not _table_exists("transactions"):
        return

    columns = _column_names("transactions")
    if "user_id" not in columns:
        with op.batch_alter_table("transactions") as batch_op:
            batch_op.add_column(sa.Column("user_id", sa.String(length=36), nullable=True))

    if _scalar("SELECT COUNT(*) FROM transactions"):
        _ensure_legacy_user()
        op.execute(sa.text("UPDATE transactions SET user_id = :user_id WHERE user_id IS NULL").bindparams(user_id=LEGACY_USER_ID))

    indexes = _index_names("transactions")
    has_fk = _has_foreign_key("transactions", "user_id")
    nullable = next(column["nullable"] for column in _inspect().get_columns("transactions") if column["name"] == "user_id")

    with op.batch_alter_table("transactions") as batch_op:
        if "ix_transactions_user_id" not in indexes:
            batch_op.create_index("ix_transactions_user_id", ["user_id"], unique=False)
        if not has_fk:
            batch_op.create_foreign_key(
                "fk_transactions_user_id_users",
                "users",
                ["user_id"],
                ["id"],
                ondelete="CASCADE",
            )
        if nullable:
            batch_op.alter_column("user_id", existing_type=sa.String(length=36), nullable=False)



def upgrade() -> None:
    _create_tables()
    _backfill_portfolio_positions()
    _backfill_transactions()



def downgrade() -> None:
    if _table_exists("transactions") and "user_id" in _column_names("transactions"):
        indexes = _index_names("transactions")
        has_fk = _has_foreign_key("transactions", "user_id")
        with op.batch_alter_table("transactions") as batch_op:
            if has_fk:
                batch_op.drop_constraint("fk_transactions_user_id_users", type_="foreignkey")
            if "ix_transactions_user_id" in indexes:
                batch_op.drop_index("ix_transactions_user_id")
            batch_op.drop_column("user_id")

    if _table_exists("portfolio_positions") and "user_id" in _column_names("portfolio_positions"):
        indexes = _index_names("portfolio_positions")
        unique_constraints = _unique_constraint_names("portfolio_positions")
        has_fk = _has_foreign_key("portfolio_positions", "user_id")
        with op.batch_alter_table("portfolio_positions") as batch_op:
            if has_fk:
                batch_op.drop_constraint("fk_portfolio_positions_user_id_users", type_="foreignkey")
            if "uq_portfolio_position_user_item" in unique_constraints:
                batch_op.drop_constraint("uq_portfolio_position_user_item", type_="unique")
            if "uq_portfolio_position_item" not in unique_constraints:
                batch_op.create_unique_constraint("uq_portfolio_position_item", ["item_id"])
            if "ix_portfolio_positions_user_id" in indexes:
                batch_op.drop_index("ix_portfolio_positions_user_id")
            batch_op.drop_column("user_id")

    if _table_exists("user_connections"):
        op.drop_table("user_connections")
    if _table_exists("refresh_tokens"):
        op.drop_table("refresh_tokens")
    if _table_exists("user_settings"):
        op.drop_table("user_settings")
    if _table_exists("users"):
        op.drop_table("users")

    bind = op.get_bind()
    sa.Enum(name="connectionstatus").drop(bind, checkfirst=True)
    sa.Enum(name="connectionprovider").drop(bind, checkfirst=True)
    sa.Enum(name="authprovider").drop(bind, checkfirst=True)
