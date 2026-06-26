from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MatchingRequest, MatchingTarget, Quote, User
from app.schemas.contractor_matching import ContractorMatchingRequestSummary
from app.services.matching_common import pagination, require_contractor


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
