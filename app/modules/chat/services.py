import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import WebSocket
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.modules.auth.models import User
from app.modules.auth.schemas import UserResponse
from app.modules.posts.services import format_relative_time
from .models import Message
from .schemas import ConversationSummary, DirectMessage

logger = logging.getLogger("connect_hub.chat")


class ChatManager:
    def __init__(self):
        # Maps user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected to Chat WebSocket.")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected from Chat WebSocket.")

    def is_online(self, user_id: str) -> bool:
        return user_id in self.active_connections

    async def send_personal_message(self, receiver_id: str, message_payload: dict) -> bool:
        if receiver_id in self.active_connections:
            ws = self.active_connections[receiver_id]
            try:
                await ws.send_text(json.dumps(message_payload))
                return True
            except Exception as e:
                logger.warning(f"Error delivering websocket message to {receiver_id}: {e}")
                return False
        return False


chat_manager = ChatManager()


class ChatService:
    def _format_time(self, dt: Optional[datetime]) -> str:
        if not dt:
            return ""
        return dt.strftime("%I:%M %p").lstrip("0")

    async def get_messages(
        self, db: AsyncSession, current_user_id: str, other_user_id: str, skip: int = 0, limit: int = 100
    ) -> List[DirectMessage]:
        stmt = (
            select(Message)
            .where(
                or_(
                    (Message.sender_id == current_user_id) & (Message.receiver_id == other_user_id),
                    (Message.sender_id == other_user_id) & (Message.receiver_id == current_user_id),
                )
            )
            .order_by(Message.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        messages = result.scalars().all()

        return [
            DirectMessage(
                id=m.id,
                senderId=m.sender_id,
                text=m.text,
                timestamp=self._format_time(m.created_at),
                isMe=m.sender_id == current_user_id,
            )
            for m in messages
        ]

    async def send_message(
        self, db: AsyncSession, sender_id: str, receiver_id: str, text: str
    ) -> DirectMessage:
        if not text.strip():
            raise ValueError("Message text cannot be empty.")

        new_msg = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            text=text.strip(),
            is_read=False,
        )
        db.add(new_msg)
        await db.commit()
        await db.refresh(new_msg)

        formatted = DirectMessage(
            id=new_msg.id,
            senderId=new_msg.sender_id,
            text=new_msg.text,
            timestamp=self._format_time(new_msg.created_at),
            isMe=True,
        )

        # Broadcast via WebSocket in real-time
        await chat_manager.send_personal_message(
            receiver_id,
            {
                "type": "NEW_MESSAGE",
                "message": {
                    "id": new_msg.id,
                    "senderId": sender_id,
                    "text": new_msg.text,
                    "timestamp": self._format_time(new_msg.created_at),
                    "isMe": False,
                },
            },
        )

        return formatted

    async def mark_conversation_as_read(
        self, db: AsyncSession, current_user_id: str, sender_id: str
    ) -> bool:
        stmt = (
            select(Message)
            .where(
                Message.sender_id == sender_id,
                Message.receiver_id == current_user_id,
                Message.is_read == False,
            )
        )
        result = await db.execute(stmt)
        unread = result.scalars().all()
        for msg in unread:
            msg.is_read = True
        await db.commit()
        return True


chat_service = ChatService()
