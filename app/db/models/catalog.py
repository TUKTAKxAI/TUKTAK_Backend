from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import BIGINT_PK


class Attachment(Base):
    __tablename__ = "attachments"

    attachment_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    owner_type: Mapped[str] = mapped_column(String(40), nullable=False)
    owner_id: Mapped[int] = mapped_column(BIGINT_PK, nullable=False)
    file_category: Mapped[str] = mapped_column(String(30), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BIGINT_PK, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    uploaded_by: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ReferenceCode(Base):
    __tablename__ = "reference_codes"
    __table_args__ = (UniqueConstraint("code_group", "code", name="uq_reference_code_group_code"),)

    code_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    code_group: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    code_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_code_id: Mapped[int | None] = mapped_column(BIGINT_PK, ForeignKey("reference_codes.code_id"))
    description: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ServiceTask(Base):
    __tablename__ = "service_tasks"

    service_task_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    parent_task_id: Mapped[int | None] = mapped_column(BIGINT_PK, ForeignKey("service_tasks.service_task_id"))
    task_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    task_name: Mapped[str] = mapped_column(String(100), nullable=False)
    main_category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    base_unit: Mapped[str | None] = mapped_column(String(30))
    requires_license: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class AiEstimate(Base):
    __tablename__ = "ai_estimates"

    estimate_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("users.user_id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    main_category: Mapped[str] = mapped_column(String(50), nullable=False)
    object_label: Mapped[str] = mapped_column(String(100), nullable=False)
    problem_label: Mapped[str] = mapped_column(String(100), nullable=False)
    repair_task_name: Mapped[str] = mapped_column(String(150), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    min_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    max_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    estimated_minutes_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    estimated_minutes_max: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=0, server_default="0")
    ai_summary: Mapped[str | None] = mapped_column(Text)
    estimate_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PROCESSING", server_default="PROCESSING")
    image_urls: Mapped[list[str] | None] = mapped_column(JSON)
    region_code_id: Mapped[int | None] = mapped_column(BIGINT_PK, ForeignKey("reference_codes.code_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class PricingRule(Base):
    __tablename__ = "pricing_rules"

    pricing_rule_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    service_task_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("service_tasks.service_task_id"), nullable=False)
    region_code_id: Mapped[int | None] = mapped_column(BIGINT_PK, ForeignKey("reference_codes.code_id"))
    rule_name: Mapped[str] = mapped_column(String(150), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(30), nullable=False)
    condition_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    base_min_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    base_max_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    adjustment_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    fixed_adjustment_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_by: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
