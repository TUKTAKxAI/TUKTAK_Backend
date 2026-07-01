from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import risk_report as risk_report_crud
from app.db.models.risk_report import RiskReport
from app.schemas.risk_report import RiskReportCreateRequest
from app.services import ai_stub


async def create_risk_report(
    db: AsyncSession,
    user_id: int,
    payload: RiskReportCreateRequest,
) -> RiskReport:
    risk_report = await risk_report_crud.create_risk_report(
        db=db,
        user_id=user_id,
        estimate_id=payload.estimate_id,
    )
    await ai_stub.complete_risk_report(db, risk_report)
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
