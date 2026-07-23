"""Seed service task catalog.

Revision ID: 20260710_0001
Revises: 20260629_0002
Create Date: 2026-07-10
"""

from typing import Sequence

from alembic import op

revision: str = "20260710_0001"
down_revision: str | None = "20260629_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


SERVICE_TASKS = [
    ("aircon_inspection", "에어컨 점검", "가전/설비", 10),
    ("remote_receiver_inspection", "리모컨/수신부 점검", "가전/설비", 20),
    ("appliance_inspection", "가전 점검", "가전/설비", 30),
    ("boiler_inspection", "보일러 점검", "가전/설비", 40),
    ("water_heater_inspection", "온수기 점검", "가전/설비", 50),
    ("leak_inspection", "누수 점검", "배관/수도", 60),
    ("sink_under_leak_inspection", "싱크대 하부 누수 점검", "배관/수도", 70),
    ("bathroom_leak_inspection", "욕실 누수 점검", "배관/수도", 80),
    ("faucet_replacement", "수전 교체", "배관/수도", 90),
    ("pipe_replacement", "배관 교체", "배관/수도", 100),
    ("drain_clog_resolution", "배수구 막힘 해결", "배관/수도", 110),
    ("sewer_clog_resolution", "하수구 막힘 해결", "배관/수도", 120),
    ("silicone_rework", "실리콘 재시공", "인테리어/보수", 130),
    ("mold_removal", "곰팡이 제거", "인테리어/보수", 140),
    ("wall_repair", "벽면 보수", "인테리어/보수", 150),
    ("wallpaper", "도배", "인테리어/보수", 160),
    ("paint_repair", "페인트 보수", "인테리어/보수", 170),
    ("tile_replacement", "타일 교체", "인테리어/보수", 180),
    ("flooring_repair", "바닥재 보수", "인테리어/보수", 190),
    ("wood_vinyl_floor_repair", "마루/장판 보수", "인테리어/보수", 200),
    ("lighting_replacement", "조명 교체", "전기", 210),
    ("outlet_switch_repair", "콘센트/스위치 수리", "전기", 220),
    ("breaker_inspection", "차단기 점검", "전기", 230),
    ("door_repair", "문 수리", "문/창호", 240),
    ("doorlock_repair", "도어락 수리", "문/창호", 250),
    ("window_sash_repair", "창문/샷시 수리", "문/창호", 260),
    ("screen_replacement", "방충망 교체", "문/창호", 270),
    ("furniture_repair", "가구 수리", "가구/설치", 280),
    ("installation_work", "설치 작업", "가구/설치", 290),
    ("replacement_work", "교체 작업", "기타", 300),
    ("site_inspection", "현장 점검", "기타", 310),
    ("other_work", "기타 작업", "기타", 320),
    ("unavailable", "작업 불가", "기타", 330),
]


def upgrade() -> None:
    values_sql = ",\n".join(
        "        "
        f"(NULL, '{task_code}', '{task_name}', '{main_category}', NULL, NULL, 0, 1, {sort_order}, NOW(), NOW())"
        for task_code, task_name, main_category, sort_order in SERVICE_TASKS
    )
    op.execute(
        f"""
        INSERT INTO service_tasks (
            parent_task_id,
            task_code,
            task_name,
            main_category,
            description,
            base_unit,
            requires_license,
            is_active,
            sort_order,
            created_at,
            updated_at
        )
        VALUES
{values_sql}
        ON DUPLICATE KEY UPDATE
            task_name = VALUES(task_name),
            main_category = VALUES(main_category),
            sort_order = VALUES(sort_order),
            is_active = VALUES(is_active),
            updated_at = NOW()
        """
    )


def downgrade() -> None:
    task_codes = ", ".join(f"'{task_code}'" for task_code, _, _, _ in SERVICE_TASKS)
    op.execute(f"DELETE FROM service_tasks WHERE task_code IN ({task_codes})")
