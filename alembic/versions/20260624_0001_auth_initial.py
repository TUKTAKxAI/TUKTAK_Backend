"""Create authentication and contractor profile tables.

Revision ID: 20260624_0001
Revises:
Create Date: 2026-06-24
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260624_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("login_id", sa.String(50), nullable=False),
        sa.Column("email", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("nickname", sa.String(50), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("phone_carrier", sa.String(20), nullable=True),
        sa.Column("profile_image_url", sa.String(500), nullable=True),
        sa.Column("user_type", sa.String(20), nullable=False),
        sa.Column("account_status", sa.String(20), server_default="ACTIVE", nullable=False),
        sa.Column("default_address_json", sa.JSON(), nullable=True),
        sa.Column("push_subscription_json", sa.JSON(), nullable=True),
        sa.Column("notification_settings_json", sa.JSON(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("user_id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("login_id", name="uq_users_login_id"),
        sa.UniqueConstraint("nickname", name="uq_users_nickname"),
        sa.UniqueConstraint("phone", name="uq_users_phone"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_user_type", "users", ["user_type"])
    op.create_index("ix_users_account_status", "users", ["account_status"])

    op.create_table(
        "auth_tokens",
        sa.Column("token_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_type", sa.String(30), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_auth_tokens_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_id", name="pk_auth_tokens"),
        sa.UniqueConstraint("token_hash", name="uq_auth_tokens_token_hash"),
    )
    op.create_index("ix_auth_tokens_user_type", "auth_tokens", ["user_id", "token_type"])

    op.create_table(
        "user_agreements",
        sa.Column("agreement_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("terms_type", sa.String(50), nullable=False),
        sa.Column("terms_version", sa.String(20), nullable=False),
        sa.Column("terms_title", sa.String(150), nullable=False),
        sa.Column("terms_content_url", sa.String(500), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("is_agreed", sa.Boolean(), nullable=False),
        sa.Column("agreed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_user_agreements_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("agreement_id", name="pk_user_agreements"),
        sa.UniqueConstraint("user_id", "terms_type", "terms_version", name="uq_user_agreement_version"),
    )

    op.create_table(
        "contractor_profiles",
        sa.Column("contractor_id", sa.BigInteger(), nullable=False),
        sa.Column("business_name", sa.String(100), nullable=False),
        sa.Column("representative_name", sa.String(50), nullable=False),
        sa.Column("business_number", sa.String(20), nullable=True),
        sa.Column("contact_phone", sa.String(20), nullable=False),
        sa.Column("introduction", sa.Text(), nullable=True),
        sa.Column("business_status", sa.String(20), nullable=False),
        sa.Column("approval_status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("document_status_json", sa.JSON(), nullable=True),
        sa.Column("service_radius_km", sa.Numeric(6, 2), nullable=True),
        sa.Column("rating_avg", sa.Numeric(3, 2), server_default="0", nullable=False),
        sa.Column("review_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("matching_alert_enabled", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("available_status", sa.String(20), server_default="AVAILABLE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["contractor_id"], ["users.user_id"], name="fk_contractor_profiles_contractor_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("contractor_id", name="pk_contractor_profiles"),
        sa.UniqueConstraint("business_number", name="uq_contractor_profiles_business_number"),
    )


def downgrade() -> None:
    op.drop_table("contractor_profiles")
    op.drop_table("user_agreements")
    op.drop_index("ix_auth_tokens_user_type", table_name="auth_tokens")
    op.drop_table("auth_tokens")
    op.drop_index("ix_users_account_status", table_name="users")
    op.drop_index("ix_users_user_type", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
