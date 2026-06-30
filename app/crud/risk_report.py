from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.risk_report import RiskReport


async def create_risk_report(
    db: AsyncSession,
    user_id: int,
    estimate_id: int,
) -> RiskReport:
    risk_report = RiskReport(
        user_id=user_id,
        estimate_id=estimate_id,
        report_status="PROCESSING",
    )
    db.add(risk_report)
    await db.flush()
    await db.refresh(risk_report)
    return risk_report


async def get_risk_reports(
    db: AsyncSession,
    user_id: int,
    status: str | None,
    offset: int,
    limit: int,
) -> list[RiskReport]:
    query = select(RiskReport).where(RiskReport.user_id == user_id)

    if status is not None:
        query = query.where(RiskReport.report_status == status)

    query = query.order_by(RiskReport.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


async def count_risk_reports(
    db: AsyncSession,
    user_id: int,
    status: str | None,
) -> int:
    query = select(func.count()).select_from(RiskReport).where(RiskReport.user_id == user_id)

    if status is not None:
        query = query.where(RiskReport.report_status == status)

    result = await db.execute(query)
    return int(result.scalar_one())


async def get_risk_report_by_id(
    db: AsyncSession,
    user_id: int,
    risk_report_id: int,
) -> RiskReport | None:
    result = await db.execute(
        select(RiskReport).where(
            RiskReport.risk_report_id == risk_report_id,
            RiskReport.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()