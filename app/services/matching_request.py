from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ContractorProfile, MatchingRequest, MatchingTarget, Quote, User, WorkOrder
from app.schemas.matching_request import (
    MatchingRequestCancel,
    MatchingRequestCreate,
    MatchingRequestDetail,
    MatchingRequestSummary,
)
from app.services.matching_common import pagination, require_customer

MATCHING_REQUEST_EXPIRE_DAYS = 7
MATCHING_CANCELABLE_STATUSES = {"REQUESTED", "RECEIVING_QUOTES"}


async def _find_candidate_contractors(db: AsyncSession, limit: int = 10) -> list[int]:
    result = await db.execute(
        select(ContractorProfile.contractor_id)
        .where(
            ContractorProfile.approval_status == "APPROVED",
            ContractorProfile.available_status == "AVAILABLE",
            ContractorProfile.matching_alert_enabled.is_(True),
        )
        .order_by(ContractorProfile.rating_avg.desc(), ContractorProfile.review_count.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_matching_request(
    db: AsyncSession,
    current_user: User,
    payload: MatchingRequestCreate,
) -> MatchingRequest:
    require_customer(current_user)
    now = datetime.now(timezone.utc)
    try:
        contractor_ids = await _find_candidate_contractors(db)
        matching_request = MatchingRequest(
            user_id=current_user.user_id,
            estimate_id=payload.estimate_id,
            service_task_id=payload.service_task_id,
            title=payload.title.strip(),
            region_code_id=payload.region_code_id,
            address=payload.address,
            preferred_date=payload.preferred_date,
            preferred_time_start=payload.preferred_time_start,
            preferred_time_end=payload.preferred_time_end,
            contact_time_text=payload.contact_time_text,
            budget_min=payload.budget_min,
            budget_max=payload.budget_max,
            request_message=payload.request_message,
            privacy_settings_json=payload.privacy_settings,
            is_emergency=payload.is_emergency,
            matching_status="REQUESTED",
            matched_contractor_count=len(contractor_ids),
            expires_at=now + timedelta(days=MATCHING_REQUEST_EXPIRE_DAYS),
        )
        db.add(matching_request)
        await db.flush()
        db.add_all(
            [
                MatchingTarget(
                    matching_request_id=matching_request.matching_request_id,
                    contractor_id=contractor_id,
                    target_status="NOTIFIED",
                    notified_at=now,
                )
                for contractor_id in contractor_ids
            ]
        )
        await db.commit()
        await db.refresh(matching_request)
        return matching_request
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Matching request could not be created") from exc


def summary_from_request(
    request: MatchingRequest,
    quote_count: int = 0,
    work_order_id: int | None = None,
) -> MatchingRequestSummary:
    return MatchingRequestSummary(
        matching_request_id=request.matching_request_id,
        estimate_id=request.estimate_id,
        title=request.title,
        service_task_id=request.service_task_id,
        region_code_id=request.region_code_id,
        matching_status=request.matching_status,
        quote_count=quote_count,
        selected_contractor_id=request.selected_contractor_id,
        work_order_id=work_order_id,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


async def list_customer_matching_requests(
    db: AsyncSession,
    current_user: User,
    status_filter: str | None,
    page: int,
    size: int,
) -> tuple[list[MatchingRequestSummary], int, int, int]:
    require_customer(current_user)
    page, size = pagination(page, size)
    filters = [MatchingRequest.user_id == current_user.user_id]
    if status_filter:
        filters.append(MatchingRequest.matching_status == status_filter)

    total = await db.scalar(select(func.count()).select_from(MatchingRequest).where(*filters))
    result = await db.execute(
        select(
            MatchingRequest,
            func.count(Quote.quote_id).label("quote_count"),
            WorkOrder.work_order_id,
        )
        .outerjoin(Quote, Quote.matching_request_id == MatchingRequest.matching_request_id)
        .outerjoin(WorkOrder, WorkOrder.matching_request_id == MatchingRequest.matching_request_id)
        .where(*filters)
        .group_by(MatchingRequest.matching_request_id, WorkOrder.work_order_id)
        .order_by(MatchingRequest.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [
        summary_from_request(request, quote_count, work_order_id)
        for request, quote_count, work_order_id in result.all()
    ]
    return items, page, size, int(total or 0)


async def get_matching_request_detail(
    db: AsyncSession,
    current_user: User,
    matching_request_id: int,
) -> MatchingRequestDetail:
    result = await db.execute(
        select(
            MatchingRequest,
            func.count(Quote.quote_id).label("quote_count"),
            WorkOrder.work_order_id,
        )
        .outerjoin(Quote, Quote.matching_request_id == MatchingRequest.matching_request_id)
        .outerjoin(WorkOrder, WorkOrder.matching_request_id == MatchingRequest.matching_request_id)
        .where(MatchingRequest.matching_request_id == matching_request_id)
        .group_by(MatchingRequest.matching_request_id, WorkOrder.work_order_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Matching request not found")

    request, quote_count, work_order_id = row
    if current_user.user_type == "CUSTOMER" and request.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Matching request not found")
    if current_user.user_type == "CONTRACTOR":
        allowed = await db.scalar(
            select(MatchingTarget.matching_target_id).where(
                MatchingTarget.matching_request_id == matching_request_id,
                MatchingTarget.contractor_id == current_user.user_id,
            )
        )
        if allowed is None:
            raise HTTPException(status_code=404, detail="Matching request not found")
    if current_user.user_type not in {"CUSTOMER", "CONTRACTOR"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    summary = summary_from_request(request, quote_count, work_order_id)
    return MatchingRequestDetail(
        **summary.model_dump(),
        user_id=request.user_id,
        address=request.address,
        preferred_date=request.preferred_date,
        preferred_time_start=request.preferred_time_start,
        preferred_time_end=request.preferred_time_end,
        contact_time_text=request.contact_time_text,
        budget_min=request.budget_min,
        budget_max=request.budget_max,
        request_message=request.request_message,
        privacy_settings=request.privacy_settings_json,
        is_emergency=request.is_emergency,
        matched_contractor_count=request.matched_contractor_count,
        expires_at=request.expires_at,
    )


async def delete_matching_request(
    db: AsyncSession,
    current_user: User,
    matching_request_id: int,
) -> int:
    require_customer(current_user)
    result = await db.execute(
        select(MatchingRequest)
        .where(
            MatchingRequest.matching_request_id == matching_request_id,
            MatchingRequest.user_id == current_user.user_id,
            MatchingRequest.matching_status == "REQUESTED",
        )
        .with_for_update()
    )
    matching_request = result.scalar_one_or_none()
    if matching_request is None:
        raise HTTPException(status_code=404, detail="Deletable matching request not found")

    quote_count = await db.scalar(
        select(func.count())
        .select_from(Quote)
        .where(Quote.matching_request_id == matching_request_id)
    )
    work_order_count = await db.scalar(
        select(func.count())
        .select_from(WorkOrder)
        .where(WorkOrder.matching_request_id == matching_request_id)
    )
    if quote_count or work_order_count:
        raise HTTPException(status_code=409, detail="Matching request is already in progress")

    await db.delete(matching_request)
    await db.commit()
    return matching_request_id


async def cancel_matching_request(
    db: AsyncSession,
    current_user: User,
    matching_request_id: int,
    payload: MatchingRequestCancel,
) -> MatchingRequest:
    require_customer(current_user)
    result = await db.execute(
        select(MatchingRequest)
        .where(
            MatchingRequest.matching_request_id == matching_request_id,
            MatchingRequest.user_id == current_user.user_id,
            MatchingRequest.matching_status.in_(MATCHING_CANCELABLE_STATUSES),
        )
        .with_for_update()
    )
    matching_request = result.scalar_one_or_none()
    if matching_request is None:
        raise HTTPException(status_code=404, detail="Cancelable matching request not found")

    work_order_id = await db.scalar(
        select(WorkOrder.work_order_id).where(
            WorkOrder.matching_request_id == matching_request_id
        )
    )
    if work_order_id is not None:
        raise HTTPException(status_code=409, detail="Matching request already has a work order")

    matching_request.matching_status = "CANCELLED"
    matching_request.cancel_reason = payload.cancel_reason
    await db.commit()
    await db.refresh(matching_request)
    return matching_request
