from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .schemas import (
    ConversationSummary,
    CreateGroupChatRequest,
    DirectMessage,
    GroupChatMessageResponse,
    GroupChatSummary,
    InviteMembersRequest,
    SendGroupMessageRequest,
    SendMessageRequest,
    UpdateGroupChatRequest,
)
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

    # --- GROUP CHATS ---

    async def create_group_chat(
        self, db: AsyncSession, current_user: User, data: CreateGroupChatRequest
    ) -> GroupChatSummary:
        return await chat_service.create_group_chat(db=db, creator=current_user, data=data)

    async def get_user_group_chats(
        self, db: AsyncSession, current_user: User
    ) -> List[GroupChatSummary]:
        return await chat_service.get_user_group_chats(db=db, current_user_id=current_user.id)

    async def get_group_chat(
        self, db: AsyncSession, current_user: User, group_id: str
    ) -> GroupChatSummary:
        return await chat_service.get_group_chat(db=db, current_user_id=current_user.id, group_id=group_id)

    async def update_group_chat(
        self, db: AsyncSession, current_user: User, group_id: str, data: UpdateGroupChatRequest
    ) -> GroupChatSummary:
        return await chat_service.update_group_chat(db=db, current_user=current_user, group_id=group_id, data=data)

    async def invite_members(
        self, db: AsyncSession, current_user: User, group_id: str, data: InviteMembersRequest
    ) -> GroupChatSummary:
        return await chat_service.invite_members(
            db=db, current_user=current_user, group_id=group_id, member_ids=data.memberIds
        )

    async def join_by_invite_code(
        self, db: AsyncSession, current_user: User, invite_code: str
    ) -> GroupChatSummary:
        return await chat_service.join_by_invite_code(
            db=db, current_user=current_user, invite_code=invite_code
        )

    async def leave_group_chat(
        self, db: AsyncSession, current_user: User, group_id: str
    ) -> dict:
        return await chat_service.leave_group_chat(db=db, current_user=current_user, group_id=group_id)

    async def get_group_messages(
        self, db: AsyncSession, current_user: User, group_id: str, skip: int, limit: int
    ) -> List[GroupChatMessageResponse]:
        return await chat_service.get_group_messages(
            db=db, current_user_id=current_user.id, group_id=group_id, skip=skip, limit=limit
        )

    async def send_group_message(
        self, db: AsyncSession, current_user: User, group_id: str, data: SendGroupMessageRequest
    ) -> GroupChatMessageResponse:
        return await chat_service.send_group_message(
            db=db,
            current_user=current_user,
            group_id=group_id,
            text=data.text,
            message_type=data.messageType,
            media_url=data.mediaUrl,
            file_name=data.fileName,
            file_size=data.fileSize,
            duration=data.duration,
        )


chat_controller = ChatController()


