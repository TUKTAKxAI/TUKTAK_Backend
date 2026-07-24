from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessageSummary(BaseModel):
    message_id: int
    chat_room_id: int
    sender_id: int
    message_type: str
    content: str
    client_message_id: str | None = None
    created_at: datetime
    is_mine: bool = False


class ChatRoomSummary(BaseModel):
    chat_room_id: int
    matching_request_id: int
    work_order_id: int
    customer_id: int
    contractor_id: int
    partner_name: str
    matching_request_title: str
    room_status: str
    unread_count: int = 0
    last_message: ChatMessageSummary | None = None
    created_at: datetime
    updated_at: datetime


class ChatRoomListResponse(BaseModel):
    success: bool = True
    items: list[ChatRoomSummary]
    page: int
    size: int
    total: int


class ChatMessageListResponse(BaseModel):
    success: bool = True
    items: list[ChatMessageSummary]
    page: int
    size: int
    total: int


class ChatReadRequest(BaseModel):
    last_read_message_id: int | None = None


class ChatReadResponse(BaseModel):
    success: bool = True
    chat_room_id: int
    last_read_message_id: int | None = None
    last_read_at: datetime


class ChatSendMessage(BaseModel):
    client_message_id: str | None = Field(None, max_length=100)
    content: str = Field(..., min_length=1, max_length=2000)
