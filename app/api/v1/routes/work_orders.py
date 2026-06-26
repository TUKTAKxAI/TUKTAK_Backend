from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.work_order import (
    WorkOrderCancel,
    WorkOrderDetailResponse,
    WorkOrderListResponse,
    WorkOrderScheduleUpdate,
    WorkOrderStatusResponse,
)
from app.services import work_order as work_order_service

router = APIRouter(prefix="/work-orders", tags=["Work Order"])


@router.get("", response_model=WorkOrderListResponse)
async def list_work_orders(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkOrderListResponse:
    items, page, size, total = await work_order_service.list_work_orders(
        db, current_user, status, page, size
    )
    return WorkOrderListResponse(items=items, page=page, size=size, total=total)


@router.get("/{work_order_id}", response_model=WorkOrderDetailResponse)
async def get_work_order(
    work_order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkOrderDetailResponse:
    work_order = await work_order_service.get_work_order_detail(
        db, current_user, work_order_id
    )
    return WorkOrderDetailResponse(work_order=work_order)


@router.patch("/{work_order_id}/schedule", response_model=WorkOrderStatusResponse)
async def update_work_order_schedule(
    work_order_id: int,
    payload: WorkOrderScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkOrderStatusResponse:
    work_order = await work_order_service.update_work_order_schedule(
        db, current_user, work_order_id, payload
    )
    return WorkOrderStatusResponse(
        work_order_id=work_order.work_order_id,
        work_order_status=work_order.work_order_status,
        updated_at=work_order.updated_at,
    )


@router.patch("/{work_order_id}/start", response_model=WorkOrderStatusResponse)
async def start_work_order(
    work_order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkOrderStatusResponse:
    work_order = await work_order_service.start_work_order(
        db, current_user, work_order_id
    )
    return WorkOrderStatusResponse(
        work_order_id=work_order.work_order_id,
        work_order_status=work_order.work_order_status,
        updated_at=work_order.updated_at,
    )


@router.patch("/{work_order_id}/complete", response_model=WorkOrderStatusResponse)
async def complete_work_order(
    work_order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkOrderStatusResponse:
    work_order = await work_order_service.complete_work_order(
        db, current_user, work_order_id
    )
    return WorkOrderStatusResponse(
        work_order_id=work_order.work_order_id,
        work_order_status=work_order.work_order_status,
        updated_at=work_order.updated_at,
    )


@router.patch("/{work_order_id}/confirm", response_model=WorkOrderStatusResponse)
async def confirm_work_order(
    work_order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkOrderStatusResponse:
    work_order = await work_order_service.confirm_work_order(
        db, current_user, work_order_id
    )
    return WorkOrderStatusResponse(
        work_order_id=work_order.work_order_id,
        work_order_status=work_order.work_order_status,
        updated_at=work_order.updated_at,
    )


@router.patch("/{work_order_id}/cancel", response_model=WorkOrderStatusResponse)
async def cancel_work_order(
    work_order_id: int,
    payload: WorkOrderCancel,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkOrderStatusResponse:
    work_order = await work_order_service.cancel_work_order(
        db, current_user, work_order_id, payload
    )
    return WorkOrderStatusResponse(
        work_order_id=work_order.work_order_id,
        work_order_status=work_order.work_order_status,
        updated_at=work_order.updated_at,
    )
