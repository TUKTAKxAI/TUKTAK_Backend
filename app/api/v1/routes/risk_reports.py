from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.risk_report import (
    RiskReportCreateRequest,
    RiskReportCreateResponse,
    RiskReportDetail,
    RiskReportDetailResponse,
    RiskReportListItem,
    RiskReportListResponse,
)
from app.services import risk_report as risk_report_service

router = APIRouter(prefix="/risk-reports", tags=["Risk Report"])


@router.post("", response_model=RiskReportCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_risk_report(
    payload: RiskReportCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskReportCreateResponse:
    risk_report = await risk_report_service.create_risk_report(
        db=db,
        user_id=current_user.user_id,
        payload=payload,
    )
    return RiskReportCreateResponse(
        risk_report_id=risk_report.risk_report_id,
        report_status=risk_report.report_status,
        created_at=risk_report.created_at,
    )


@router.get("", response_model=RiskReportListResponse)
async def get_risk_reports(
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskReportListResponse:
    items, total = await risk_report_service.get_risk_reports(
        db=db,
        user_id=current_user.user_id,
        status=status_filter,
        page=page,
        size=size,
    )
    return RiskReportListResponse(
        items=[RiskReportListItem.model_validate(item) for item in items],
        page=page,
        size=size,
        total=total,
    )


@router.get("/{risk_report_id}", response_model=RiskReportDetailResponse)
async def get_risk_report_detail(
    risk_report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskReportDetailResponse:
    risk_report = await risk_report_service.get_risk_report_detail(
        db=db,
        user_id=current_user.user_id,
        risk_report_id=risk_report_id,
    )
    return RiskReportDetailResponse(
        report=RiskReportDetail.model_validate(risk_report)
    )