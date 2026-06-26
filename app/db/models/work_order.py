from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import BIGINT_PK


class WorkOrder(Base):
    __tablename__ = "work_orders"

    work_order_id: Mapped[int] = mapped_column(
        BIGINT_PK, primary_key=True, autoincrement=True
    )
    matching_request_id: Mapped[int] = mapped_column(
        BIGINT_PK,
        ForeignKey("matching_requests.matching_request_id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    quote_id: Mapped[int] = mapped_column(
        BIGINT_PK, ForeignKey("quotes.quote_id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    customer_id: Mapped[int] = mapped_column(
        BIGINT_PK, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False
    )
    contractor_id: Mapped[int] = mapped_column(
        BIGINT_PK,
        ForeignKey("contractor_profiles.contractor_id", ondelete="RESTRICT"),
        nullable=False,
    )
    work_order_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="CREATED", server_default="CREATED"
    )
    final_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    scheduled_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scheduled_start_time: Mapped[str | None] = mapped_column(String(10))
    scheduled_end_time: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    matching_request: Mapped["MatchingRequest"] = relationship(back_populates="work_order")
    quote: Mapped["Quote"] = relationship(back_populates="work_order")
    customer: Mapped["User"] = relationship()
    contractor: Mapped["ContractorProfile"] = relationship()
