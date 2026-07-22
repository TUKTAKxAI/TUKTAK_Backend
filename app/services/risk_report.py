from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import risk_report as risk_report_crud
from app.db.models import AiEstimate
from app.db.models.risk_report import RiskReport
from app.schemas.risk_report import RiskReportCreateRequest
from app.services.risk_report_client import complete_risk_report_with_ai_service


async def create_risk_report(
    db: AsyncSession,
    user_id: int,
    payload: RiskReportCreateRequest,
) -> RiskReport:
    estimate = await db.scalar(
        select(AiEstimate).where(
            AiEstimate.estimate_id == payload.estimate_id,
            AiEstimate.user_id == user_id,
        )
    )
    if estimate is None:
        raise HTTPException(status_code=404, detail="AI estimate not found")
    if estimate.estimate_status != "COMPLETED":
        raise HTTPException(status_code=409, detail="Only completed AI estimates can be used for risk reports")

    risk_report = await risk_report_crud.create_risk_report(
        db=db,
        user_id=user_id,
        estimate_id=payload.estimate_id,
    )
    try:
        await complete_risk_report_with_ai_service(db, risk_report, estimate)
    except Exception as exc:
        risk_report.report_status = "FAILED"
        risk_report.failure_reason = str(exc)
        risk_report.summary = "AI 리스크 리포트 생성 중 오류가 발생했습니다."
    await db.commit()
    await db.refresh(risk_report)
    return risk_report


async def get_risk_reports(
    db: AsyncSession,
    user_id: int,
    status: str | None,
    page: int,
    size: int,
) -> tuple[list[RiskReport], int]:
    offset = (page - 1) * size

    items = await risk_report_crud.get_risk_reports(
        db=db,
        user_id=user_id,
        status=status,
        offset=offset,
        limit=size,
    )
    total = await risk_report_crud.count_risk_reports(
        db=db,
        user_id=user_id,
        status=status,
    )

    return items, total


async def get_risk_report_detail(
    db: AsyncSession,
    user_id: int,
    risk_report_id: int,
) -> RiskReport:
    risk_report = await risk_report_crud.get_risk_report_by_id(
        db=db,
        user_id=user_id,
        risk_report_id=risk_report_id,
    )

    if risk_report is None:
        raise HTTPException(status_code=404, detail="Risk report not found")

    return risk_report
