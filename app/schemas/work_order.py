from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class WorkOrderSummary(BaseModel):
    work_order_id: int
    matching_request_id: int
    matching_request_title: str
    quote_id: int
    customer_id: int
    contractor_id: int
    contractor_name: str | None = None
    work_order_status: str
    scheduled_date: datetime | None
    final_amount: Decimal
    created_at: datetime
    updated_at: datetime


class WorkOrderDetail(BaseModel):
    work_order_id: int
    matching_request_id: int
    matching_request_title: str
    quote_id: int
    customer_id: int
    customer_name: str
    contractor_id: int
    contractor_name: str | None = None
    work_order_status: str
    scheduled_date: datetime | None
    scheduled_start_time: str | None
    scheduled_end_time: str | None
    final_amount: Decimal
    contact_revealed_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancel_reason: str | None
    customer_confirmed_at: datetime | None
    contractor_confirmed_at: datetime | None
    can_review: bool = False
    created_at: datetime
    updated_at: datetime


class WorkOrderScheduleUpdate(BaseModel):
    scheduled_date: datetime | None = None
    scheduled_start_time: str | None = Field(None, max_length=10)
    scheduled_end_time: str | None = Field(None, max_length=10)


class WorkOrderCancel(BaseModel):
    cancel_reason: str | None = Field(None, max_length=500)


class WorkOrderListResponse(BaseModel):
    success: bool = True
    items: list[WorkOrderSummary]
    page: int
    size: int
    total: int


class WorkOrderDetailResponse(BaseModel):
    success: bool = True
    work_order: WorkOrderDetail


class WorkOrderStatusResponse(BaseModel):
    success: bool = True
    work_order_id: int
    work_order_status: str
    updated_at: datetime
