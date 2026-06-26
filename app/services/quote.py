from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    ContractorProfile,
    MatchingRequest,
    MatchingTarget,
    Quote,
    User,
    WorkOrder,
)
from app.schemas.quote import QuoteCreate, QuoteSummary
from app.services.matching_common import pagination, require_contractor, require_customer
from app.services.matching_request import get_matching_request_detail


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
    if current_user.user_type != "CUSTOMER" or detail.customer_id != current_user.user_id:
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
            MatchingRequest.customer_id == current_user.user_id,
            Quote.quote_id == quote_id,
        )
        .with_for_update()
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Quote not found")

    matching_request, quote = row
    if matching_request.matching_status in {"SELECTED", "CLOSED", "CANCELED"}:
        raise HTTPException(status_code=409, detail="Matching request already finalized")

    now = datetime.now(timezone.utc)
    async with db.begin_nested():
        quote.quote_status = "SELECTED"
        quote.selected_at = now
        matching_request.selected_quote_id = quote.quote_id
        matching_request.selected_contractor_id = quote.contractor_id
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
    await db.commit()
    await db.refresh(matching_request)
    await db.refresh(quote)
    await db.refresh(work_order)
    return matching_request, quote, work_order
