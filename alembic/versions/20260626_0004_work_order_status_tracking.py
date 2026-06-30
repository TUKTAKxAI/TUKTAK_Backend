"""Add work order status tracking columns.

Revision ID: 20260626_0004
Revises: 20260626_0003
Create Date: 2026-06-26
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260626_0004"
down_revision: str | None = "20260626_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "work_orders",
        sa.Column("contact_revealed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "work_orders",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "work_orders",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "work_orders",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "work_orders",
        sa.Column("cancel_reason", sa.String(500), nullable=True),
    )
    op.add_column(
        "work_orders",
        sa.Column("customer_confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "work_orders",
        sa.Column("contractor_confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("work_orders", "contractor_confirmed_at")
    op.drop_column("work_orders", "customer_confirmed_at")
    op.drop_column("work_orders", "cancel_reason")
    op.drop_column("work_orders", "cancelled_at")
    op.drop_column("work_orders", "completed_at")
    op.drop_column("work_orders", "started_at")
    op.drop_column("work_orders", "contact_revealed_at")
