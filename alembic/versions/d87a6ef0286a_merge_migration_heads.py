"""merge migration heads

Revision ID: d87a6ef0286a
Revises: 20260626_0005, 20260629_0002
Create Date: 2026-06-29 10:42:15.671431
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd87a6ef0286a'
down_revision: Union[str, None] = ('20260626_0005', '20260629_0002')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
