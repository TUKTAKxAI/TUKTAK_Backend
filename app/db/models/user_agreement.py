from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import BIGINT_PK


class UserAgreement(Base):
    __tablename__ = "user_agreements"
    __table_args__ = (
        UniqueConstraint("user_id", "terms_type", "terms_version", name="uq_user_agreement_version"),
    )

    agreement_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_PK, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    terms_type: Mapped[str] = mapped_column(String(50), nullable=False)
    terms_version: Mapped[str] = mapped_column(String(20), nullable=False)
    terms_title: Mapped[str] = mapped_column(String(150), nullable=False)
    terms_content_url: Mapped[str | None] = mapped_column(String(500))
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_agreed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    agreed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="agreements")
