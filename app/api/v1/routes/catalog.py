from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import ReferenceCode, ServiceTask
from app.schemas.common import (
    ReferenceCodeItem,
    ReferenceCodeListResponse,
    ServiceTaskItem,
    ServiceTaskListResponse,
)

router = APIRouter(tags=["Reference Code", "Service Task"])


@router.get("/reference-codes", response_model=ReferenceCodeListResponse)
async def get_reference_codes(
    code_group: str = Query(...),
    parent_code_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ReferenceCodeListResponse:
    query = select(ReferenceCode).where(
        ReferenceCode.code_group == code_group,
        ReferenceCode.is_active.is_(True),
    )
    if parent_code_id is not None:
        query = query.where(ReferenceCode.parent_code_id == parent_code_id)
    query = query.order_by(ReferenceCode.sort_order, ReferenceCode.code_id)
    result = await db.execute(query)
    return ReferenceCodeListResponse(
        codes=[ReferenceCodeItem.model_validate(item) for item in result.scalars()]
    )


@router.get("/service-tasks", response_model=ServiceTaskListResponse)
async def get_service_tasks(
    main_category: str | None = Query(None),
    parent_task_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ServiceTaskListResponse:
    query = select(ServiceTask).where(ServiceTask.is_active.is_(True))
    if main_category is not None:
        query = query.where(ServiceTask.main_category == main_category)
    if parent_task_id is not None:
        query = query.where(ServiceTask.parent_task_id == parent_task_id)
    query = query.order_by(ServiceTask.sort_order, ServiceTask.service_task_id)
    result = await db.execute(query)
    return ServiceTaskListResponse(
        tasks=[ServiceTaskItem.model_validate(item) for item in result.scalars()]
    )
