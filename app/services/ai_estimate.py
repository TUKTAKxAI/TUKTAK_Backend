from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ai_estimate import AIEstimate


class AIEstimateService:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==========================
    # 공통 입력 검증
    # ==========================
    def _validate_estimate_input(
        self,
        description: str | None,
        images: list[UploadFile] | None,
    ) -> None:

        missing_info = []

        if description is None or len(description.strip()) < 10:
            missing_info.append("상세한 고장 증상")

        if missing_info:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INPUT_NEEDS_MORE_INFO",
                    "missing_info": missing_info,
                },
            )

    # AI 견적 생성
    async def create_estimate(
        self,
        description: str,
        images: list[UploadFile] | None,
        main_category: str | None,
        region_code_id: int | None,
    ):

        self._validate_estimate_input(
            description=description,
            images=images,
        )

        return {
            "success": True,
            "estimate_id": 1,
            "estimate_status": "PROCESSING",
            "created_at": datetime.now(
                ZoneInfo("Asia/Seoul")
            ).isoformat(),
        }

    # AI 견적 상세 조회
    async def get_estimate(
        self,
        estimate_id: int,
    ):

        result = await self.db.execute(
            select(AIEstimate).where(
                AIEstimate.estimate_id == estimate_id
            )
        )

        estimate = result.scalar_one_or_none()

        if estimate is None:
            raise HTTPException(
                status_code=404,
                detail="AI 견적서를 찾을 수 없습니다."
            )

        return {
            "success": True,
            "estimate": {
                "estimate_id": estimate.estimate_id,
                "description": estimate.description,
                "image_urls": estimate.image_urls,
                "main_category": estimate.main_category,
                "object_label": estimate.object_label,
                "problem_label": estimate.problem_label,
                "repair_task_name": estimate.repair_task_name,
                "severity": estimate.severity,
                "min_price": estimate.min_price,
                "max_price": estimate.max_price,
                "estimated_minutes_min": estimate.estimated_minutes_min,
                "estimated_minutes_max": estimate.estimated_minutes_max,
                "confidence_score": estimate.confidence_score,
                "ai_summary": estimate.ai_summary,
                "estimate_status": estimate.estimate_status,
                "created_at": estimate.created_at,
            },
        }

    # 내 AI 견적 목록
    async def get_my_estimates(
        self,
        status: str | None,
        page: int,
        size: int,
    ):

        user_id = 1

        query = select(AIEstimate).where(
            AIEstimate.user_id == user_id
        )

        if status:
            query = query.where(
                AIEstimate.estimate_status == status
            )

        total = await self.db.scalar(
            select(func.count()).select_from(
                query.subquery()
            )
        )

        query = (
            query.order_by(
                AIEstimate.created_at.desc()
            )
            .offset((page - 1) * size)
            .limit(size)
        )

        result = await self.db.execute(query)

        estimates = result.scalars().all()

        return {
            "success": True,
            "items": [
                {
                    "estimate_id": e.estimate_id,
                    "main_category": e.main_category,
                    "repair_task_name": e.repair_task_name,
                    "min_price": e.min_price,
                    "max_price": e.max_price,
                    "confidence_score": e.confidence_score,
                    "estimate_status": e.estimate_status,
                    "created_at": e.created_at,
                }
                for e in estimates
            ],
            "page": page,
            "size": size,
            "total": total,
        }

    # AI 견적 재생성
    async def retry_estimate(
        self,
        estimate_id: int,
        description: str | None,
        images: list[UploadFile] | None,
    ):

        result = await self.db.execute(
            select(AIEstimate).where(
                AIEstimate.estimate_id == estimate_id
            )
        )

        estimate = result.scalar_one_or_none()

        if estimate is None:
            raise HTTPException(
                status_code=404,
                detail="AI 견적서를 찾을 수 없습니다."
            )

        # 재생성 시에도 설명 + 사진 필수
        self._validate_estimate_input(
            description=description,
            images=images,
        )

        # TODO
        # 새 이미지 저장
        # AI 재분석
        # 결과 업데이트

        estimate.description = description
        estimate.estimate_status = "PROCESSING"
        estimate.updated_at = datetime.now(
            ZoneInfo("Asia/Seoul")
        )

        await self.db.commit()
        await self.db.refresh(estimate)

        return {
            "success": True,
            "estimate_id": estimate.estimate_id,
            "estimate_status": estimate.estimate_status,
            "updated_at": estimate.updated_at,
        }