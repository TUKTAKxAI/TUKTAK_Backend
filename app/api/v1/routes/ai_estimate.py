from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.ai_estimate import AIEstimateService

router = APIRouter(
    prefix="/ai-estimates",
    tags=["AI Estimate"],
)


# 1. AI 견적 생성
@router.post("")
async def create_ai_estimate(
    description: str = Form(...),
    images: Optional[list[UploadFile]] = File(None),
    main_category: Optional[str] = Form(None),
    region_code_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    service = AIEstimateService(db)

    return await service.create_estimate(
        description=description,
        images=images,
        main_category=main_category,
        region_code_id=region_code_id,
    )


# 2. 내 AI 견적 목록
@router.get("/users/me")
async def get_my_ai_estimates(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = AIEstimateService(db)

    return await service.get_my_estimates(
        status=status,
        page=page,
        size=size,
    )


# 3. AI 견적 상세 조회
@router.get("/{estimate_id}")
async def get_ai_estimate(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = AIEstimateService(db)

    return await service.get_estimate(estimate_id)


# 4. AI 견적 재생성
@router.post("/{estimate_id}/retry")
async def retry_ai_estimate(
    estimate_id: int,
    description: Optional[str] = Form(None),
    images: Optional[list[UploadFile]] = File(None),
    db: AsyncSession = Depends(get_db),
):
    service = AIEstimateService(db)

    return await service.retry_estimate(
        estimate_id=estimate_id,
        description=description,
        images=images,
    )