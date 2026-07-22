from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.db.models import AiEstimate, RiskReport, RiskReportSource


async def complete_risk_report_with_ai_service(
    db: AsyncSession,
    risk_report: RiskReport,
    estimate: AiEstimate,
) -> None:
    payload = {
        "estimate_id": estimate.estimate_id,
        "main_category": estimate.main_category,
        "object_label": estimate.object_label,
        "problem_label": estimate.problem_label,
        "repair_task": estimate.repair_task_name,
        "expected_price_min": int(estimate.min_price or 0),
        "expected_price_max": int(estimate.max_price or 0),
        "expected_duration_minutes": int(estimate.estimated_minutes_max or estimate.estimated_minutes_min or 0),
        "description": estimate.description,
        "ai_summary": estimate.ai_summary,
    }
    url = f"{settings.ai_service_url.rstrip('/')}/api/v1/ai/risk-reports"
    async with httpx.AsyncClient(timeout=settings.ai_service_timeout_seconds) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    report = data.get("risk_report") or {}
    _apply_risk_report_result(risk_report, report)
    for source in report.get("sources") or []:
        _add_risk_report_source(db, risk_report, source)


def _apply_risk_report_result(risk_report: RiskReport, report: dict[str, Any]) -> None:
    now = datetime.now(timezone.utc)
    risk_report.report_status = str(report.get("report_status") or "FAILED")
    risk_report.risk_score = int(report.get("risk_score") or 0)
    risk_report.risk_level = str(report.get("risk_level") or "UNKNOWN")
    risk_report.summary = str(report.get("summary") or "")
    risk_report.risk_items_json = list(report.get("risk_items") or [])
    risk_report.checklist_json = list(report.get("checklist") or [])
    risk_report.additional_cost_risks_json = list(report.get("additional_cost_risks") or [])
    risk_report.safety_risks_json = list(report.get("safety_risks") or [])
    risk_report.contract_risks_json = list(report.get("contract_risks") or [])
    risk_report.field_variable_risks_json = list(report.get("field_variable_risks") or [])
    risk_report.model_name = str(report.get("model_name") or "ai-service-risk-rag")
    risk_report.model_version = report.get("model_version")
    risk_report.failure_reason = report.get("failure_reason")
    risk_report.completed_at = now


def _add_risk_report_source(db: AsyncSession, risk_report: RiskReport, source: dict[str, Any]) -> None:
    document_id = source.get("backend_document_id")
    if document_id is None:
        return
    db.add(
        RiskReportSource(
            risk_report_id=risk_report.risk_report_id,
            document_id=int(document_id),
            chunk_id=source.get("backend_chunk_id"),
            risk_category=str(source.get("risk_category") or "UNKNOWN"),
            citation_order=int(source.get("citation_order") or 0),
            relevance_score=Decimal(str(source.get("relevance_score") or 0)),
            quoted_summary=str(source.get("quoted_summary") or ""),
        )
    )
