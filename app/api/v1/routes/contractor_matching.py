from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.contractor_matching import (
    ContractorMatchingDecline,
    ContractorMatchingDeclineResponse,
    ContractorMatchingRequestListResponse,
)
from app.services import contractor_matching as contractor_matching_service

router = APIRouter(prefix="/contractors/me/matching-requests", tags=["Contractor Matching"])


@router.get("", response_model=ContractorMatchingRequestListResponse)
async def list_contractor_matching_requests(
    target_status: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContractorMatchingRequestListResponse:
    items, page, size, total = (
        await contractor_matching_service.list_contractor_matching_requests(
            db, current_user, target_status, page, size
        )
    )
    return ContractorMatchingRequestListResponse(
        items=items,
        page=page,
        size=size,
        total=total,
    )


@router.patch("/{matching_request_id}/decline", response_model=ContractorMatchingDeclineResponse)
async def decline_matching_request(
    matching_request_id: int,
    payload: ContractorMatchingDecline,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContractorMatchingDeclineResponse:
    target = await contractor_matching_service.decline_matching_request(
        db, current_user, matching_request_id, payload
    )
    return ContractorMatchingDeclineResponse(
        matching_request_id=target.matching_request_id,
        matching_target_id=target.matching_target_id,
        target_status=target.target_status,
        declined_at=target.declined_at,
    )
