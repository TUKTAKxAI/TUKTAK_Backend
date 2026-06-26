from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ContractorProfile, MatchingRequest, User, WorkOrder
from app.schemas.work_order import (
    WorkOrderCancel,
    WorkOrderDetail,
    WorkOrderScheduleUpdate,
    WorkOrderSummary,
)
from app.services.matching_common import pagination

WORK_ORDER_CANCELABLE_STATUSES = {"CREATED", "SCHEDULED"}
WORK_ORDER_SCHEDULABLE_STATUSES = {"CREATED", "SCHEDULED"}
WORK_ORDER_STARTABLE_STATUSES = {"CREATED", "SCHEDULED"}
WORK_ORDER_COMPLETABLE_STATUSES = {"IN_PROGRESS"}


def _has_work_order_access(user: User, work_order: WorkOrder) -> bool:
    return (
        user.user_type == "CUSTOMER"
        and work_order.customer_id == user.user_id
    ) or (
        user.user_type == "CONTRACTOR"
        and work_order.contractor_id == user.user_id
    )


def _require_contractor_owner(user: User, work_order: WorkOrder) -> None:
    if user.user_type != "CONTRACTOR" or work_order.contractor_id != user.user_id:
        raise HTTPException(status_code=403, detail="Contractor account required")


def _summary_from_row(
    work_order: WorkOrder,
    matching_request_title: str,
    contractor_name: str | None,
) -> WorkOrderSummary:
    return WorkOrderSummary(
        work_order_id=work_order.work_order_id,
        matching_request_id=work_order.matching_request_id,
        matching_request_title=matching_request_title,
        quote_id=work_order.quote_id,
        customer_id=work_order.customer_id,
        contractor_id=work_order.contractor_id,
        contractor_name=contractor_name,
        work_order_status=work_order.work_order_status,
        scheduled_date=work_order.scheduled_date,
        final_amount=work_order.final_amount,
        created_at=work_order.created_at,
        updated_at=work_order.updated_at,
    )


def _detail_from_row(
    work_order: WorkOrder,
    matching_request_title: str,
    customer_name: str,
    contractor_name: str | None,
) -> WorkOrderDetail:
    return WorkOrderDetail(
        work_order_id=work_order.work_order_id,
        matching_request_id=work_order.matching_request_id,
        matching_request_title=matching_request_title,
        quote_id=work_order.quote_id,
        customer_id=work_order.customer_id,
        customer_name=customer_name,
        contractor_id=work_order.contractor_id,
        contractor_name=contractor_name,
        work_order_status=work_order.work_order_status,
        scheduled_date=work_order.scheduled_date,
        scheduled_start_time=work_order.scheduled_start_time,
        scheduled_end_time=work_order.scheduled_end_time,
        final_amount=work_order.final_amount,
        contact_revealed_at=work_order.contact_revealed_at,
        started_at=work_order.started_at,
        completed_at=work_order.completed_at,
        cancelled_at=work_order.cancelled_at,
        cancel_reason=work_order.cancel_reason,
        customer_confirmed_at=work_order.customer_confirmed_at,
        contractor_confirmed_at=work_order.contractor_confirmed_at,
        can_review=work_order.work_order_status == "COMPLETED",
        created_at=work_order.created_at,
        updated_at=work_order.updated_at,
    )


async def list_work_orders(
    db: AsyncSession,
    current_user: User,
    status_filter: str | None,
    page: int,
    size: int,
) -> tuple[list[WorkOrderSummary], int, int, int]:
    page, size = pagination(page, size)
    filters = []
    if current_user.user_type == "CUSTOMER":
        filters.append(WorkOrder.customer_id == current_user.user_id)
    elif current_user.user_type == "CONTRACTOR":
        filters.append(WorkOrder.contractor_id == current_user.user_id)
    else:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if status_filter:
        filters.append(WorkOrder.work_order_status == status_filter)

    total = await db.scalar(select(func.count()).select_from(WorkOrder).where(*filters))
    result = await db.execute(
        select(WorkOrder, MatchingRequest.title, ContractorProfile.business_name)
        .join(
            MatchingRequest,
            MatchingRequest.matching_request_id == WorkOrder.matching_request_id,
        )
        .join(
            ContractorProfile,
            ContractorProfile.contractor_id == WorkOrder.contractor_id,
        )
        .where(*filters)
        .order_by(WorkOrder.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [
        _summary_from_row(work_order, matching_request_title, contractor_name)
        for work_order, matching_request_title, contractor_name in result.all()
    ]
    return items, page, size, int(total or 0)


async def get_work_order_detail(
    db: AsyncSession,
    current_user: User,
    work_order_id: int,
) -> WorkOrderDetail:
    result = await db.execute(
        select(
            WorkOrder,
            MatchingRequest.title,
            User.name,
            ContractorProfile.business_name,
        )
        .join(
            MatchingRequest,
            MatchingRequest.matching_request_id == WorkOrder.matching_request_id,
        )
        .join(User, User.user_id == WorkOrder.customer_id)
        .join(
            ContractorProfile,
            ContractorProfile.contractor_id == WorkOrder.contractor_id,
        )
        .where(WorkOrder.work_order_id == work_order_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Work order not found")

    work_order, matching_request_title, customer_name, contractor_name = row
    if not _has_work_order_access(current_user, work_order):
        raise HTTPException(status_code=404, detail="Work order not found")

    return _detail_from_row(
        work_order,
        matching_request_title,
        customer_name,
        contractor_name,
    )


async def _get_owned_work_order_for_update(
    db: AsyncSession,
    current_user: User,
    work_order_id: int,
) -> WorkOrder:
    result = await db.execute(
        select(WorkOrder)
        .where(WorkOrder.work_order_id == work_order_id)
        .with_for_update()
    )
    work_order = result.scalar_one_or_none()
    if work_order is None or not _has_work_order_access(current_user, work_order):
        raise HTTPException(status_code=404, detail="Work order not found")
    return work_order


async def update_work_order_schedule(
    db: AsyncSession,
    current_user: User,
    work_order_id: int,
    payload: WorkOrderScheduleUpdate,
) -> WorkOrder:
    work_order = await _get_owned_work_order_for_update(db, current_user, work_order_id)
    if work_order.work_order_status not in WORK_ORDER_SCHEDULABLE_STATUSES:
        raise HTTPException(status_code=409, detail="Work order schedule cannot be changed")

    work_order.scheduled_date = payload.scheduled_date
    work_order.scheduled_start_time = payload.scheduled_start_time
    work_order.scheduled_end_time = payload.scheduled_end_time
    work_order.work_order_status = "SCHEDULED"
    await db.commit()
    await db.refresh(work_order)
    return work_order


async def start_work_order(
    db: AsyncSession,
    current_user: User,
    work_order_id: int,
) -> WorkOrder:
    work_order = await _get_owned_work_order_for_update(db, current_user, work_order_id)
    _require_contractor_owner(current_user, work_order)
    if work_order.work_order_status not in WORK_ORDER_STARTABLE_STATUSES:
        raise HTTPException(status_code=409, detail="Work order cannot be started")

    now = datetime.now(timezone.utc)
    work_order.work_order_status = "IN_PROGRESS"
    work_order.started_at = now
    if work_order.contact_revealed_at is None:
        work_order.contact_revealed_at = now
    await db.commit()
    await db.refresh(work_order)
    return work_order


async def complete_work_order(
    db: AsyncSession,
    current_user: User,
    work_order_id: int,
) -> WorkOrder:
    work_order = await _get_owned_work_order_for_update(db, current_user, work_order_id)
    _require_contractor_owner(current_user, work_order)
    if work_order.work_order_status not in WORK_ORDER_COMPLETABLE_STATUSES:
        raise HTTPException(status_code=409, detail="Work order cannot be completed")

    now = datetime.now(timezone.utc)
    work_order.work_order_status = "COMPLETED"
    work_order.completed_at = now
    work_order.contractor_confirmed_at = now
    await db.commit()
    await db.refresh(work_order)
    return work_order


async def confirm_work_order(
    db: AsyncSession,
    current_user: User,
    work_order_id: int,
) -> WorkOrder:
    work_order = await _get_owned_work_order_for_update(db, current_user, work_order_id)
    now = datetime.now(timezone.utc)
    if current_user.user_type == "CUSTOMER" and work_order.customer_id == current_user.user_id:
        work_order.customer_confirmed_at = now
    elif (
        current_user.user_type == "CONTRACTOR"
        and work_order.contractor_id == current_user.user_id
    ):
        work_order.contractor_confirmed_at = now
    else:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    if (
        work_order.work_order_status == "IN_PROGRESS"
        and work_order.customer_confirmed_at is not None
        and work_order.contractor_confirmed_at is not None
    ):
        work_order.work_order_status = "COMPLETED"
        work_order.completed_at = now
    await db.commit()
    await db.refresh(work_order)
    return work_order


async def cancel_work_order(
    db: AsyncSession,
    current_user: User,
    work_order_id: int,
    payload: WorkOrderCancel,
) -> WorkOrder:
    work_order = await _get_owned_work_order_for_update(db, current_user, work_order_id)
    if work_order.work_order_status not in WORK_ORDER_CANCELABLE_STATUSES:
        raise HTTPException(status_code=409, detail="Work order cannot be cancelled")

    work_order.work_order_status = "CANCELLED"
    work_order.cancel_reason = payload.cancel_reason
    work_order.cancelled_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(work_order)
    return work_order
