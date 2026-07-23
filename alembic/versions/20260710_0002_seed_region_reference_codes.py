"""seed region reference codes

Revision ID: 20260710_0002
Revises: 20260710_0001
Create Date: 2026-07-10 00:02:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "20260710_0002"
down_revision = "20260710_0001"
branch_labels = None
depends_on = None


REGION_GROUP = "REGION"

PARENT_REGIONS = [
    ("11", "서울특별시", 10),
    ("41", "경기도", 20),
    ("28", "인천광역시", 30),
]

CHILD_REGIONS = [
    ("11680", "강남구", "11", 110),
    ("11440", "마포구", "11", 120),
    ("11710", "송파구", "11", 130),
    ("11560", "영등포구", "11", 140),
    ("41570", "김포시", "41", 210),
    ("41280", "고양시", "41", 220),
    ("41190", "부천시", "41", 230),
    ("41110", "수원시", "41", 240),
    ("28260", "서구", "28", 310),
    ("28200", "남동구", "28", 320),
    ("28185", "연수구", "28", 330),
    ("28237", "부평구", "28", 340),
]


def upgrade() -> None:
    for code, name, sort_order in PARENT_REGIONS:
        op.execute(
            f"""
            INSERT INTO reference_codes
                (code_group, code, code_name, parent_code_id, description, sort_order, is_active, metadata_json)
            VALUES
                ('{REGION_GROUP}', '{code}', '{name}', NULL, NULL, {sort_order}, 1, NULL)
            ON DUPLICATE KEY UPDATE
                code_name = VALUES(code_name),
                parent_code_id = VALUES(parent_code_id),
                sort_order = VALUES(sort_order),
                is_active = VALUES(is_active),
                updated_at = CURRENT_TIMESTAMP
            """
        )

    for code, name, parent_code, sort_order in CHILD_REGIONS:
        op.execute(
            f"""
            INSERT INTO reference_codes
                (code_group, code, code_name, parent_code_id, description, sort_order, is_active, metadata_json)
            VALUES
                (
                    '{REGION_GROUP}',
                    '{code}',
                    '{name}',
                    (
                        SELECT parent.code_id
                        FROM reference_codes AS parent
                        WHERE parent.code_group = '{REGION_GROUP}'
                          AND parent.code = '{parent_code}'
                        LIMIT 1
                    ),
                    NULL,
                    {sort_order},
                    1,
                    NULL
                )
            ON DUPLICATE KEY UPDATE
                code_name = VALUES(code_name),
                parent_code_id = VALUES(parent_code_id),
                sort_order = VALUES(sort_order),
                is_active = VALUES(is_active),
                updated_at = CURRENT_TIMESTAMP
            """
        )


def downgrade() -> None:
    child_codes = ", ".join(f"'{code}'" for code, *_ in CHILD_REGIONS)
    parent_codes = ", ".join(f"'{code}'" for code, *_ in PARENT_REGIONS)
    op.execute(
        f"DELETE FROM reference_codes WHERE code_group = '{REGION_GROUP}' AND code IN ({child_codes})"
    )
    op.execute(
        f"DELETE FROM reference_codes WHERE code_group = '{REGION_GROUP}' AND code IN ({parent_codes})"
    )
