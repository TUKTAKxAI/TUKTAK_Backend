"""add chat rooms and messages

Revision ID: 20260724_0001
Revises: 20260710_0003
Create Date: 2026-07-24 00:01:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "20260724_0001"
down_revision: str | None = "20260710_0003"
branch_labels = None
depends_on = None
BIGINT = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "chat_rooms",
        sa.Column("chat_room_id", BIGINT, primary_key=True, autoincrement=True),
        sa.Column("matching_request_id", BIGINT, nullable=False),
        sa.Column("work_order_id", BIGINT, nullable=False),
        sa.Column("customer_id", BIGINT, nullable=False),
        sa.Column("contractor_id", BIGINT, nullable=False),
        sa.Column("room_status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["matching_request_id"],
            ["matching_requests.matching_request_id"],
            name="fk_chat_rooms_matching_request_id_matching_requests",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["work_orders.work_order_id"],
            name="fk_chat_rooms_work_order_id_work_orders",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["users.user_id"],
            name="fk_chat_rooms_customer_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["contractor_id"],
            ["contractor_profiles.contractor_id"],
            name="fk_chat_rooms_contractor_id_contractor_profiles",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("matching_request_id", name="uq_chat_rooms_matching_request_id"),
        sa.UniqueConstraint("work_order_id", name="uq_chat_rooms_work_order_id"),
    )
    op.create_index("ix_chat_rooms_customer_updated", "chat_rooms", ["customer_id", "updated_at"])
    op.create_index("ix_chat_rooms_contractor_updated", "chat_rooms", ["contractor_id", "updated_at"])

    op.create_table(
        "chat_messages",
        sa.Column("message_id", BIGINT, primary_key=True, autoincrement=True),
        sa.Column("chat_room_id", BIGINT, nullable=False),
        sa.Column("sender_id", BIGINT, nullable=False),
        sa.Column("message_type", sa.String(length=20), nullable=False, server_default="TEXT"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("client_message_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["chat_room_id"],
            ["chat_rooms.chat_room_id"],
            name="fk_chat_messages_chat_room_id_chat_rooms",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["users.user_id"],
            name="fk_chat_messages_sender_id_users",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "chat_room_id",
            "sender_id",
            "client_message_id",
            name="uq_chat_messages_client_message",
        ),
    )
    op.create_index("ix_chat_messages_room_created", "chat_messages", ["chat_room_id", "created_at"])
    op.create_index("ix_chat_messages_room_id", "chat_messages", ["chat_room_id", "message_id"])

    op.create_table(
        "chat_room_members",
        sa.Column("chat_room_member_id", BIGINT, primary_key=True, autoincrement=True),
        sa.Column("chat_room_id", BIGINT, nullable=False),
        sa.Column("user_id", BIGINT, nullable=False),
        sa.Column("last_read_message_id", BIGINT, nullable=True),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["chat_room_id"],
            ["chat_rooms.chat_room_id"],
            name="fk_chat_room_members_chat_room_id_chat_rooms",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            name="fk_chat_room_members_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("chat_room_id", "user_id", name="uq_chat_room_members_room_user"),
    )

    op.execute(
        """
        INSERT INTO chat_rooms
            (matching_request_id, work_order_id, customer_id, contractor_id, room_status)
        SELECT
            matching_request_id,
            work_order_id,
            customer_id,
            contractor_id,
            'OPEN'
        FROM work_orders
        ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
        """
    )
    op.execute(
        """
        INSERT INTO chat_room_members (chat_room_id, user_id)
        SELECT chat_room_id, customer_id FROM chat_rooms
        ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
        """
    )
    op.execute(
        """
        INSERT INTO chat_room_members (chat_room_id, user_id)
        SELECT chat_room_id, contractor_id FROM chat_rooms
        ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
        """
    )


def downgrade() -> None:
    op.drop_table("chat_room_members")
    op.drop_index("ix_chat_messages_room_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_room_created", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_chat_rooms_contractor_updated", table_name="chat_rooms")
    op.drop_index("ix_chat_rooms_customer_updated", table_name="chat_rooms")
    op.drop_table("chat_rooms")
