from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import BIGINT_PK


class ContractorProfile(Base):
    __tablename__ = "contractor_profiles"

    contractor_id: Mapped[int] = mapped_column(
        BIGINT_PK,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    business_name: Mapped[str] = mapped_column(String(100), nullable=False)
    representative_name: Mapped[str] = mapped_column(String(50), nullable=False)
    business_number: Mapped[str | None] = mapped_column(String(20), unique=True)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    introduction: Mapped[str | None] = mapped_column(Text)
    business_status: Mapped[str] = mapped_column(String(20), nullable=False)
    approval_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", server_default="PENDING"
    )
    document_status_json: Mapped[dict | None] = mapped_column(JSON)
    service_radius_km: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    rating_avg: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=0, server_default="0"
    )
    review_count: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    matching_alert_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    available_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="AVAILABLE", server_default="AVAILABLE"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="contractor_profile")
    services: Mapped[List["ContractorService"]] = relationship("ContractorService", back_populates="profile")