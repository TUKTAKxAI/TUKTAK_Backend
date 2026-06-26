from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MatchingRequest, MatchingTarget, Quote, User
from app.schemas.contractor_matching import (
    ContractorMatchingDecline,
    ContractorMatchingRequestSummary,
)
from app.services.matching_common import pagination, require_contractor

DECLINABLE_TARGET_STATUSES = {"NOTIFIED", "VIEWED"}
OPEN_MATCHING_STATUSES = {"REQUESTED", "RECEIVING_QUOTES"}


async def list_contractor_matching_requests(
    db: AsyncSession,
    current_user: User,
    target_status: str | None,
    page: int,
    size: int,
) -> tuple[list[ContractorMatchingRequestSummary], int, int, int]:
    require_contractor(current_user)
    page, size = pagination(page, size)
    filters = [MatchingTarget.contractor_id == current_user.user_id]
    if target_status:
        filters.append(MatchingTarget.target_status == target_status)

    total = await db.scalar(select(func.count()).select_from(MatchingTarget).where(*filters))
    result = await db.execute(
        select(MatchingTarget, MatchingRequest, Quote.quote_id)
        .join(
            MatchingRequest,
            MatchingRequest.matching_request_id == MatchingTarget.matching_request_id,
        )
        .outerjoin(
            Quote,
            (Quote.matching_request_id == MatchingRequest.matching_request_id)
            & (Quote.contractor_id == current_user.user_id),
        )
        .where(*filters)
        .order_by(MatchingTarget.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [
        ContractorMatchingRequestSummary(
            matching_request_id=request.matching_request_id,
            matching_target_id=target.matching_target_id,
            title=request.title,
            service_task_id=request.service_task_id,
            region_code_id=request.region_code_id,
            preferred_date=request.preferred_date,
            budget_min=request.budget_min,
            budget_max=request.budget_max,
            matching_status=request.matching_status,
            target_status=target.target_status,
            quote_id=quote_id,
            created_at=target.created_at,
        )
        for target, request, quote_id in result.all()
    ]
    return items, page, size, int(total or 0)


async def decline_matching_request(
    db: AsyncSession,
    current_user: User,
    matching_request_id: int,
    payload: ContractorMatchingDecline,
) -> MatchingTarget:
    require_contractor(current_user)
    result = await db.execute(
        select(MatchingTarget, MatchingRequest)
        .join(
            MatchingRequest,
            MatchingRequest.matching_request_id == MatchingTarget.matching_request_id,
        )
        .where(
            MatchingTarget.matching_request_id == matching_request_id,
            MatchingTarget.contractor_id == current_user.user_id,
            MatchingTarget.target_status.in_(DECLINABLE_TARGET_STATUSES),
            MatchingRequest.matching_status.in_(OPEN_MATCHING_STATUSES),
        )
        .with_for_update()
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Declinable matching target not found")

    quote_id = await db.scalar(
        select(Quote.quote_id).where(
            Quote.matching_request_id == matching_request_id,
            Quote.contractor_id == current_user.user_id,
            Quote.quote_status.in_(["SENT", "SELECTED"]),
        )
    )
    if quote_id is not None:
        raise HTTPException(status_code=409, detail="Quote already submitted")

    matching_target, _ = row
    matching_target.target_status = "DECLINED"
    matching_target.declined_reason = payload.declined_reason
    matching_target.declined_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(matching_target)
    return matching_target
