from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AiEstimate, MatchingRequest, MatchingTarget, Quote, ReferenceCode, ServiceTask, User
from app.schemas.contractor_matching import (
    ContractorMatchingDecline,
    ContractorMatchingRequestSummary,
)
from app.services.matching_common import pagination, require_contractor
from app.services.s3_image_storage import display_image_urls

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
    filters = [
        MatchingTarget.contractor_id == current_user.user_id,
        MatchingRequest.matching_status.in_(OPEN_MATCHING_STATUSES),
    ]
    if target_status:
        filters.append(MatchingTarget.target_status == target_status)

    total = await db.scalar(
        select(func.count())
        .select_from(MatchingTarget)
        .join(
            MatchingRequest,
            MatchingRequest.matching_request_id == MatchingTarget.matching_request_id,
        )
        .where(*filters)
    )
    result = await db.execute(
        select(
            MatchingTarget,
            MatchingRequest,
            Quote.quote_id,
            ReferenceCode.code_name.label("region_name"),
            ServiceTask.task_name.label("service_task_name"),
            AiEstimate,
        )
        .join(
            MatchingRequest,
            MatchingRequest.matching_request_id == MatchingTarget.matching_request_id,
        )
        .outerjoin(
            ReferenceCode,
            ReferenceCode.code_id == MatchingRequest.region_code_id,
        )
        .outerjoin(
            ServiceTask,
            ServiceTask.service_task_id == MatchingRequest.service_task_id,
        )
        .outerjoin(
            AiEstimate,
            AiEstimate.estimate_id == MatchingRequest.estimate_id,
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
            service_task_name=service_task_name,
            region_code_id=request.region_code_id,
            region_name=region_name,
            address=request.address,
            preferred_date=request.preferred_date,
            preferred_time_start=request.preferred_time_start,
            preferred_time_end=request.preferred_time_end,
            budget_min=request.budget_min,
            budget_max=request.budget_max,
            request_message=request.request_message,
            matching_status=request.matching_status,
            target_status=target.target_status,
            quote_id=quote_id,
            estimate_id=request.estimate_id,
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
            created_at=target.created_at,
        )
        for target, request, quote_id, region_name, service_task_name, estimate in result.all()
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
