from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AiEstimate,
    ContractorProfile,
    ContractorService,
    MatchingRequest,
    MatchingTarget,
    Quote,
    ReferenceCode,
    User,
    WorkOrder,
)
from app.schemas.matching_request import (
    MatchingRequestCancel,
    MatchingRequestCreate,
    MatchingRequestDetail,
    MatchingRequestSummary,
)
from app.services.matching_common import CONTRACTOR_ROLES, CUSTOMER_ROLES, pagination, require_customer
from app.services.notification import create_notification

MATCHING_REQUEST_EXPIRE_DAYS = 7
MATCHING_CANCELABLE_STATUSES = {"REQUESTED", "RECEIVING_QUOTES"}
ACTIVE_MATCHING_STATUSES = {"REQUESTED", "RECEIVING_QUOTES"}


async def _resolve_region_code_id(db: AsyncSession, raw_region_code_id: int | None) -> int | None:
    if raw_region_code_id is None:
        return None

    direct_code_id = await db.scalar(
        select(ReferenceCode.code_id).where(
            ReferenceCode.code_group == "REGION",
            ReferenceCode.code_id == raw_region_code_id,
            ReferenceCode.is_active.is_(True),
        )
    )
    if direct_code_id is not None:
        return direct_code_id

    raw_code = str(raw_region_code_id)
    candidate_codes = [raw_code[:5], raw_code[:2]]
    for code in candidate_codes:
        if not code:
            continue
        code_id = await db.scalar(
            select(ReferenceCode.code_id).where(
                ReferenceCode.code_group == "REGION",
                ReferenceCode.code == code,
                ReferenceCode.is_active.is_(True),
            )
        )
        if code_id is not None:
            return code_id

    return raw_region_code_id


async def _region_scope_ids(db: AsyncSession, region_code_id: int | None) -> set[int] | None:
    if region_code_id is None:
        return None

    result = await db.execute(
        select(ReferenceCode.code_id, ReferenceCode.parent_code_id).where(
            ReferenceCode.code_group == "REGION",
            ReferenceCode.is_active.is_(True),
        )
    )
    parent_by_id: dict[int, int | None] = {}
    children_by_parent: dict[int, list[int]] = {}
    for code_id, parent_code_id in result.all():
        parent_by_id[code_id] = parent_code_id
        if parent_code_id is not None:
            children_by_parent.setdefault(parent_code_id, []).append(code_id)

    if region_code_id not in parent_by_id:
        return {region_code_id}

    scope = {region_code_id}

    parent_id = parent_by_id.get(region_code_id)
    while parent_id is not None and parent_id not in scope:
        scope.add(parent_id)
        parent_id = parent_by_id.get(parent_id)

    stack = list(children_by_parent.get(region_code_id, []))
    while stack:
        child_id = stack.pop()
        if child_id in scope:
            continue
        scope.add(child_id)
        stack.extend(children_by_parent.get(child_id, []))

    return scope


async def _find_candidate_contractors(
    db: AsyncSession,
    region_code_id: int | None,
    service_task_id: int | None,
) -> list[int]:
    filters = [
        ContractorProfile.approval_status == "APPROVED",
        ContractorProfile.available_status == "AVAILABLE",
        ContractorProfile.matching_alert_enabled.is_(True),
        ContractorService.is_active.is_(True),
    ]
    region_scope_ids = await _region_scope_ids(db, region_code_id)
    if region_scope_ids is not None:
        filters.append(ContractorService.region_code_id.in_(region_scope_ids))
    if service_task_id is not None:
        filters.append(ContractorService.service_task_id == service_task_id)

    result = await db.execute(
        select(ContractorProfile.contractor_id)
        .join(
            ContractorService,
            ContractorService.contractor_id == ContractorProfile.contractor_id,
        )
        .where(
            *filters,
        )
        .order_by(ContractorProfile.rating_avg.desc(), ContractorProfile.review_count.desc())
    )
    contractor_ids = []
    seen = set()
    for contractor_id in result.scalars().all():
        if contractor_id in seen:
            continue
        seen.add(contractor_id)
        contractor_ids.append(contractor_id)
    return contractor_ids


async def create_matching_request(
    db: AsyncSession,
    current_user: User,
    payload: MatchingRequestCreate,
) -> MatchingRequest:
    require_customer(current_user)
    now = datetime.now(timezone.utc)
    try:
        active_matching_request_id = await db.scalar(
            select(MatchingRequest.matching_request_id).where(
                MatchingRequest.user_id == current_user.user_id,
                MatchingRequest.matching_status.in_(ACTIVE_MATCHING_STATUSES),
            )
        )
        if active_matching_request_id is not None:
            raise HTTPException(
                status_code=409,
                detail="Customer already has an active matching request",
            )

        if payload.estimate_id is not None:
            estimate = await db.scalar(
                select(AiEstimate).where(
                    AiEstimate.estimate_id == payload.estimate_id,
                    AiEstimate.user_id == current_user.user_id,
                )
            )
            if estimate is None:
                raise HTTPException(status_code=404, detail="AI estimate not found")
            if estimate.estimate_status != "COMPLETED":
                raise HTTPException(
                    status_code=409,
                    detail="Only completed AI estimates can be used for matching requests",
                )

        region_code_id = await _resolve_region_code_id(db, payload.region_code_id)
        contractor_ids = await _find_candidate_contractors(
            db,
            region_code_id=region_code_id,
            service_task_id=payload.service_task_id,
        )
        matching_request = MatchingRequest(
            user_id=current_user.user_id,
            estimate_id=payload.estimate_id,
            service_task_id=payload.service_task_id,
            title=payload.title.strip(),
            region_code_id=region_code_id,
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
        for contractor_id in contractor_ids:
            await create_notification(
                db,
                user_id=contractor_id,
                notification_type="MATCHING_REQUEST_NEW",
                title="새로운 시공 요청이 도착했습니다",
                content=f"'{matching_request.title}' 시공 요청이 도착했습니다.",
                target_type="MATCHING_REQUEST",
                target_id=matching_request.matching_request_id,
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
    is_customer_owner = (
        current_user.user_type in CUSTOMER_ROLES and request.user_id == current_user.user_id
    )
    if current_user.user_type in CONTRACTOR_ROLES and not is_customer_owner:
        allowed = await db.scalar(
            select(MatchingTarget.matching_target_id).where(
                MatchingTarget.matching_request_id == matching_request_id,
                MatchingTarget.contractor_id == current_user.user_id,
            )
        )
        if allowed is None:
            raise HTTPException(status_code=404, detail="Matching request not found")
    elif current_user.user_type in CUSTOMER_ROLES and not is_customer_owner:
        raise HTTPException(status_code=404, detail="Matching request not found")
    if current_user.user_type not in CUSTOMER_ROLES | CONTRACTOR_ROLES:
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
