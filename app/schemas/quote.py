from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class QuoteCreate(BaseModel):
    total_amount: Decimal = Field(ge=0)
    work_scope: str = Field(min_length=1)
    quote_items: list | None = None
    included_items: str | None = None
    excluded_items: str | None = None
    estimated_minutes: int | None = Field(None, ge=1)
    visit_count: int | None = Field(None, ge=1)
    available_date: datetime | None = None
    arrival_time: str | None = Field(None, max_length=50)
    as_period_days: int | None = Field(None, ge=0)
    valid_until: datetime | None = None
    additional_note: str | None = None


class SelectQuoteRequest(BaseModel):
    quote_id: int


class QuoteSummary(BaseModel):
    quote_id: int
    matching_request_id: int
    contractor_id: int
    business_name: str | None = None
    quote_status: str
    total_amount: Decimal
    work_scope: str | None
    estimated_minutes: int | None
    visit_count: int | None
    available_date: datetime | None
    valid_until: datetime | None
    sent_at: datetime | None
    selected_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuoteListResponse(BaseModel):
    success: bool = True
    quotes: list[QuoteSummary]
    page: int
    size: int
    total: int


class ContractorQuoteSummary(BaseModel):
    quote_id: int
    matching_request_id: int
    matching_request_title: str
    matching_status: str
    quote_status: str
    total_amount: Decimal
    work_scope: str | None
    estimated_minutes: int | None
    visit_count: int | None
    available_date: datetime | None
    valid_until: datetime | None
    sent_at: datetime | None
    selected_at: datetime | None
    created_at: datetime


class QuoteDetail(BaseModel):
    quote_id: int
    matching_request_id: int
    matching_request_title: str
    contractor_id: int
    business_name: str | None = None
    quote_status: str
    total_amount: Decimal
    work_scope: str | None
    quote_items: list | None = None
    included_items: str | None
    excluded_items: str | None
    estimated_minutes: int | None
    visit_count: int | None
    available_date: datetime | None
    arrival_time: str | None
    as_period_days: int | None
    valid_until: datetime | None
    additional_note: str | None
    sent_at: datetime | None
    selected_at: datetime | None
    created_at: datetime
    updated_at: datetime


class QuoteDetailResponse(BaseModel):
    success: bool = True
    quote: QuoteDetail


class ContractorQuoteListResponse(BaseModel):
    success: bool = True
    items: list[ContractorQuoteSummary]
    page: int
    size: int
    total: int


class QuoteCreateResponse(BaseModel):
    success: bool = True
    quote_id: int
    matching_request_id: int
    contractor_id: int
    quote_status: str
    total_amount: Decimal
    sent_at: datetime | None
    created_at: datetime


class SelectQuoteResponse(BaseModel):
    success: bool = True
    matching_request_id: int
    selected_quote_id: int
    selected_contractor_id: int
    matching_status: str
    work_order_id: int
    created_at: datetime
