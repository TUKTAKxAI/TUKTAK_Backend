from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import BIGINT_PK

if TYPE_CHECKING:
    from app.db.models.user import User


class RiskReport(Base):
    __tablename__ = "risk_reports"
    __table_args__ = (
        Index("ix_risk_reports_user_status", "user_id", "report_status"),
        Index("ix_risk_reports_estimate", "estimate_id"),
    )

    risk_report_id: Mapped[int] = mapped_column(
        BIGINT_PK, primary_key=True, autoincrement=True
    )

    estimate_id: Mapped[int] = mapped_column(BIGINT_PK, nullable=False)

    user_id: Mapped[int] = mapped_column(
        BIGINT_PK,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    report_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PROCESSING",
        server_default="PROCESSING",
    )

    risk_score: Mapped[int | None] = mapped_column(Integer)
    risk_level: Mapped[str | None] = mapped_column(String(30))
    summary: Mapped[str | None] = mapped_column(Text)

    result_json: Mapped[dict | None] = mapped_column(JSON)
    sources_json: Mapped[list | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship()