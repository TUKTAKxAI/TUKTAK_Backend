from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MatchingRequestCreate(BaseModel):
    estimate_id: int | None = None
    service_task_id: int | None = None
    title: str = Field(min_length=1, max_length=150)
    region_code_id: int | None = None
    address: str | None = Field(None, max_length=500)
    preferred_date: datetime | None = None
    preferred_time_start: str | None = Field(None, max_length=10)
    preferred_time_end: str | None = Field(None, max_length=10)
    contact_time_text: str | None = Field(None, max_length=100)
    budget_min: Decimal | None = Field(None, ge=0)
    budget_max: Decimal | None = Field(None, ge=0)
    request_message: str | None = None
    privacy_settings: dict | None = None
    is_emergency: bool = False

    @model_validator(mode="after")
    def validate_budget_range(self) -> "MatchingRequestCreate":
        if (
            self.budget_min is not None
            and self.budget_max is not None
            and self.budget_min > self.budget_max
        ):
            raise ValueError("budget_min must be less than or equal to budget_max")
        return self


class MatchingRequestSummary(BaseModel):
    matching_request_id: int
    estimate_id: int | None
    title: str
    service_task_id: int | None
    region_code_id: int | None
    matching_status: str
    quote_count: int = 0
    selected_contractor_id: int | None
    work_order_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchingRequestDetail(MatchingRequestSummary):
    customer_id: int
    address: str | None
    preferred_date: datetime | None
    preferred_time_start: str | None
    preferred_time_end: str | None
    contact_time_text: str | None
    budget_min: Decimal | None
    budget_max: Decimal | None
    request_message: str | None
    privacy_settings: dict | None
    is_emergency: bool
    matched_contractor_count: int
    expires_at: datetime | None


class MatchingRequestCreateResponse(BaseModel):
    success: bool = True
    matching_request_id: int
    matching_status: str
    matched_contractor_count: int
    expires_at: datetime | None
    created_at: datetime


class MatchingRequestListResponse(BaseModel):
    success: bool = True
    items: list[MatchingRequestSummary]
    page: int
    size: int
    total: int


class MatchingRequestDetailResponse(BaseModel):
    success: bool = True
    request: MatchingRequestDetail
