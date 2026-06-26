from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ContractorMatchingRequestSummary(BaseModel):
    matching_request_id: int
    matching_target_id: int
    title: str
    service_task_id: int | None
    region_code_id: int | None
    preferred_date: datetime | None
    budget_min: Decimal | None
    budget_max: Decimal | None
    matching_status: str
    target_status: str
    quote_id: int | None = None
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
