from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, DECIMAL, UniqueConstraint, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import BIGINT_PK


class ContractorService(Base):
    __tablename__ = 'contractor_services'

    contractor_service_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    contractor_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey('contractor_profiles.contractor_id'), nullable=False)
    service_task_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey('service_tasks.service_task_id'), nullable=False)
    region_code_id: Mapped[int] = mapped_column(BIGINT_PK, ForeignKey('reference_codes.code_id'), nullable=False)
    experience_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    minimum_visit_fee: Mapped[Optional[float]] = mapped_column(DECIMAL(12, 2), nullable=True)
    service_radius_km: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('contractor_id', 'service_task_id', 'region_code_id', name='uq_contractor_service'),
    )

    profile: Mapped["ContractorProfile"] = relationship("ContractorProfile", back_populates="services")