from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.types import BIGINT_PK


class RagDocument(Base):
    __tablename__ = "rag_documents"

    document_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_name: Mapped[str] = mapped_column(String(150), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    published_date: Mapped[date | None] = mapped_column(Date)
    effective_date: Mapped[date | None] = mapped_column(Date)
    version: Mapped[str | None] = mapped_column(String(50))
    file_attachment_id: Mapped[int | None] = mapped_column(BIGINT_PK, ForeignKey("attachments.attachment_id"))
    content_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    document_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PROCESSING", server_default="PROCESSING")
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_by: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class RagDocumentChunk(Base):
    __tablename__ = "rag_document_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_rag_document_chunk_index"),)

    chunk_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("rag_documents.document_id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    section_title: Mapped[str | None] = mapped_column(String(255))
    page_number: Mapped[int | None] = mapped_column(Integer)
    vector_collection: Mapped[str] = mapped_column(String(100), nullable=False)
    vector_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RiskReportSource(Base):
    __tablename__ = "risk_report_sources"

    report_source_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    risk_report_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("risk_reports.risk_report_id"), nullable=False)
    document_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("rag_documents.document_id"), nullable=False)
    chunk_id: Mapped[int | None] = mapped_column(BIGINT_PK, ForeignKey("rag_document_chunks.chunk_id"))
    risk_category: Mapped[str] = mapped_column(String(50), nullable=False)
    citation_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    relevance_score: Mapped[Decimal | None] = mapped_column(Numeric(7, 6))
    quoted_summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class MatchingRequest(Base):
    __tablename__ = "matching_requests"

    matching_request_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("users.user_id"), nullable=False)
    estimate_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("ai_estimates.estimate_id"), nullable=False)
    risk_report_id: Mapped[int | None] = mapped_column(BIGINT_PK, ForeignKey("risk_reports.risk_report_id"))
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    service_task_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("service_tasks.service_task_id"), nullable=False)
    address_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    region_code_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("reference_codes.code_id"), nullable=False)
    preferred_date: Mapped[date] = mapped_column(Date, nullable=False)
    preferred_time_start: Mapped[time | None] = mapped_column(Time)
    preferred_time_end: Mapped[time | None] = mapped_column(Time)
    contact_time_text: Mapped[str | None] = mapped_column(String(100))
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    request_message: Mapped[str | None] = mapped_column(Text)
    privacy_settings_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    matching_status: Mapped[str] = mapped_column(String(30), nullable=False, default="REQUESTED", server_default="REQUESTED")
    is_emergency: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    max_contractor_count: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default="5")
    selected_quote_id: Mapped[int | None] = mapped_column(BIGINT_PK)
    selected_contractor_id: Mapped[int | None] = mapped_column(BIGINT_PK, ForeignKey("contractor_profiles.contractor_id"))
    selected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(String(500))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class MatchingTarget(Base):
    __tablename__ = "matching_targets"
    __table_args__ = (UniqueConstraint("matching_request_id", "contractor_id", name="uq_matching_target_contractor"),)

    matching_target_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    matching_request_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("matching_requests.matching_request_id"), nullable=False)
    contractor_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("contractor_profiles.contractor_id"), nullable=False)
    target_status: Mapped[str] = mapped_column(String(30), nullable=False, default="SENT", server_default="SENT")
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(7, 4))
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    declined_reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ContractorQuote(Base):
    __tablename__ = "contractor_quotes"

    quote_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    matching_request_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("matching_requests.matching_request_id"), nullable=False)
    matching_target_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("matching_targets.matching_target_id"), nullable=False)
    contractor_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("contractor_profiles.contractor_id"), nullable=False)
    quote_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    parent_quote_id: Mapped[int | None] = mapped_column(BIGINT_PK, ForeignKey("contractor_quotes.quote_id"))
    quote_status: Mapped[str] = mapped_column(String(30), nullable=False, default="SENT", server_default="SENT")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    work_scope: Mapped[str] = mapped_column(Text, nullable=False)
    quote_items_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    included_items_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    excluded_items_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer)
    visit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    available_date: Mapped[date] = mapped_column(Date, nullable=False)
    arrival_time: Mapped[time | None] = mapped_column(Time)
    as_period_days: Mapped[int | None] = mapped_column(Integer)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    additional_note: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    selected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class WorkOrder(Base):
    __tablename__ = "work_orders"

    work_order_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    matching_request_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("matching_requests.matching_request_id"), unique=True, nullable=False)
    quote_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("contractor_quotes.quote_id"), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("users.user_id"), nullable=False)
    contractor_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("contractor_profiles.contractor_id"), nullable=False)
    work_status: Mapped[str] = mapped_column(String(30), nullable=False, default="SCHEDULED", server_default="SCHEDULED")
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_start_time: Mapped[time | None] = mapped_column(Time)
    scheduled_end_time: Mapped[time | None] = mapped_column(Time)
    final_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    contact_revealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(String(500))
    customer_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    contractor_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Review(Base):
    __tablename__ = "reviews"

    review_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    work_order_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("work_orders.work_order_id"), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("users.user_id"), nullable=False)
    contractor_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("contractor_profiles.contractor_id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    quality_rating: Mapped[int | None] = mapped_column(Integer)
    price_rating: Mapped[int | None] = mapped_column(Integer)
    punctuality_rating: Mapped[int | None] = mapped_column(Integer)
    kindness_rating: Mapped[int | None] = mapped_column(Integer)
    as_rating: Mapped[int | None] = mapped_column(Integer)
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    contractor_reply: Mapped[str | None] = mapped_column(Text)
    contractor_replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PUBLIC", server_default="PUBLIC")
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Notification(Base):
    __tablename__ = "notifications"

    notification_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey("users.user_id"), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(40))
    target_id: Mapped[int | None] = mapped_column(BIGINT_PK)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="IN_APP", server_default="IN_APP")
    delivery_status: Mapped[str] = mapped_column(String(20), nullable=False, default="SENT", server_default="SENT")
    provider_message_id: Mapped[str | None] = mapped_column(String(255))
    failure_reason: Mapped[str | None] = mapped_column(String(1000))
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

