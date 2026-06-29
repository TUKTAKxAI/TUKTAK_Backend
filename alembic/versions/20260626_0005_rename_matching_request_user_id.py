"""Rename matching request customer_id to user_id.

Revision ID: 20260626_0005
Revises: 20260626_0004
Create Date: 2026-06-26
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260626_0005"
down_revision: str | None = "20260626_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "fk_matching_requests_customer_id_users",
        "matching_requests",
        type_="foreignkey",
    )
    op.drop_index("ix_matching_requests_customer_status", table_name="matching_requests")
    op.alter_column(
        "matching_requests",
        "customer_id",
        new_column_name="user_id",
        existing_type=sa.BigInteger(),
        existing_nullable=False,
    )
    op.create_foreign_key(
        "fk_matching_requests_user_id_users",
        "matching_requests",
        "users",
        ["user_id"],
        ["user_id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_matching_requests_user_status",
        "matching_requests",
        ["user_id", "matching_status"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_matching_requests_user_id_users",
        "matching_requests",
        type_="foreignkey",
    )
    op.drop_index("ix_matching_requests_user_status", table_name="matching_requests")
    op.alter_column(
        "matching_requests",
        "user_id",
        new_column_name="customer_id",
        existing_type=sa.BigInteger(),
        existing_nullable=False,
    )
    op.create_foreign_key(
        "fk_matching_requests_customer_id_users",
        "matching_requests",
        "users",
        ["customer_id"],
        ["user_id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_matching_requests_customer_status",
        "matching_requests",
        ["customer_id", "matching_status"],
    )
