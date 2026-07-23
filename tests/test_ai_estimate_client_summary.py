import asyncio
from decimal import Decimal

import app.services.ai_estimate_client as ai_estimate_client
from app.services.ai_estimate_client import _apply_completed_estimate


class EstimateStub:
    main_category = "UNKNOWN"
    object_label = "UNKNOWN"
    problem_label = "UNKNOWN"
    repair_task_name = "AI estimate"
    severity = "UNKNOWN"
    min_price = Decimal("0")
    max_price = Decimal("0")
    estimated_minutes_min = 0
    estimated_minutes_max = 0
    confidence_score = Decimal("0")
    ai_summary = None
    estimate_status = "PROCESSING"


def test_apply_completed_estimate_persists_llm_summary():
    estimate = EstimateStub()

    _apply_completed_estimate(
        estimate,
        {
            "main_category": "도배/벽면",
            "object_label": "벽",
            "problem_label": "균열",
            "repair_task": "벽면 보수",
            "expected_price_min": 100000,
            "expected_price_max": 220000,
            "expected_duration_minutes": 120,
            "confidence_score": 0.82,
            "summary": "부분 보수 기준의 AI 견적입니다.",
        },
    )

    assert estimate.estimate_status == "COMPLETED"
    assert estimate.ai_summary == "부분 보수 기준의 AI 견적입니다."


def test_complete_ai_estimate_sends_s3_keys(monkeypatch):
    estimate = EstimateStub()
    estimate.estimate_id = 123
    estimate.description = "wallpaper repair"
    estimate.image_urls = ["s3://bucket/ai-estimates/1/123/image.jpg"]
    estimate.region_code_id = None

    captured = {}

    class ResponseStub:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "success": False,
                "status": "needs_more_info",
                "code": "ESTIMATE_NEEDS_MORE_INFO",
                "message": "missing",
                "missing_info": ["repair_symptom"],
            }

    class ClientStub:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            captured["url"] = url
            captured["json"] = json
            return ResponseStub()

    monkeypatch.setattr(ai_estimate_client.httpx, "AsyncClient", ClientStub)

    asyncio.run(
        ai_estimate_client.complete_ai_estimate_with_ai_service(
            estimate,
            image_s3_keys=["ai-estimates/1/123/image.jpg"],
        )
    )

    assert captured["json"]["image_paths"] == []
    assert captured["json"]["image_s3_keys"] == ["ai-estimates/1/123/image.jpg"]
