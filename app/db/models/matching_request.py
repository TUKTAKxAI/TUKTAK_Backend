from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import BIGINT_PK


class MatchingRequest(Base):
    __tablename__ = "matching_requests"
    __table_args__ = (
        Index("ix_matching_requests_customer_status", "customer_id", "matching_status"),
    )

    matching_request_id: Mapped[int] = mapped_column(
        BIGINT_PK, primary_key=True, autoincrement=True
    )
    customer_id: Mapped[int] = mapped_column(
        BIGINT_PK, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    estimate_id: Mapped[int | None] = mapped_column(BIGINT_PK)
    service_task_id: Mapped[int | None] = mapped_column(BIGINT_PK)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    region_code_id: Mapped[int | None] = mapped_column(BIGINT_PK)
    address: Mapped[str | None] = mapped_column(String(500))
    preferred_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    preferred_time_start: Mapped[str | None] = mapped_column(String(10))
    preferred_time_end: Mapped[str | None] = mapped_column(String(10))
    contact_time_text: Mapped[str | None] = mapped_column(String(100))
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    request_message: Mapped[str | None] = mapped_column(Text)
    privacy_settings_json: Mapped[dict | None] = mapped_column(JSON)
    is_emergency: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    matching_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="REQUESTED", server_default="REQUESTED"
    )
    matched_contractor_count: Mapped[int] = mapped_column(
        nullable=False, default=0, server_default="0"
    )
    selected_quote_id: Mapped[int | None] = mapped_column(BIGINT_PK)
    selected_contractor_id: Mapped[int | None] = mapped_column(BIGINT_PK)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    customer: Mapped["User"] = relationship()
    targets: Mapped[list["MatchingTarget"]] = relationship(
        back_populates="matching_request", cascade="all, delete-orphan"
    )
    quotes: Mapped[list["Quote"]] = relationship(
        back_populates="matching_request", cascade="all, delete-orphan"
    )
    work_order: Mapped["WorkOrder | None"] = relationship(
        back_populates="matching_request", uselist=False
    )
