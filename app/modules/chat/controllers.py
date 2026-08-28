from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .schemas import ConversationSummary, DirectMessage, SendMessageRequest
from .services import chat_service


class ChatController:
    async def get_messages(
        self, db: AsyncSession, current_user: User, other_user_id: str, skip: int, limit: int
    ) -> List[DirectMessage]:
        return await chat_service.get_messages(
            db=db,
            current_user_id=current_user.id,
            other_user_id=other_user_id,
            skip=skip,
            limit=limit,
        )

    async def send_message(
        self, db: AsyncSession, current_user: User, receiver_id: str, data: SendMessageRequest
    ) -> DirectMessage:
        return await chat_service.send_message(
            db=db,
            sender_id=current_user.id,
            receiver_id=receiver_id,
            text=data.text,
            message_type=data.messageType,
            media_url=data.mediaUrl,
            file_name=data.fileName,
            file_size=data.fileSize,
            duration=data.duration,
        )

    async def mark_as_read(
        self, db: AsyncSession, current_user: User, sender_id: str
    ) -> dict:
        await chat_service.mark_conversation_as_read(db, current_user.id, sender_id)
        return {"success": True}

    async def get_conversations(
        self, db: AsyncSession, current_user: User
    ) -> List[ConversationSummary]:
        return await chat_service.get_conversations(db=db, current_user_id=current_user.id)


chat_controller = ChatController()

