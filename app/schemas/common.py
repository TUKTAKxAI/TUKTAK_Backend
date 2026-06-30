from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PageResponse(BaseModel):
    page: int
    size: int
    total: int


class UserMe(BaseModel):
    user_id: int
    email: str
    nickname: str
    name: str
    phone: str | None = None
    profile_image_url: str | None = None
    user_type: str
    account_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserMeResponse(BaseModel):
    success: bool = True
    user: UserMe


class UserUpdateResponse(BaseModel):
    success: bool = True
    user: dict[str, Any]


class ReferenceCodeItem(BaseModel):
    code_id: int
    code: str
    code_name: str
    parent_code_id: int | None = None
    metadata_json: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class ReferenceCodeListResponse(BaseModel):
    success: bool = True
    codes: list[ReferenceCodeItem]


class ServiceTaskItem(BaseModel):
    service_task_id: int
    parent_task_id: int | None = None
    task_code: str
    task_name: str
    main_category: str
    requires_license: bool

    model_config = ConfigDict(from_attributes=True)


class ServiceTaskListResponse(BaseModel):
    success: bool = True
    tasks: list[ServiceTaskItem]


class AiEstimateCreateResponse(BaseModel):
    success: bool = True
    estimate_id: int
    estimate_status: str
    created_at: datetime


class AiEstimateDetail(BaseModel):
    estimate_id: int
    description: str
    image_urls: list[str] | None = None
    main_category: str
    object_label: str
    problem_label: str
    repair_task_name: str
    severity: str
    min_price: Decimal
    max_price: Decimal
    estimated_minutes_min: int
    estimated_minutes_max: int
    confidence_score: Decimal
    ai_summary: str | None = None
    estimate_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AiEstimateDetailResponse(BaseModel):
    success: bool = True
    estimate: AiEstimateDetail


class AiEstimateListItem(BaseModel):
    estimate_id: int
    main_category: str
    repair_task_name: str
    min_price: Decimal
    max_price: Decimal
    confidence_score: Decimal
    estimate_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AiEstimateListResponse(PageResponse):
    success: bool = True
    items: list[AiEstimateListItem]


class AiEstimateRetryResponse(BaseModel):
    success: bool = True
    estimate_id: int
    estimate_status: str
    updated_at: datetime


class RagDocumentCreateResponse(BaseModel):
    success: bool = True
    document_id: int
    document_status: str
    created_at: datetime


class RagDocumentListItem(BaseModel):
    document_id: int
    title: str
    document_type: str
    source_name: str
    document_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RagDocumentListResponse(PageResponse):
    success: bool = True
    items: list[RagDocumentListItem]


class RagDocumentDetail(BaseModel):
    document_id: int
    title: str
    document_type: str
    source_name: str
    source_url: str | None = None
    published_date: date | None = None
    effective_date: date | None = None
    version: str | None = None
    file_url: str | None = None
    document_status: str
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RagDocumentDetailResponse(BaseModel):
    success: bool = True
    document: RagDocumentDetail


class IdStatusResponse(BaseModel):
    success: bool = True
    document_id: int | None = None
    document_status: str | None = None
    updated_at: datetime | None = None


class QuoteCreateRequest(BaseModel):
    total_amount: Decimal
    work_scope: str
    quote_items: list[dict[str, Any]]
    included_items: list[dict[str, Any]] | None = None
    excluded_items: list[dict[str, Any]] | None = None
    estimated_minutes: int | None = None
    visit_count: int = 1
    available_date: date
    arrival_time: time | None = None
    as_period_days: int | None = None
    valid_until: datetime
    additional_note: str | None = None


class QuoteCreateResponse(BaseModel):
    success: bool = True
    quote_id: int
    quote_status: str
    sent_at: datetime


class QuoteDetailResponse(BaseModel):
    success: bool = True
    quote: dict[str, Any]


class QuoteListResponse(PageResponse):
    success: bool = True
    items: list[dict[str, Any]]


class WorkOrderDetailResponse(BaseModel):
    success: bool = True
    work_order: dict[str, Any]


class NotificationListResponse(PageResponse):
    success: bool = True
    unread_count: int
    items: list[dict[str, Any]]


class NotificationReadResponse(BaseModel):
    success: bool = True
    notification_id: int
    is_read: bool
    read_at: datetime


class ReviewCreateRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    quality_rating: int | None = Field(None, ge=1, le=5)
    price_rating: int | None = Field(None, ge=1, le=5)
    punctuality_rating: int | None = Field(None, ge=1, le=5)
    kindness_rating: int | None = Field(None, ge=1, le=5)
    as_rating: int | None = Field(None, ge=1, le=5)
    review_text: str


class ReviewUpdateRequest(BaseModel):
    rating: int | None = Field(None, ge=1, le=5)
    quality_rating: int | None = Field(None, ge=1, le=5)
    price_rating: int | None = Field(None, ge=1, le=5)
    punctuality_rating: int | None = Field(None, ge=1, le=5)
    kindness_rating: int | None = Field(None, ge=1, le=5)
    as_rating: int | None = Field(None, ge=1, le=5)
    review_text: str | None = None


class ReviewCreateResponse(BaseModel):
    success: bool = True
    review_id: int
    review_status: str
    created_at: datetime


class ReviewListResponse(PageResponse):
    success: bool = True
    rating_avg: Decimal | None = None
    review_count: int | None = None
    items: list[dict[str, Any]]


class ReviewUpdateResponse(BaseModel):
    success: bool = True
    review_id: int
    updated_at: datetime


class ReviewDeleteResponse(BaseModel):
    success: bool = True
    review_id: int
    is_visible: bool
    deleted_at: datetime
