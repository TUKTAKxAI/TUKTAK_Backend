from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.types import BIGINT_PK


class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    __table_args__ = (
        UniqueConstraint("matching_request_id", name="uq_chat_rooms_matching_request_id"),
        UniqueConstraint("work_order_id", name="uq_chat_rooms_work_order_id"),
        Index("ix_chat_rooms_customer_updated", "customer_id", "updated_at"),
        Index("ix_chat_rooms_contractor_updated", "contractor_id", "updated_at"),
    )

    chat_room_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    matching_request_id: Mapped[int] = mapped_column(
        BIGINT_PK,
        ForeignKey("matching_requests.matching_request_id", ondelete="RESTRICT"),
        nullable=False,
    )
    work_order_id: Mapped[int] = mapped_column(
        BIGINT_PK,
        ForeignKey("work_orders.work_order_id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id: Mapped[int] = mapped_column(
        BIGINT_PK, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False
    )
    contractor_id: Mapped[int] = mapped_column(
        BIGINT_PK,
        ForeignKey("contractor_profiles.contractor_id", ondelete="RESTRICT"),
        nullable=False,
    )
    room_status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN", server_default="OPEN")
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )
    members: Mapped[list["ChatRoomMember"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        UniqueConstraint(
            "chat_room_id",
            "sender_id",
            "client_message_id",
            name="uq_chat_messages_client_message",
        ),
        Index("ix_chat_messages_room_created", "chat_room_id", "created_at"),
        Index("ix_chat_messages_room_id", "chat_room_id", "message_id"),
    )

    message_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    chat_room_id: Mapped[int] = mapped_column(
        BIGINT_PK, ForeignKey("chat_rooms.chat_room_id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[int] = mapped_column(
        BIGINT_PK, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False
    )
    message_type: Mapped[str] = mapped_column(String(20), nullable=False, default="TEXT", server_default="TEXT")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    client_message_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    room: Mapped["ChatRoom"] = relationship(back_populates="messages")


class ChatRoomMember(Base):
    __tablename__ = "chat_room_members"
    __table_args__ = (
        UniqueConstraint("chat_room_id", "user_id", name="uq_chat_room_members_room_user"),
    )

    chat_room_member_id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    chat_room_id: Mapped[int] = mapped_column(
        BIGINT_PK, ForeignKey("chat_rooms.chat_room_id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BIGINT_PK, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False
    )
    last_read_message_id: Mapped[int | None] = mapped_column(BIGINT_PK)
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    room: Mapped["ChatRoom"] = relationship(back_populates="members")
