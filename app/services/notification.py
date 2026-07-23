from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Notification, User
from app.schemas.notification import NotificationSummary
from app.services.matching_common import pagination


async def create_notification(
    db: AsyncSession,
    user_id: int,
    notification_type: str,
    title: str,
    content: str,
    target_type: str | None = None,
    target_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content,
        target_type=target_type,
        target_id=target_id,
        channel="IN_APP",
        delivery_status="SENT",
        sent_at=datetime.now(timezone.utc),
    )
    db.add(notification)
    return notification


async def list_notifications(
    db: AsyncSession,
    current_user: User,
    unread_only: bool,
    page: int,
    size: int,
) -> tuple[list[NotificationSummary], int, int, int, int]:
    page, size = pagination(page, size)
    filters = [Notification.user_id == current_user.user_id]
    if unread_only:
        filters.append(Notification.is_read.is_(False))

    total = await db.scalar(select(func.count()).select_from(Notification).where(*filters))
    unread_count = await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == current_user.user_id, Notification.is_read.is_(False))
    )
    result = await db.execute(
        select(Notification)
        .where(*filters)
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [NotificationSummary.model_validate(n) for n in result.scalars().all()]
    return items, page, size, int(total or 0), int(unread_count or 0)


async def mark_notification_read(
    db: AsyncSession,
    current_user: User,
    notification_id: int,
) -> Notification:
    result = await db.execute(
        select(Notification)
        .where(
            Notification.notification_id == notification_id,
            Notification.user_id == current_user.user_id,
        )
        .with_for_update()
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(notification)
    return notification


async def mark_all_notifications_read(
    db: AsyncSession,
    current_user: User,
) -> int:
    result = await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.user_id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return result.rowcount or 0
