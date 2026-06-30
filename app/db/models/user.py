from datetime import datetime

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import BIGINT_PK


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    login_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    phone_carrier: Mapped[str | None] = mapped_column(String(20))
    profile_image_url: Mapped[str | None] = mapped_column(String(500))
    user_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    account_status: Mapped[str] = mapped_column(
        String(20), index=True, nullable=False, default="ACTIVE", server_default="ACTIVE"
    )
    default_address_json: Mapped[dict | None] = mapped_column(JSON)
    push_subscription_json: Mapped[dict | None] = mapped_column(JSON)
    notification_settings_json: Mapped[dict | None] = mapped_column(JSON)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    auth_tokens: Mapped[list["AuthToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    agreements: Mapped[list["UserAgreement"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    contractor_profile: Mapped["ContractorProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
