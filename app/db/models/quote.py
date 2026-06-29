from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import BIGINT_PK


class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = (
        Index("ix_quotes_matching_request_status", "matching_request_id", "quote_status"),
    )

    quote_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    matching_request_id: Mapped[int] = mapped_column(
        BIGINT_PK,
        ForeignKey("matching_requests.matching_request_id", ondelete="CASCADE"),
        nullable=False,
    )
    contractor_id: Mapped[int] = mapped_column(
        BIGINT_PK,
        ForeignKey("contractor_profiles.contractor_id", ondelete="CASCADE"),
        nullable=False,
    )
    quote_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SENT", server_default="SENT"
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    work_scope: Mapped[str | None] = mapped_column(Text)
    quote_items_json: Mapped[list | None] = mapped_column(JSON)
    included_items: Mapped[str | None] = mapped_column(Text)
    excluded_items: Mapped[str | None] = mapped_column(Text)
    estimated_minutes: Mapped[int | None] = mapped_column()
    visit_count: Mapped[int | None] = mapped_column()
    available_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    arrival_time: Mapped[str | None] = mapped_column(String(50))
    as_period_days: Mapped[int | None] = mapped_column()
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    additional_note: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    selected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    matching_request: Mapped["MatchingRequest"] = relationship(back_populates="quotes")
    contractor: Mapped["ContractorProfile"] = relationship()
    work_order: Mapped["WorkOrder | None"] = relationship(back_populates="quote", uselist=False)
