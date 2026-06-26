"""Create matching workflow tables.

Revision ID: 20260626_0002
Revises: 20260624_0001
Create Date: 2026-06-26
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260626_0002"
down_revision: str | None = "20260624_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "matching_requests",
        sa.Column("matching_request_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("estimate_id", sa.BigInteger(), nullable=True),
        sa.Column("service_task_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("region_code_id", sa.BigInteger(), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("preferred_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("preferred_time_start", sa.String(10), nullable=True),
        sa.Column("preferred_time_end", sa.String(10), nullable=True),
        sa.Column("contact_time_text", sa.String(100), nullable=True),
        sa.Column("budget_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("budget_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("request_message", sa.Text(), nullable=True),
        sa.Column("privacy_settings_json", sa.JSON(), nullable=True),
        sa.Column("is_emergency", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("matching_status", sa.String(20), server_default="REQUESTED", nullable=False),
        sa.Column("matched_contractor_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("selected_quote_id", sa.BigInteger(), nullable=True),
        sa.Column("selected_contractor_id", sa.BigInteger(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["users.user_id"], name="fk_matching_requests_customer_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("matching_request_id", name="pk_matching_requests"),
    )
    op.create_index(
        "ix_matching_requests_customer_status",
        "matching_requests",
        ["customer_id", "matching_status"],
    )

    op.create_table(
        "matching_targets",
        sa.Column("matching_target_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("matching_request_id", sa.BigInteger(), nullable=False),
        sa.Column("contractor_id", sa.BigInteger(), nullable=False),
        sa.Column("target_status", sa.String(20), server_default="NOTIFIED", nullable=False),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("declined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractor_profiles.contractor_id"], name="fk_matching_targets_contractor_id_contractor_profiles", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matching_request_id"], ["matching_requests.matching_request_id"], name="fk_matching_targets_matching_request_id_matching_requests", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("matching_target_id", name="pk_matching_targets"),
    )
    op.create_index(
        "ix_matching_targets_contractor_status",
        "matching_targets",
        ["contractor_id", "target_status"],
    )

    op.create_table(
        "quotes",
        sa.Column("quote_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("matching_request_id", sa.BigInteger(), nullable=False),
        sa.Column("contractor_id", sa.BigInteger(), nullable=False),
        sa.Column("quote_status", sa.String(20), server_default="SENT", nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("work_scope", sa.Text(), nullable=True),
        sa.Column("quote_items_json", sa.JSON(), nullable=True),
        sa.Column("included_items", sa.Text(), nullable=True),
        sa.Column("excluded_items", sa.Text(), nullable=True),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("visit_count", sa.Integer(), nullable=True),
        sa.Column("available_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("arrival_time", sa.String(50), nullable=True),
        sa.Column("as_period_days", sa.Integer(), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("additional_note", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractor_profiles.contractor_id"], name="fk_quotes_contractor_id_contractor_profiles", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matching_request_id"], ["matching_requests.matching_request_id"], name="fk_quotes_matching_request_id_matching_requests", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("quote_id", name="pk_quotes"),
    )
    op.create_index(
        "ix_quotes_matching_request_status",
        "quotes",
        ["matching_request_id", "quote_status"],
    )

    op.create_table(
        "work_orders",
        sa.Column("work_order_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("matching_request_id", sa.BigInteger(), nullable=False),
        sa.Column("quote_id", sa.BigInteger(), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("contractor_id", sa.BigInteger(), nullable=False),
        sa.Column("work_order_status", sa.String(20), server_default="CREATED", nullable=False),
        sa.Column("final_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_start_time", sa.String(10), nullable=True),
        sa.Column("scheduled_end_time", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractor_profiles.contractor_id"], name="fk_work_orders_contractor_id_contractor_profiles", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["customer_id"], ["users.user_id"], name="fk_work_orders_customer_id_users", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["matching_request_id"], ["matching_requests.matching_request_id"], name="fk_work_orders_matching_request_id_matching_requests", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.quote_id"], name="fk_work_orders_quote_id_quotes", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("work_order_id", name="pk_work_orders"),
        sa.UniqueConstraint("matching_request_id", name="uq_work_orders_matching_request_id"),
        sa.UniqueConstraint("quote_id", name="uq_work_orders_quote_id"),
    )


def downgrade() -> None:
    op.drop_table("work_orders")
    op.drop_index("ix_quotes_matching_request_status", table_name="quotes")
    op.drop_table("quotes")
    op.drop_index("ix_matching_targets_contractor_status", table_name="matching_targets")
    op.drop_table("matching_targets")
    op.drop_index("ix_matching_requests_customer_status", table_name="matching_requests")
    op.drop_table("matching_requests")
