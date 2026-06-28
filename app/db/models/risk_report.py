from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import BIGINT_PK


class RiskReport(Base):
    __tablename__ = "risk_reports"
    __table_args__ = (
        Index("ix_risk_reports_user_status", "user_id", "report_status"),
        Index("ix_risk_reports_estimate", "estimate_id"),
    )

    risk_report_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    estimate_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("ai_estimates.estimate_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    report_status: Mapped[str] = mapped_column(String(30), nullable=False, default="PROCESSING", server_default="PROCESSING")
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="LOW", server_default="LOW")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    risk_items_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    checklist_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    additional_cost_risks_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    safety_risks_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    contract_risks_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    field_variable_risks_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default="pending", server_default="pending")
    model_version: Mapped[str | None] = mapped_column(String(50))
    failure_reason: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship()
