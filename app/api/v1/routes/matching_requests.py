from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.matching_request import (
    MatchingRequestCancel,
    MatchingRequestCancelResponse,
    MatchingRequestCreate,
    MatchingRequestCreateResponse,
    MatchingRequestDeleteResponse,
    MatchingRequestDetailResponse,
    MatchingRequestListResponse,
)
from app.services import matching_request as matching_request_service

router = APIRouter(prefix="/matching-requests", tags=["Matching"])


@router.post("", response_model=MatchingRequestCreateResponse, status_code=201)
async def create_matching_request(
    payload: MatchingRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchingRequestCreateResponse:
    request = await matching_request_service.create_matching_request(
        db, current_user, payload
    )
    return MatchingRequestCreateResponse(
        matching_request_id=request.matching_request_id,
        matching_status=request.matching_status,
        matched_contractor_count=request.matched_contractor_count,
        expires_at=request.expires_at,
        created_at=request.created_at,
    )


@router.get("", response_model=MatchingRequestListResponse)
async def list_matching_requests(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchingRequestListResponse:
    items, page, size, total = await matching_request_service.list_customer_matching_requests(
        db, current_user, status, page, size
    )
    return MatchingRequestListResponse(items=items, page=page, size=size, total=total)


@router.get("/{matching_request_id}", response_model=MatchingRequestDetailResponse)
async def get_matching_request(
    matching_request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchingRequestDetailResponse:
    request = await matching_request_service.get_matching_request_detail(
        db, current_user, matching_request_id
    )
    return MatchingRequestDetailResponse(request=request)


@router.patch("/{matching_request_id}/cancel", response_model=MatchingRequestCancelResponse)
async def cancel_matching_request(
    matching_request_id: int,
    payload: MatchingRequestCancel,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchingRequestCancelResponse:
    request = await matching_request_service.cancel_matching_request(
        db, current_user, matching_request_id, payload
    )
    return MatchingRequestCancelResponse(
        matching_request_id=request.matching_request_id,
        matching_status=request.matching_status,
        canceled_at=request.updated_at,
    )


@router.delete("/{matching_request_id}", response_model=MatchingRequestDeleteResponse)
async def delete_matching_request(
    matching_request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchingRequestDeleteResponse:
    deleted_id = await matching_request_service.delete_matching_request(
        db, current_user, matching_request_id
    )
    return MatchingRequestDeleteResponse(
        matching_request_id=deleted_id,
        message="Matching request deleted",
    )
