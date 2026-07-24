import asyncio
from collections import defaultdict

import jwt
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.security import decode_token
from app.core.settings import settings
from app.db.database import AsyncSessionLocal, get_db
from app.db.models import User
from app.schemas.chat import (
    ChatMessageListResponse,
    ChatMessageSummary,
    ChatReadRequest,
    ChatReadResponse,
    ChatRoomListResponse,
    ChatSendMessage,
)
from app.services import chat as chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])
ws_router = APIRouter(prefix="/ws/chat", tags=["Chat WebSocket"])


class ChatConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[int, dict[WebSocket, int]] = defaultdict(dict)

    async def connect(self, chat_room_id: int, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        self._rooms[chat_room_id][websocket] = user_id

    def disconnect(self, chat_room_id: int, websocket: WebSocket) -> None:
        sockets = self._rooms.get(chat_room_id)
        if not sockets:
            return
        sockets.pop(websocket, None)
        if not sockets:
            self._rooms.pop(chat_room_id, None)

    async def broadcast_message(self, chat_room_id: int, message) -> None:
        sockets = list(self._rooms.get(chat_room_id, {}).items())
        for socket, user_id in sockets:
            summary = ChatMessageSummary(
                message_id=message.message_id,
                chat_room_id=message.chat_room_id,
                sender_id=message.sender_id,
                message_type=message.message_type,
                content=message.content,
                client_message_id=message.client_message_id,
                created_at=message.created_at,
                is_mine=message.sender_id == user_id,
            )
            try:
                await socket.send_json(
                    {
                        "type": "message.created",
                        "message": summary.model_dump(mode="json"),
                    }
                )
            except RuntimeError:
                self.disconnect(chat_room_id, socket)


manager = ChatConnectionManager()


@router.get("/rooms", response_model=ChatRoomListResponse)
async def list_chat_rooms(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatRoomListResponse:
    items, page, size, total = await chat_service.list_chat_rooms(db, current_user, page, size)
    return ChatRoomListResponse(items=items, page=page, size=size, total=total)


@router.get("/rooms/{chat_room_id}/messages", response_model=ChatMessageListResponse)
async def list_messages(
    chat_room_id: int,
    before_message_id: int | None = Query(None, ge=1),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageListResponse:
    items, page, size, total = await chat_service.list_messages(
        db, current_user, chat_room_id, before_message_id, page, size
    )
    return ChatMessageListResponse(items=items, page=page, size=size, total=total)


@router.post("/rooms/{chat_room_id}/read", response_model=ChatReadResponse)
async def mark_room_read(
    chat_room_id: int,
    payload: ChatReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatReadResponse:
    member = await chat_service.mark_room_read(db, current_user, chat_room_id, payload)
    return ChatReadResponse(
        chat_room_id=chat_room_id,
        last_read_message_id=member.last_read_message_id,
        last_read_at=member.last_read_at,
    )


async def _get_websocket_user(websocket: WebSocket, db: AsyncSession) -> User | None:
    token = websocket.query_params.get("token") or websocket.cookies.get(settings.auth_access_cookie_name)
    if not token:
        return None
    try:
        payload = decode_token(token, "access")
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError):
        return None

    return await db.scalar(
        select(User).where(User.user_id == user_id, User.account_status == "ACTIVE")
    )


@ws_router.websocket("/rooms/{chat_room_id}")
async def chat_room_socket(websocket: WebSocket, chat_room_id: int) -> None:
    async with AsyncSessionLocal() as db:
        current_user = await _get_websocket_user(websocket, db)
        if current_user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        try:
            await chat_service.require_room_member(db, current_user, chat_room_id)
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await manager.connect(chat_room_id, websocket, current_user.user_id)
        await websocket.send_json({"type": "connected", "chat_room_id": chat_room_id})
        heartbeat_task = asyncio.create_task(_heartbeat(websocket))
        try:
            while True:
                data = await websocket.receive_json()
                event_type = data.get("type")
                if event_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
                if event_type == "message.read":
                    member = await chat_service.mark_room_read(
                        db,
                        current_user,
                        chat_room_id,
                        ChatReadRequest(last_read_message_id=data.get("last_read_message_id")),
                    )
                    await websocket.send_json(
                        {
                            "type": "message.read",
                            "chat_room_id": chat_room_id,
                            "user_id": current_user.user_id,
                            "last_read_message_id": member.last_read_message_id,
                            "last_read_at": member.last_read_at.isoformat(),
                        }
                    )
                    continue
                if event_type != "message.send":
                    await websocket.send_json({"type": "error", "detail": "Unsupported message type"})
                    continue

                try:
                    payload = ChatSendMessage(
                        client_message_id=data.get("client_message_id"),
                        content=data.get("content") or "",
                    )
                except ValidationError as exc:
                    await websocket.send_json({"type": "error", "detail": exc.errors()})
                    continue

                message = await chat_service.create_message(db, current_user, chat_room_id, payload)
                await manager.broadcast_message(chat_room_id, message)
        except WebSocketDisconnect:
            pass
        finally:
            heartbeat_task.cancel()
            manager.disconnect(chat_room_id, websocket)


async def _heartbeat(websocket: WebSocket) -> None:
    while True:
        await asyncio.sleep(25)
        try:
            await websocket.send_json({"type": "ping"})
        except RuntimeError:
            return
