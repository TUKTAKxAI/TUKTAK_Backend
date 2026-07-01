import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.db.models import AiEstimate, RagDocument, RagDocumentChunk, RiskReport, RiskReportSource


async def complete_ai_estimate(estimate: AiEstimate) -> None:
    await _simulate_latency()
    estimate.main_category = estimate.main_category if estimate.main_category != "UNKNOWN" else "REPAIR"
    estimate.object_label = "싱크대 하부 배관"
    estimate.problem_label = "누수 의심"
    estimate.repair_task_name = "배관 누수 점검 및 부분 교체"
    estimate.severity = "MEDIUM"
    estimate.min_price = Decimal("80000.00")
    estimate.max_price = Decimal("180000.00")
    estimate.estimated_minutes_min = 60
    estimate.estimated_minutes_max = 120
    estimate.confidence_score = Decimal("0.8700")
    estimate.ai_summary = (
        "업로드된 사진과 설명 기준으로 싱크대 하부 배관 누수가 의심됩니다. "
        "현장 점검 후 패킹 교체 또는 배관 일부 교체가 필요할 수 있습니다."
    )
    estimate.estimate_status = "COMPLETED"


async def complete_risk_report(db: AsyncSession, risk_report: RiskReport) -> None:
    await _simulate_latency()
    now = datetime.now(timezone.utc)
    risk_report.report_status = "COMPLETED"
    risk_report.risk_score = 42
    risk_report.risk_level = "MEDIUM"
    risk_report.summary = (
        "더미 리스크 분석 결과입니다. 누수 범위가 사진만으로 확정되지 않아 "
        "현장 확인 전 추가 비용 가능성이 있습니다."
    )
    risk_report.risk_items_json = [
        {
            "category": "ADDITIONAL_COST",
            "level": "MEDIUM",
            "title": "숨은 누수 범위 확인 필요",
            "description": "배관 안쪽 또는 하부장 내부 손상 범위에 따라 비용이 달라질 수 있습니다.",
        }
    ]
    risk_report.checklist_json = [
        {"label": "누수 위치를 현장에서 재확인했는가?", "checked": False},
        {"label": "부품비와 출장비 포함 여부를 견적서에 명시했는가?", "checked": False},
    ]
    risk_report.additional_cost_risks_json = [
        {"title": "부품 추가 교체", "expected_impact": "견적 금액 증가 가능"}
    ]
    risk_report.safety_risks_json = [
        {"title": "미끄럼 사고", "expected_impact": "작업 전 주변 물기 제거 필요"}
    ]
    risk_report.contract_risks_json = [
        {"title": "작업 범위 불명확", "expected_impact": "견적서에 포함/제외 항목 명시 필요"}
    ]
    risk_report.field_variable_risks_json = [
        {"title": "하부장 내부 상태", "expected_impact": "현장 확인 후 작업 시간이 변동될 수 있음"}
    ]
    risk_report.model_name = "local-dummy-rag"
    risk_report.model_version = "stub-1"
    risk_report.failure_reason = None
    risk_report.completed_at = now

    document = await db.scalar(
        select(RagDocument)
        .where(RagDocument.document_status == "COMPLETED")
        .order_by(RagDocument.created_at.desc())
        .limit(1)
    )
    if document is None:
        return

    chunk = await db.scalar(
        select(RagDocumentChunk)
        .where(RagDocumentChunk.document_id == document.document_id)
        .order_by(RagDocumentChunk.chunk_index)
        .limit(1)
    )
    db.add(
        RiskReportSource(
            risk_report_id=risk_report.risk_report_id,
            document_id=document.document_id,
            chunk_id=chunk.chunk_id if chunk is not None else None,
            risk_category="ADDITIONAL_COST",
            citation_order=1,
            relevance_score=Decimal("0.910000"),
            quoted_summary="더미 RAG 근거입니다. 실제 RAG 연동 전까지 화면 확인용으로 사용합니다.",
        )
    )


async def complete_rag_document(document: RagDocument) -> RagDocumentChunk:
    await _simulate_latency()
    document.document_status = "COMPLETED"
    return RagDocumentChunk(
        document_id=document.document_id,
        chunk_index=0,
        content_text=(
            "더미 RAG 문서 청크입니다. 실제 벡터화 서비스가 연결되면 이 stub 대신 "
            "문서 파싱 및 임베딩 결과를 저장하면 됩니다."
        ),
        section_title="더미 기준 문서",
        page_number=1,
        vector_collection="rag_documents_stub",
        vector_id=f"stub-rag-document-{document.document_id}-0",
        token_count=42,
        metadata_json={"stub": True, "source": "local-ai-stub"},
    )


async def _simulate_latency() -> None:
    if settings.ai_stub_delay_seconds > 0:
        await asyncio.sleep(settings.ai_stub_delay_seconds)
