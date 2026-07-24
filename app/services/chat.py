from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    ChatMessage,
    ChatRoom,
    ChatRoomMember,
    ContractorProfile,
    MatchingRequest,
    User,
    WorkOrder,
)
from app.schemas.chat import ChatMessageSummary, ChatReadRequest, ChatRoomSummary, ChatSendMessage
from app.services.matching_common import pagination


def _message_summary(message: ChatMessage, current_user: User) -> ChatMessageSummary:
    return ChatMessageSummary(
        message_id=message.message_id,
        chat_room_id=message.chat_room_id,
        sender_id=message.sender_id,
        message_type=message.message_type,
        content=message.content,
        client_message_id=message.client_message_id,
        created_at=message.created_at,
        is_mine=message.sender_id == current_user.user_id,
    )


async def create_room_for_work_order(
    db: AsyncSession,
    work_order: WorkOrder,
) -> ChatRoom:
    existing = await db.scalar(
        select(ChatRoom).where(ChatRoom.work_order_id == work_order.work_order_id)
    )
    if existing is not None:
        return existing

    room = ChatRoom(
        matching_request_id=work_order.matching_request_id,
        work_order_id=work_order.work_order_id,
        customer_id=work_order.customer_id,
        contractor_id=work_order.contractor_id,
        room_status="OPEN",
    )
    db.add(room)
    await db.flush()
    db.add_all(
        [
            ChatRoomMember(chat_room_id=room.chat_room_id, user_id=room.customer_id),
            ChatRoomMember(chat_room_id=room.chat_room_id, user_id=room.contractor_id),
        ]
    )
    return room


async def require_room_member(
    db: AsyncSession,
    current_user: User,
    chat_room_id: int,
) -> ChatRoom:
    room = await db.scalar(
        select(ChatRoom).where(
            ChatRoom.chat_room_id == chat_room_id,
            or_(
                ChatRoom.customer_id == current_user.user_id,
                ChatRoom.contractor_id == current_user.user_id,
            ),
        )
    )
    if room is None:
        raise HTTPException(status_code=404, detail="Chat room not found")
    return room


async def list_chat_rooms(
    db: AsyncSession,
    current_user: User,
    page: int,
    size: int,
) -> tuple[list[ChatRoomSummary], int, int, int]:
    page, size = pagination(page, size)
    member_filter = or_(
        ChatRoom.customer_id == current_user.user_id,
        ChatRoom.contractor_id == current_user.user_id,
    )
    total = await db.scalar(select(func.count()).select_from(ChatRoom).where(member_filter))
    result = await db.execute(
        select(
            ChatRoom,
            MatchingRequest.title,
            WorkOrder.work_order_status,
            User.name,
            User.nickname,
            ContractorProfile.business_name,
        )
        .join(MatchingRequest, MatchingRequest.matching_request_id == ChatRoom.matching_request_id)
        .join(WorkOrder, WorkOrder.work_order_id == ChatRoom.work_order_id)
        .join(User, User.user_id == ChatRoom.customer_id)
        .outerjoin(ContractorProfile, ContractorProfile.contractor_id == ChatRoom.contractor_id)
        .where(member_filter)
        .order_by(ChatRoom.updated_at.desc(), ChatRoom.chat_room_id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    rooms: list[ChatRoomSummary] = []
    for room, title, work_order_status, customer_name, customer_nickname, business_name in result.all():
        last_message = await db.scalar(
            select(ChatMessage)
            .where(ChatMessage.chat_room_id == room.chat_room_id, ChatMessage.deleted_at.is_(None))
            .order_by(ChatMessage.message_id.desc())
            .limit(1)
        )
        member = await db.scalar(
            select(ChatRoomMember).where(
                ChatRoomMember.chat_room_id == room.chat_room_id,
                ChatRoomMember.user_id == current_user.user_id,
            )
        )
        unread_filters = [
            ChatMessage.chat_room_id == room.chat_room_id,
            ChatMessage.sender_id != current_user.user_id,
            ChatMessage.deleted_at.is_(None),
        ]
        if member and member.last_read_message_id:
            unread_filters.append(ChatMessage.message_id > member.last_read_message_id)
        unread_count = await db.scalar(select(func.count()).select_from(ChatMessage).where(*unread_filters))

        partner_name = (
            customer_name or customer_nickname or "고객"
            if current_user.user_id == room.contractor_id
            else business_name or "시공자"
        )
        rooms.append(
            ChatRoomSummary(
                chat_room_id=room.chat_room_id,
                matching_request_id=room.matching_request_id,
                work_order_id=room.work_order_id,
                customer_id=room.customer_id,
                contractor_id=room.contractor_id,
                partner_name=partner_name,
                matching_request_title=title,
                room_status=room.room_status,
                work_order_status=work_order_status,
                can_send_messages=room.room_status == "OPEN" and work_order_status == "IN_PROGRESS",
                unread_count=int(unread_count or 0),
                last_message=_message_summary(last_message, current_user) if last_message else None,
                created_at=room.created_at,
                updated_at=room.updated_at,
            )
        )
    return rooms, page, size, int(total or 0)


async def list_messages(
    db: AsyncSession,
    current_user: User,
    chat_room_id: int,
    before_message_id: int | None,
    page: int,
    size: int,
) -> tuple[list[ChatMessageSummary], int, int, int]:
    await require_room_member(db, current_user, chat_room_id)
    page, size = pagination(page, size)
    filters = [ChatMessage.chat_room_id == chat_room_id, ChatMessage.deleted_at.is_(None)]
    if before_message_id:
        filters.append(ChatMessage.message_id < before_message_id)

    total = await db.scalar(select(func.count()).select_from(ChatMessage).where(*filters))
    result = await db.execute(
        select(ChatMessage)
        .where(*filters)
        .order_by(ChatMessage.message_id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    messages = [_message_summary(message, current_user) for message in reversed(result.scalars().all())]
    return messages, page, size, int(total or 0)


async def create_message(
    db: AsyncSession,
    current_user: User,
    chat_room_id: int,
    payload: ChatSendMessage,
) -> ChatMessage:
    room = await require_room_member(db, current_user, chat_room_id)
    work_order_status = await db.scalar(
        select(WorkOrder.work_order_status).where(WorkOrder.work_order_id == room.work_order_id)
    )
    if room.room_status != "OPEN" or work_order_status != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail="Chat is available only while work is in progress")

    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="Message content is required")

    if payload.client_message_id:
        existing = await db.scalar(
            select(ChatMessage).where(
                ChatMessage.chat_room_id == chat_room_id,
                ChatMessage.sender_id == current_user.user_id,
                ChatMessage.client_message_id == payload.client_message_id,
            )
        )
        if existing is not None:
            return existing

    message = ChatMessage(
        chat_room_id=chat_room_id,
        sender_id=current_user.user_id,
        message_type="TEXT",
        content=content,
        client_message_id=payload.client_message_id,
    )
    room.updated_at = datetime.now(timezone.utc)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def mark_room_read(
    db: AsyncSession,
    current_user: User,
    chat_room_id: int,
    payload: ChatReadRequest,
) -> ChatRoomMember:
    await require_room_member(db, current_user, chat_room_id)
    member = await db.scalar(
        select(ChatRoomMember).where(
            ChatRoomMember.chat_room_id == chat_room_id,
            ChatRoomMember.user_id == current_user.user_id,
        )
    )
    if member is None:
        member = ChatRoomMember(chat_room_id=chat_room_id, user_id=current_user.user_id)
        db.add(member)

    last_read_message_id = payload.last_read_message_id
    if last_read_message_id is None:
        last_read_message_id = await db.scalar(
            select(func.max(ChatMessage.message_id)).where(ChatMessage.chat_room_id == chat_room_id)
        )

    member.last_read_message_id = last_read_message_id
    member.last_read_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(member)
    return member
