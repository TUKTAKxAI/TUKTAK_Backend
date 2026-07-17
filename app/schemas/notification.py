from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PageResponse


class NotificationSummary(BaseModel):
    notification_id: int
    notification_type: str
    title: str
    content: str
    target_type: str | None = None
    target_id: int | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(PageResponse):
    success: bool = True
    unread_count: int
    items: list[NotificationSummary]


class NotificationReadResponse(BaseModel):
    success: bool = True
    notification_id: int
    is_read: bool
    read_at: datetime


class NotificationReadAllResponse(BaseModel):
    success: bool = True
    updated_count: int
