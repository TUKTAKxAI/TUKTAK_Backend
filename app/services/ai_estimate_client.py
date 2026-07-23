import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import httpx

from app.core.settings import settings
from app.db.models import AiEstimate


@dataclass
class AiEstimateServiceResult:
    response_status: str
    code: str
    message: str
    missing_info: list[str] = field(default_factory=list)


async def complete_ai_estimate_with_ai_service(
    estimate: AiEstimate,
    image_paths: list[str] | None = None,
    image_s3_keys: list[str] | None = None,
) -> AiEstimateServiceResult:
    payload = {
        "request_id": str(estimate.estimate_id),
        "description": estimate.description,
        "image_urls": estimate.image_urls or [],
        "image_paths": image_paths or [],
        "image_s3_keys": image_s3_keys or [],
        "main_category_hint": None if estimate.main_category == "UNKNOWN" else estimate.main_category,
        "region_code": str(estimate.region_code_id) if estimate.region_code_id is not None else None,
    }

    url = f"{settings.ai_service_url.rstrip('/')}/api/v1/ai/estimates"
    async with httpx.AsyncClient(timeout=settings.ai_service_timeout_seconds) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    status = str(data.get("status") or "service_error")
    code = str(data.get("code") or "ESTIMATE_SERVICE_ERROR")
    message = str(data.get("message") or "AI estimate service returned an empty message.")
    missing_info = _extract_missing_info(data)

    if status == "completed" and data.get("success") is True:
        _apply_completed_estimate(estimate, data.get("estimate") or {})
        return AiEstimateServiceResult(status, code, message, missing_info)

    if status == "needs_more_info":
        estimate.estimate_status = "NEEDS_MORE_INFO"
    else:
        estimate.estimate_status = "FAILED"

    estimate.ai_summary = json.dumps(
        {
            "response_status": status,
            "code": code,
            "message": message,
            "missing_info": missing_info,
        },
        ensure_ascii=False,
    )
    return AiEstimateServiceResult(status, code, message, missing_info)


def _apply_completed_estimate(estimate: AiEstimate, ai_estimate: dict[str, Any]) -> None:
    expected_duration = int(ai_estimate.get("expected_duration_minutes") or 0)
    estimate.main_category = ai_estimate.get("main_category") or estimate.main_category or "REPAIR"
    estimate.object_label = ai_estimate.get("object_label") or "UNKNOWN"
    estimate.problem_label = ai_estimate.get("problem_label") or "UNKNOWN"
    estimate.repair_task_name = ai_estimate.get("repair_task") or "AI estimate"
    estimate.severity = _severity_from_confidence(ai_estimate.get("confidence_score"))
    estimate.min_price = Decimal(str(ai_estimate.get("expected_price_min") or 0))
    estimate.max_price = Decimal(str(ai_estimate.get("expected_price_max") or 0))
    estimate.estimated_minutes_min = expected_duration
    estimate.estimated_minutes_max = expected_duration
    estimate.confidence_score = Decimal(str(ai_estimate.get("confidence_score") or 0)).quantize(Decimal("0.0001"))
    estimate.ai_summary = ai_estimate.get("summary") or _build_completed_summary(ai_estimate)
    estimate.estimate_status = "COMPLETED"


def _build_completed_summary(ai_estimate: dict[str, Any]) -> str:
    warnings = ai_estimate.get("warnings") or []
    method = ai_estimate.get("estimate_method") or "ai_service"
    summary = {
        "estimate_method": method,
        "validity_label": ai_estimate.get("validity_label"),
        "warnings": warnings,
    }
    return json.dumps(summary, ensure_ascii=False)


def _extract_missing_info(data: dict[str, Any]) -> list[str]:
    error_missing = data.get("error", {}).get("missing_info") if isinstance(data.get("error"), dict) else None
    estimate_missing = data.get("estimate", {}).get("missing_info") if isinstance(data.get("estimate"), dict) else None
    missing_info = error_missing or estimate_missing or data.get("missing_info") or []
    return [str(item) for item in missing_info if item]


def _severity_from_confidence(confidence: Any) -> str:
    try:
        score = float(confidence or 0)
    except (TypeError, ValueError):
        return "UNKNOWN"
    if score >= 0.85:
        return "LOW"
    if score >= 0.65:
        return "MEDIUM"
    return "HIGH"
