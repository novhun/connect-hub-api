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
                text=m.text or "",
                timestamp=self._format_time(m.created_at),
                isMe=m.sender_id == current_user_id,
                messageType=m.message_type or "text",
                mediaUrl=m.media_url,
                fileName=m.file_name,
                fileSize=m.file_size,
                duration=m.duration,
            )
            for m in messages
        ]

    async def send_message(
        self,
        db: AsyncSession,
        sender_id: str,
        receiver_id: str,
        text: Optional[str] = "",
        message_type: Optional[str] = "text",
        media_url: Optional[str] = None,
        file_name: Optional[str] = None,
        file_size: Optional[str] = None,
        duration: Optional[str] = None,
    ) -> DirectMessage:
        content_text = (text or "").strip()
        if not content_text and not media_url:
            raise ValueError("Message content or media cannot be empty.")

        new_msg = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            text=content_text,
            message_type=message_type or "text",
            media_url=media_url,
            file_name=file_name,
            file_size=file_size,
            duration=duration,
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
            messageType=new_msg.message_type or "text",
            mediaUrl=new_msg.media_url,
            fileName=new_msg.file_name,
            fileSize=new_msg.file_size,
            duration=new_msg.duration,
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
                    "messageType": new_msg.message_type or "text",
                    "mediaUrl": new_msg.media_url,
                    "fileName": new_msg.file_name,
                    "fileSize": new_msg.file_size,
                    "duration": new_msg.duration,
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

    async def get_conversations(
        self, db: AsyncSession, current_user_id: str
    ) -> List[ConversationSummary]:
        stmt = (
            select(Message)
            .where(
                or_(
                    Message.sender_id == current_user_id,
                    Message.receiver_id == current_user_id,
                )
            )
            .order_by(Message.created_at.desc())
        )
        result = await db.execute(stmt)
        messages = result.scalars().all()

        partner_last_message: Dict[str, Message] = {}
        partner_unread_count: Dict[str, int] = {}
        for m in messages:
            partner_id = m.receiver_id if m.sender_id == current_user_id else m.sender_id
            if partner_id not in partner_last_message:
                partner_last_message[partner_id] = m
                partner_unread_count[partner_id] = 0
            if m.receiver_id == current_user_id and not m.is_read:
                partner_unread_count[partner_id] += 1

        if not partner_last_message:
            return []

        partner_ids = list(partner_last_message.keys())
        users_stmt = select(User).where(User.id.in_(partner_ids))
        users_res = await db.execute(users_stmt)
        users_by_id = {u.id: u for u in users_res.scalars().all()}

        summaries = []
        for pid in partner_ids:
            if pid in users_by_id:
                user_obj = users_by_id[pid]
                last_m = partner_last_message[pid]
                summaries.append(
                    ConversationSummary(
                        user=UserResponse.model_validate(user_obj),
                        lastMessage=last_m.text,
                        lastTimestamp=format_relative_time(last_m.created_at),
                        unreadCount=partner_unread_count.get(pid, 0),
                    )
                )
        return summaries


chat_service = ChatService()
