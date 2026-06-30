from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import BIGINT_PK


class MatchingTarget(Base):
    __tablename__ = "matching_targets"
    __table_args__ = (
        Index("ix_matching_targets_contractor_status", "contractor_id", "target_status"),
    )

    matching_target_id: Mapped[int] = mapped_column(
        BIGINT_PK, primary_key=True, autoincrement=True
    )
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
    target_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="NOTIFIED", server_default="NOTIFIED"
    )
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    declined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    declined_reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    matching_request: Mapped["MatchingRequest"] = relationship(back_populates="targets")
    contractor: Mapped["ContractorProfile"] = relationship()
