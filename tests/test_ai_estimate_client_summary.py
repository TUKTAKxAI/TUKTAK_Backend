from decimal import Decimal

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
