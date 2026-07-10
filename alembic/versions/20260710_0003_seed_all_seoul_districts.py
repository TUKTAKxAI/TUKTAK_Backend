"""seed all Seoul district reference codes

Revision ID: 20260710_0003
Revises: 20260710_0002
Create Date: 2026-07-10 00:03:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "20260710_0003"
down_revision = "20260710_0002"
branch_labels = None
depends_on = None


REGION_GROUP = "REGION"
SEOUL_CODE = "11"

SEOUL_DISTRICTS = [
    ("11110", "종로구", 101),
    ("11140", "중구", 102),
    ("11170", "용산구", 103),
    ("11200", "성동구", 104),
    ("11215", "광진구", 105),
    ("11230", "동대문구", 106),
    ("11260", "중랑구", 107),
    ("11290", "성북구", 108),
    ("11305", "강북구", 109),
    ("11320", "도봉구", 110),
    ("11350", "노원구", 111),
    ("11380", "은평구", 112),
    ("11410", "서대문구", 113),
    ("11440", "마포구", 114),
    ("11470", "양천구", 115),
    ("11500", "강서구", 116),
    ("11530", "구로구", 117),
    ("11545", "금천구", 118),
    ("11560", "영등포구", 119),
    ("11590", "동작구", 120),
    ("11620", "관악구", 121),
    ("11650", "서초구", 122),
    ("11680", "강남구", 123),
    ("11710", "송파구", 124),
    ("11740", "강동구", 125),
]


def upgrade() -> None:
    op.execute(
        f"""
        INSERT INTO reference_codes
            (code_group, code, code_name, parent_code_id, description, sort_order, is_active, metadata_json)
        VALUES
            ('{REGION_GROUP}', '{SEOUL_CODE}', '서울특별시', NULL, NULL, 10, 1, NULL)
        ON DUPLICATE KEY UPDATE
            code_name = VALUES(code_name),
            parent_code_id = VALUES(parent_code_id),
            sort_order = VALUES(sort_order),
            is_active = VALUES(is_active),
            updated_at = CURRENT_TIMESTAMP
        """
    )

    for code, name, sort_order in SEOUL_DISTRICTS:
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
                          AND parent.code = '{SEOUL_CODE}'
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
    district_codes = ", ".join(f"'{code}'" for code, *_ in SEOUL_DISTRICTS)
    op.execute(
        f"DELETE FROM reference_codes WHERE code_group = '{REGION_GROUP}' AND code IN ({district_codes})"
    )
