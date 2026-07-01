from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import AiEstimate, ReferenceCode, User
from app.schemas.common import (
    AiEstimateCreateResponse,
    AiEstimateDetail,
    AiEstimateDetailResponse,
    AiEstimateListItem,
    AiEstimateListResponse,
    AiEstimateRetryResponse,
)
from app.services import ai_stub

router = APIRouter(tags=["AI Estimate"])


async def _normalize_region_code_id(
    db: AsyncSession,
    region_code_id: int | None,
) -> int | None:
    if region_code_id is None or region_code_id <= 0:
        return None
    exists = await db.scalar(
        select(ReferenceCode.code_id).where(
            ReferenceCode.code_id == region_code_id,
            ReferenceCode.is_active.is_(True),
        )
    )
    if exists is None:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_REFERENCE_CODE",
                "field": "region_code_id",
                "message": "region_code_id does not exist",
            },
        )
    return region_code_id


@router.post("/ai-estimates", response_model=AiEstimateCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_estimate(
    description: str = Form(...),
    images: list[UploadFile] = File(...),
    main_category: str | None = Form(None),
    region_code_id: int | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AiEstimateCreateResponse:
    if not images:
        raise HTTPException(status_code=422, detail={"code": "INPUT_NEEDS_MORE_INFO", "missing_info": ["images"]})
    normalized_region_code_id = await _normalize_region_code_id(db, region_code_id)
    estimate = AiEstimate(
        user_id=current_user.user_id,
        description=description,
        main_category=main_category or "UNKNOWN",
        object_label="분석 대기",
        problem_label="분석 대기",
        repair_task_name="분석 대기",
        severity="UNKNOWN",
        ai_summary="AI 분석 요청이 접수되었습니다.",
        estimate_status="PROCESSING",
        image_urls=[f"/uploads/ai-estimates/{current_user.user_id}/{img.filename}" for img in images],
        region_code_id=normalized_region_code_id,
    )
    db.add(estimate)
    await db.flush()
    await ai_stub.complete_ai_estimate(estimate)
    await db.commit()
    await db.refresh(estimate)
    return AiEstimateCreateResponse(
        estimate_id=estimate.estimate_id,
        estimate_status=estimate.estimate_status,
        created_at=estimate.created_at,
    )


@router.get("/ai-estimates/{estimate_id}", response_model=AiEstimateDetailResponse)
async def get_ai_estimate(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AiEstimateDetailResponse:
    result = await db.execute(
        select(AiEstimate).where(AiEstimate.estimate_id == estimate_id, AiEstimate.user_id == current_user.user_id)
    )
    estimate = result.scalar_one_or_none()
    if estimate is None:
        raise HTTPException(status_code=404, detail="AI estimate not found")
    return AiEstimateDetailResponse(estimate=AiEstimateDetail.model_validate(estimate))


@router.get("/users/me/ai-estimates", response_model=AiEstimateListResponse)
async def get_my_ai_estimates(
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AiEstimateListResponse:
    query = select(AiEstimate).where(AiEstimate.user_id == current_user.user_id)
    count_query = select(func.count()).select_from(AiEstimate).where(AiEstimate.user_id == current_user.user_id)
    if status_filter:
        query = query.where(AiEstimate.estimate_status == status_filter)
        count_query = count_query.where(AiEstimate.estimate_status == status_filter)
    query = query.order_by(AiEstimate.created_at.desc()).offset((page - 1) * size).limit(size)
    items = (await db.execute(query)).scalars().all()
    total = int((await db.execute(count_query)).scalar_one())
    return AiEstimateListResponse(
        items=[AiEstimateListItem.model_validate(item) for item in items],
        page=page,
        size=size,
        total=total,
    )


@router.post("/ai-estimates/{estimate_id}/retry", response_model=AiEstimateRetryResponse)
async def retry_ai_estimate(
    estimate_id: int,
    description: str | None = Form(None),
    images: list[UploadFile] | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AiEstimateRetryResponse:
    result = await db.execute(
        select(AiEstimate).where(AiEstimate.estimate_id == estimate_id, AiEstimate.user_id == current_user.user_id)
    )
    estimate = result.scalar_one_or_none()
    if estimate is None:
        raise HTTPException(status_code=404, detail="AI estimate not found")
    if estimate.estimate_status != "FAILED":
        raise HTTPException(status_code=409, detail="Only failed estimates can be retried")
    if description is not None:
        estimate.description = description
    if images:
        estimate.image_urls = [f"/uploads/ai-estimates/{current_user.user_id}/{img.filename}" for img in images]
    estimate.estimate_status = "PROCESSING"
    await ai_stub.complete_ai_estimate(estimate)
    await db.commit()
    await db.refresh(estimate)
    return AiEstimateRetryResponse(
        estimate_id=estimate.estimate_id,
        estimate_status=estimate.estimate_status,
        updated_at=estimate.updated_at,
    )
