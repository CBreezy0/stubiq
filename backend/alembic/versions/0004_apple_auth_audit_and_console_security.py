"""add Apple auth fields, refresh reuse metadata, and auth audit logs

Revision ID: 0004_apple_auth_audit_and_console_security
Revises: 0003_mobile_auth_and_user_scoping
Create Date: 2026-03-12 08:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004_apple_auth_audit_and_console_security"
down_revision = "0003_mobile_auth_and_user_scoping"
branch_labels = None
depends_on = None


def _bind():
    return op.get_bind()


def _inspect():
    return sa.inspect(_bind())


def _table_exists(table_name: str) -> bool:
    return table_name in set(_inspect().get_table_names())


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in _inspect().get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    return {index["name"] for index in _inspect().get_indexes(table_name) if index.get("name")}


def _is_postgresql() -> bool:
    return _bind().dialect.name == "postgresql"


def _postgres_enum_labels(enum_name: str) -> set[str]:
    if not _is_postgresql():
        return set()
    rows = _bind().execute(
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


def _ensure_authprovider_contains_apple() -> None:
    if _is_postgresql() and "apple" not in _postgres_enum_labels("authprovider"):
        op.execute("ALTER TYPE authprovider ADD VALUE IF NOT EXISTS 'apple'")


def _upgrade_users() -> None:
    if not _table_exists("users"):
        return

    columns = _column_names("users")
    indexes = _index_names("users")

    if "apple_sub" not in columns:
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(sa.Column("apple_sub", sa.String(length=255), nullable=True))

    indexes = _index_names("users")
    if "ix_users_apple_sub" not in indexes:
        op.create_index("ix_users_apple_sub", "users", ["apple_sub"], unique=True)


def _upgrade_refresh_tokens() -> None:
    if not _table_exists("refresh_tokens"):
        return

    columns = _column_names("refresh_tokens")
    indexes = _index_names("refresh_tokens")

    with op.batch_alter_table("refresh_tokens") as batch_op:
        if "replaced_by_token_hash" not in columns:
            batch_op.add_column(sa.Column("replaced_by_token_hash", sa.String(length=128), nullable=True))
        if "reuse_detected_at" not in columns:
            batch_op.add_column(sa.Column("reuse_detected_at", sa.DateTime(timezone=True), nullable=True))

    indexes = _index_names("refresh_tokens")
    if "ix_refresh_tokens_replaced_by_token_hash" not in indexes:
        op.create_index("ix_refresh_tokens_replaced_by_token_hash", "refresh_tokens", ["replaced_by_token_hash"], unique=False)
    if "ix_refresh_tokens_reuse_detected_at" not in indexes:
        op.create_index("ix_refresh_tokens_reuse_detected_at", "refresh_tokens", ["reuse_detected_at"], unique=False)


def _upgrade_auth_audit_logs() -> None:
    if _table_exists("auth_audit_logs"):
        return

    op.create_table(
        "auth_audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("auth_provider", sa.String(length=32), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("platform", sa.String(length=64), nullable=True),
        sa.Column("ip_address", sa.String(length=128), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_audit_logs_user_id", "auth_audit_logs", ["user_id"], unique=False)
    op.create_index("ix_auth_audit_logs_event_type", "auth_audit_logs", ["event_type"], unique=False)
    op.create_index("ix_auth_audit_logs_auth_provider", "auth_audit_logs", ["auth_provider"], unique=False)
    op.create_index("ix_auth_audit_logs_created_at", "auth_audit_logs", ["created_at"], unique=False)


def upgrade() -> None:
    _ensure_authprovider_contains_apple()
    _upgrade_users()
    _upgrade_refresh_tokens()
    _upgrade_auth_audit_logs()


def downgrade() -> None:
    if _table_exists("auth_audit_logs"):
        indexes = _index_names("auth_audit_logs")
        for index_name in [
            "ix_auth_audit_logs_created_at",
            "ix_auth_audit_logs_auth_provider",
            "ix_auth_audit_logs_event_type",
            "ix_auth_audit_logs_user_id",
        ]:
            if index_name in indexes:
                op.drop_index(index_name, table_name="auth_audit_logs")
        op.drop_table("auth_audit_logs")

    if _table_exists("refresh_tokens"):
        columns = _column_names("refresh_tokens")
        indexes = _index_names("refresh_tokens")
        with op.batch_alter_table("refresh_tokens") as batch_op:
            if "ix_refresh_tokens_reuse_detected_at" in indexes:
                batch_op.drop_index("ix_refresh_tokens_reuse_detected_at")
            if "ix_refresh_tokens_replaced_by_token_hash" in indexes:
                batch_op.drop_index("ix_refresh_tokens_replaced_by_token_hash")
            if "reuse_detected_at" in columns:
                batch_op.drop_column("reuse_detected_at")
            if "replaced_by_token_hash" in columns:
                batch_op.drop_column("replaced_by_token_hash")

    if _table_exists("users"):
        columns = _column_names("users")
        indexes = _index_names("users")
        with op.batch_alter_table("users") as batch_op:
            if "ix_users_apple_sub" in indexes:
                batch_op.drop_index("ix_users_apple_sub")
            if "apple_sub" in columns:
                batch_op.drop_column("apple_sub")
