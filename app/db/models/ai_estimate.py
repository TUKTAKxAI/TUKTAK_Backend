from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AIEstimate(Base):
    __tablename__ = "ai_estimates"

    # AI 견적 ID
    estimate_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # 견적 요청 사용자
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )

    # ===== 사용자 입력 =====

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 업로드한 이미지 URL 목록
    image_urls: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    main_category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ===== AI 분석 결과 =====

    # 수리 대상
    object_label: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # 문제 유형
    problem_label: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # 예상 작업
    repair_task_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # LOW / MEDIUM / HIGH
    severity: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    min_price: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    max_price: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    estimated_minutes_min: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    estimated_minutes_max: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    ai_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ===== 상태 =====

    # PROCESSING / COMPLETED / FAILED
    estimate_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PROCESSING",
        server_default="PROCESSING",
    )

    # ===== 시간 =====

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )