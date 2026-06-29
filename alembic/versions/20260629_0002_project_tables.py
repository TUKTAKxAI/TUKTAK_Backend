"""Create project domain tables.

Revision ID: 20260629_0002
Revises: 20260626_0005
Create Date: 2026-06-29
"""

from typing import Sequence

from alembic import op

from app.db.base import Base
import app.db.models  # noqa: F401

revision: str = "20260629_0002"
down_revision: str | None = "20260626_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EXCLUDED_TABLES = {
    "users",
    "auth_tokens",
    "user_agreements",
    "contractor_profiles",
    "matching_requests",
    "matching_targets",
    "quotes",
    "work_orders",
}


def upgrade() -> None:
    bind = op.get_bind()
    for table in Base.metadata.sorted_tables:
        if table.name not in EXCLUDED_TABLES:
            table.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(Base.metadata.sorted_tables):
        if table.name not in EXCLUDED_TABLES:
            table.drop(bind=bind, checkfirst=True)
