from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationReadAllResponse,
    NotificationReadResponse,
)
from app.services import notification as notification_service

router = APIRouter(prefix="/notifications", tags=["Notification"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    items, page, size, total, unread_count = await notification_service.list_notifications(
        db, current_user, unread_only, page, size
    )
    return NotificationListResponse(
        items=items, page=page, size=size, total=total, unread_count=unread_count
    )


@router.patch("/{notification_id}/read", response_model=NotificationReadResponse)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationReadResponse:
    notification = await notification_service.mark_notification_read(
        db, current_user, notification_id
    )
    return NotificationReadResponse(
        notification_id=notification.notification_id,
        is_read=notification.is_read,
        read_at=notification.read_at,
    )


@router.patch("/read-all", response_model=NotificationReadAllResponse)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationReadAllResponse:
    updated_count = await notification_service.mark_all_notifications_read(db, current_user)
    return NotificationReadAllResponse(updated_count=updated_count)
