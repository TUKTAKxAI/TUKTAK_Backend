from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AiEstimate,
    ContractorProfile,
    MatchingRequest,
    MatchingTarget,
    Quote,
    ReferenceCode,
    ServiceTask,
    User,
    WorkOrder,
)
from app.schemas.quote import ContractorQuoteSummary, QuoteCreate, QuoteDetail, QuoteSummary
from app.services.matching_common import (
    CONTRACTOR_ROLES,
    CUSTOMER_ROLES,
    pagination,
    require_contractor,
    require_customer,
)
from app.services.matching_request import get_matching_request_detail
from app.services.notification import create_notification
from app.services.s3_image_storage import display_image_urls


QUOTE_OPEN_MATCHING_STATUSES = {"REQUESTED", "RECEIVING_QUOTES"}


async def create_quote(
    db: AsyncSession,
    current_user: User,
    matching_request_id: int,
    payload: QuoteCreate,
) -> Quote:
    require_contractor(current_user)
    result = await db.execute(
        select(MatchingRequest, MatchingTarget)
        .join(
            MatchingTarget,
            MatchingTarget.matching_request_id == MatchingRequest.matching_request_id,
        )
        .where(
            MatchingRequest.matching_request_id == matching_request_id,
            MatchingTarget.contractor_id == current_user.user_id,
            MatchingTarget.target_status.in_(["NOTIFIED", "VIEWED"]),
        )
        .with_for_update()
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Matching request not found")

    matching_request, matching_target = row
    if matching_request.matching_status not in QUOTE_OPEN_MATCHING_STATUSES:
        raise HTTPException(status_code=409, detail="Matching request is not accepting quotes")

    existing_quote_id = await db.scalar(
        select(Quote.quote_id).where(
            Quote.matching_request_id == matching_request_id,
            Quote.contractor_id == current_user.user_id,
            Quote.quote_status.in_(["SENT", "SELECTED"]),
        )
    )
    if existing_quote_id is not None:
        raise HTTPException(status_code=409, detail="Quote already submitted")

    now = datetime.now(timezone.utc)
    quote = Quote(
        matching_request_id=matching_request.matching_request_id,
        contractor_id=current_user.user_id,
        quote_status="SENT",
        total_amount=payload.total_amount,
        work_scope=payload.work_scope,
        quote_items_json=payload.quote_items,
        included_items=payload.included_items,
        excluded_items=payload.excluded_items,
        estimated_minutes=payload.estimated_minutes,
        visit_count=payload.visit_count,
        available_date=payload.available_date,
        arrival_time=payload.arrival_time,
        as_period_days=payload.as_period_days,
        valid_until=payload.valid_until,
        additional_note=payload.additional_note,
        sent_at=now,
    )
    async with db.begin_nested():
        matching_target.target_status = "QUOTED"
        matching_request.matching_status = "RECEIVING_QUOTES"
        db.add(quote)
    await create_notification(
        db,
        user_id=matching_request.user_id,
        notification_type="QUOTE_RECEIVED",
        title="새로운 견적이 도착했습니다",
        content=f"'{matching_request.title}' 요청에 새로운 견적이 도착했습니다.",
        target_type="MATCHING_REQUEST",
        target_id=matching_request.matching_request_id,
    )
    await db.commit()
    await db.refresh(quote)
    return quote


async def list_quotes_for_matching_request(
    db: AsyncSession,
    current_user: User,
    matching_request_id: int,
    page: int,
    size: int,
) -> tuple[list[QuoteSummary], int, int, int]:
    detail = await get_matching_request_detail(db, current_user, matching_request_id)
    if current_user.user_type not in CUSTOMER_ROLES or detail.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Customer account required")

    page, size = pagination(page, size)
    filters = [Quote.matching_request_id == matching_request_id]
    total = await db.scalar(select(func.count()).select_from(Quote).where(*filters))
    result = await db.execute(
        select(Quote, ContractorProfile.business_name)
        .join(ContractorProfile, ContractorProfile.contractor_id == Quote.contractor_id)
        .where(*filters)
        .order_by(Quote.total_amount.asc(), Quote.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [
        QuoteSummary(
            quote_id=quote.quote_id,
            matching_request_id=quote.matching_request_id,
            contractor_id=quote.contractor_id,
            business_name=business_name,
            quote_status=quote.quote_status,
            total_amount=quote.total_amount,
            work_scope=quote.work_scope,
            estimated_minutes=quote.estimated_minutes,
            visit_count=quote.visit_count,
            available_date=quote.available_date,
            valid_until=quote.valid_until,
            sent_at=quote.sent_at,
            selected_at=quote.selected_at,
            created_at=quote.created_at,
        )
        for quote, business_name in result.all()
    ]
    return items, page, size, int(total or 0)


async def list_contractor_quotes(
    db: AsyncSession,
    current_user: User,
    quote_status: str | None,
    page: int,
    size: int,
) -> tuple[list[ContractorQuoteSummary], int, int, int]:
    require_contractor(current_user)
    page, size = pagination(page, size)
    filters = [Quote.contractor_id == current_user.user_id]
    if quote_status:
        filters.append(Quote.quote_status == quote_status)

    total = await db.scalar(select(func.count()).select_from(Quote).where(*filters))
    result = await db.execute(
        select(
            Quote,
            MatchingRequest,
            ReferenceCode.code_name.label("region_name"),
            ServiceTask.task_name.label("service_task_name"),
            AiEstimate,
        )
        .join(MatchingRequest, MatchingRequest.matching_request_id == Quote.matching_request_id)
        .outerjoin(ReferenceCode, ReferenceCode.code_id == MatchingRequest.region_code_id)
        .outerjoin(ServiceTask, ServiceTask.service_task_id == MatchingRequest.service_task_id)
        .outerjoin(AiEstimate, AiEstimate.estimate_id == MatchingRequest.estimate_id)
        .where(*filters)
        .order_by(Quote.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [
        ContractorQuoteSummary(
            quote_id=quote.quote_id,
            matching_request_id=quote.matching_request_id,
            matching_request_title=matching_request.title,
            service_task_id=matching_request.service_task_id,
            service_task_name=service_task_name,
            region_code_id=matching_request.region_code_id,
            region_name=region_name,
            address=matching_request.address,
            preferred_date=matching_request.preferred_date,
            preferred_time_start=matching_request.preferred_time_start,
            preferred_time_end=matching_request.preferred_time_end,
            budget_min=matching_request.budget_min,
            budget_max=matching_request.budget_max,
            request_message=matching_request.request_message,
            estimate_id=matching_request.estimate_id,
            estimate_description=estimate.description if estimate else None,
            estimate_image_urls=display_image_urls(estimate.image_urls if estimate else None),
            estimate_main_category=estimate.main_category if estimate else None,
            estimate_object_label=estimate.object_label if estimate else None,
            estimate_problem_label=estimate.problem_label if estimate else None,
            estimate_repair_task_name=estimate.repair_task_name if estimate else None,
            estimate_severity=estimate.severity if estimate else None,
            estimate_min_price=estimate.min_price if estimate else None,
            estimate_max_price=estimate.max_price if estimate else None,
            estimate_minutes_min=estimate.estimated_minutes_min if estimate else None,
            estimate_minutes_max=estimate.estimated_minutes_max if estimate else None,
            estimate_confidence_score=estimate.confidence_score if estimate else None,
            estimate_ai_summary=estimate.ai_summary if estimate else None,
            matching_status=matching_request.matching_status,
            quote_status=quote.quote_status,
            total_amount=quote.total_amount,
            work_scope=quote.work_scope,
            estimated_minutes=quote.estimated_minutes,
            visit_count=quote.visit_count,
            available_date=quote.available_date,
            valid_until=quote.valid_until,
            sent_at=quote.sent_at,
            selected_at=quote.selected_at,
            created_at=quote.created_at,
        )
        for quote, matching_request, region_name, service_task_name, estimate in result.all()
    ]
    return items, page, size, int(total or 0)


async def get_quote_detail(
    db: AsyncSession,
    current_user: User,
    quote_id: int,
) -> QuoteDetail:
    result = await db.execute(
        select(
            Quote,
            MatchingRequest.user_id,
            MatchingRequest.title,
            ContractorProfile.business_name,
        )
        .join(MatchingRequest, MatchingRequest.matching_request_id == Quote.matching_request_id)
        .join(ContractorProfile, ContractorProfile.contractor_id == Quote.contractor_id)
        .where(Quote.quote_id == quote_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote, user_id, matching_request_title, business_name = row
    has_customer_access = (
        current_user.user_type in CUSTOMER_ROLES and user_id == current_user.user_id
    )
    has_contractor_access = (
        current_user.user_type in CONTRACTOR_ROLES and quote.contractor_id == current_user.user_id
    )
    if not has_customer_access and not has_contractor_access:
        raise HTTPException(status_code=404, detail="Quote not found")

    return QuoteDetail(
        quote_id=quote.quote_id,
        matching_request_id=quote.matching_request_id,
        matching_request_title=matching_request_title,
        contractor_id=quote.contractor_id,
        business_name=business_name,
        quote_status=quote.quote_status,
        total_amount=quote.total_amount,
        work_scope=quote.work_scope,
        quote_items=quote.quote_items_json,
        included_items=quote.included_items,
        excluded_items=quote.excluded_items,
        estimated_minutes=quote.estimated_minutes,
        visit_count=quote.visit_count,
        available_date=quote.available_date,
        arrival_time=quote.arrival_time,
        as_period_days=quote.as_period_days,
        valid_until=quote.valid_until,
        additional_note=quote.additional_note,
        sent_at=quote.sent_at,
        selected_at=quote.selected_at,
        created_at=quote.created_at,
        updated_at=quote.updated_at,
    )


async def delete_contractor_quote(
    db: AsyncSession,
    current_user: User,
    quote_id: int,
) -> int:
    require_contractor(current_user)
    result = await db.execute(
        select(Quote, MatchingRequest)
        .join(MatchingRequest, MatchingRequest.matching_request_id == Quote.matching_request_id)
        .where(
            Quote.quote_id == quote_id,
            Quote.contractor_id == current_user.user_id,
            Quote.quote_status == "SENT",
            MatchingRequest.matching_status.in_(QUOTE_OPEN_MATCHING_STATUSES),
        )
        .with_for_update()
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Deletable quote not found")

    quote, matching_request = row
    matching_request_id = matching_request.matching_request_id
    await db.delete(quote)
    await db.flush()

    remaining_quote_count = await db.scalar(
        select(func.count())
        .select_from(Quote)
        .where(
            Quote.matching_request_id == matching_request_id,
            Quote.quote_status.in_(["SENT", "SELECTED"]),
        )
    )
    if not remaining_quote_count:
        matching_request.matching_status = "REQUESTED"

    await db.commit()
    return quote_id


async def select_quote(
    db: AsyncSession,
    current_user: User,
    matching_request_id: int,
    quote_id: int,
) -> tuple[MatchingRequest, Quote, WorkOrder]:
    require_customer(current_user)
    result = await db.execute(
        select(MatchingRequest, Quote)
        .join(Quote, Quote.matching_request_id == MatchingRequest.matching_request_id)
        .where(
            MatchingRequest.matching_request_id == matching_request_id,
            MatchingRequest.user_id == current_user.user_id,
            Quote.quote_id == quote_id,
            Quote.quote_status == "SENT",
        )
        .with_for_update()
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Quote not found")

    matching_request, quote = row
    if matching_request.matching_status in {"SELECTED", "CLOSED", "CANCELLED"}:
        raise HTTPException(status_code=409, detail="Matching request already finalized")

    now = datetime.now(timezone.utc)
    async with db.begin_nested():
        quote.quote_status = "SELECTED"
        quote.selected_at = now
        matching_request.selected_quote_id = quote.quote_id
        matching_request.selected_contractor_id = quote.contractor_id
        matching_request.selected_at = now
        matching_request.matching_status = "SELECTED"
        await db.execute(
            update(Quote)
            .where(
                Quote.matching_request_id == matching_request_id,
                Quote.quote_id != quote.quote_id,
                Quote.quote_status == "SENT",
            )
            .values(quote_status="NOT_SELECTED")
        )
        work_order = WorkOrder(
            matching_request_id=matching_request.matching_request_id,
            quote_id=quote.quote_id,
            customer_id=current_user.user_id,
            contractor_id=quote.contractor_id,
            work_order_status="CREATED",
            final_amount=quote.total_amount,
            scheduled_date=quote.available_date,
        )
        db.add(work_order)
    await create_notification(
        db,
        user_id=quote.contractor_id,
        notification_type="MATCHING_SELECTED",
        title="매칭이 성사되었습니다",
        content=f"'{matching_request.title}' 요청에서 시공자로 선택되었습니다.",
        target_type="MATCHING_REQUEST",
        target_id=matching_request.matching_request_id,
    )
    await db.commit()
    await db.refresh(matching_request)
    await db.refresh(quote)
    await db.refresh(work_order)
    return matching_request, quote, work_order
