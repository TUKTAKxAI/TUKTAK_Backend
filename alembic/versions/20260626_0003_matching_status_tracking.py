"""Add matching cancel and decline tracking columns.

Revision ID: 20260626_0003
Revises: 20260626_0002
Create Date: 2026-06-26
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260626_0003"
down_revision: str | None = "20260626_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "matching_requests",
        sa.Column("cancel_reason", sa.String(500), nullable=True),
    )
    op.add_column(
        "matching_requests",
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "matching_targets",
        sa.Column("declined_reason", sa.String(500), nullable=True),
    )
    op.add_column(
        "matching_targets",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("matching_targets", "updated_at")
    op.drop_column("matching_targets", "declined_reason")
    op.drop_column("matching_requests", "selected_at")
    op.drop_column("matching_requests", "cancel_reason")
