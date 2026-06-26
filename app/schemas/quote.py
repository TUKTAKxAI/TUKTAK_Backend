from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


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


class SelectQuoteResponse(BaseModel):
    success: bool = True
    matching_request_id: int
    selected_quote_id: int
    selected_contractor_id: int
    matching_status: str
    work_order_id: int
    created_at: datetime
