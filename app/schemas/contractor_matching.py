from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ContractorMatchingRequestSummary(BaseModel):
    matching_request_id: int
    matching_target_id: int
    title: str
    service_task_id: int | None
    service_task_name: str | None = None
    region_code_id: int | None
    region_name: str | None = None
    address: str | None = None
    preferred_date: datetime | None
    preferred_time_start: str | None = None
    preferred_time_end: str | None = None
    budget_min: Decimal | None
    budget_max: Decimal | None
    request_message: str | None = None
    matching_status: str
    target_status: str
    quote_id: int | None = None
    estimate_id: int | None = None
    estimate_description: str | None = None
    estimate_image_urls: list[str] = Field(default_factory=list)
    estimate_main_category: str | None = None
    estimate_object_label: str | None = None
    estimate_problem_label: str | None = None
    estimate_repair_task_name: str | None = None
    estimate_severity: str | None = None
    estimate_min_price: Decimal | None = None
    estimate_max_price: Decimal | None = None
    estimate_minutes_min: int | None = None
    estimate_minutes_max: int | None = None
    estimate_confidence_score: Decimal | None = None
    estimate_ai_summary: str | None = None
    created_at: datetime


class ContractorMatchingRequestListResponse(BaseModel):
    success: bool = True
    items: list[ContractorMatchingRequestSummary]
    page: int
    size: int
    total: int


class ContractorMatchingDecline(BaseModel):
    declined_reason: str | None = Field(None, max_length=500)


class ContractorMatchingDeclineResponse(BaseModel):
    success: bool = True
    matching_request_id: int
    matching_target_id: int
    target_status: str
    declined_at: datetime
