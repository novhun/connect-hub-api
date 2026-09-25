import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import HTTPException, WebSocket, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.modules.auth.models import User
from app.modules.auth.schemas import UserResponse
from app.modules.posts.services import format_relative_time
from .models import GroupChat, GroupChatMember, GroupChatMessage, Message
from .schemas import (
    ConversationSummary,
    CreateGroupChatRequest,
    DirectMessage,
    GroupChatMemberResponse,
    GroupChatMessageResponse,
    GroupChatSummary,
    UpdateGroupChatRequest,
)

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

    def get_online_user_ids(self) -> List[str]:
        return list(self.active_connections.keys())

    async def broadcast(self, message_payload: dict, exclude_user_id: Optional[str] = None):
        """Broadcast a real-time event to all active connected users."""
        for uid, ws in list(self.active_connections.items()):
            if exclude_user_id and uid == exclude_user_id:
                continue
            try:
                await ws.send_text(json.dumps(message_payload))
            except Exception as e:
                logger.warning(f"Error broadcasting to user {uid}: {e}")

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

    async def send_to_users(self, user_ids: List[str], message_payload: dict, exclude_user_id: Optional[str] = None):
        """Send message payload to all active users in the user_ids list."""
        for uid in user_ids:
            if exclude_user_id and uid == exclude_user_id:
                continue
            await self.send_personal_message(uid, message_payload)


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

    # =========================================================================
    # Group Chat Services
    # =========================================================================

    async def get_group_member_ids(self, db: AsyncSession, group_id: str) -> List[str]:
        stmt = select(GroupChatMember.user_id).where(GroupChatMember.group_chat_id == group_id)
        res = await db.execute(stmt)
        return [r[0] for r in res.fetchall()]

    async def create_group_chat(
        self,
        db: AsyncSession,
        creator: User,
        data: CreateGroupChatRequest,
    ) -> GroupChatSummary:
        name_str = data.name.strip()
        avatar_url = data.avatar or f"https://api.dicebear.com/7.x/identicon/svg?seed={name_str}"
        group = GroupChat(
            name=name_str,
            avatar=avatar_url,
            description=data.description or "",
            creator_id=creator.id,
        )
        db.add(group)
        await db.flush()

        # Add creator as admin
        creator_member = GroupChatMember(
            group_chat_id=group.id,
            user_id=creator.id,
            role="admin",
        )
        db.add(creator_member)

        # Add initial members (filter out creator if present)
        added_user_ids = {creator.id}
        for uid in data.memberIds:
            if uid and uid not in added_user_ids:
                added_user_ids.add(uid)
                db.add(
                    GroupChatMember(
                        group_chat_id=group.id,
                        user_id=uid,
                        role="member",
                    )
                )

        # Add initial system message
        sys_msg = GroupChatMessage(
            group_chat_id=group.id,
            sender_id=creator.id,
            text=f"{creator.name} created the group chat.",
            message_type="system",
        )
        db.add(sys_msg)

        await db.commit()
        await db.refresh(group)

        summary = await self.get_group_chat(db, creator.id, group.id)

        # Realtime notify all members
        await chat_manager.send_to_users(
            list(added_user_ids),
            {
                "type": "GROUP_CREATED",
                "group": summary.model_dump(),
            },
        )
        return summary

    async def get_user_group_chats(
        self,
        db: AsyncSession,
        current_user_id: str,
    ) -> List[GroupChatSummary]:
        stmt_memberships = select(GroupChatMember.group_chat_id).where(GroupChatMember.user_id == current_user_id)
        res_memberships = await db.execute(stmt_memberships)
        group_ids = [r[0] for r in res_memberships.fetchall()]

        if not group_ids:
            return []

        stmt = (
            select(GroupChat)
            .options(
                selectinload(GroupChat.members).selectinload(GroupChatMember.user),
                selectinload(GroupChat.messages).selectinload(GroupChatMessage.sender),
            )
            .where(GroupChat.id.in_(group_ids))
            .order_by(GroupChat.updated_at.desc())
        )
        res = await db.execute(stmt)
        groups = res.scalars().all()

        summaries = []
        for g in groups:
            sorted_msgs = sorted(g.messages, key=lambda m: m.created_at) if g.messages else []
            last_m = sorted_msgs[-1] if sorted_msgs else None

            members_res = [
                GroupChatMemberResponse(
                    id=m.id,
                    userId=m.user_id,
                    role=m.role,
                    joinedAt=self._format_time(m.joined_at),
                    user=UserResponse.model_validate(m.user),
                )
                for m in g.members
                if m.user
            ]

            last_msg_text = last_m.text if last_m else None
            last_sender_name = last_m.sender.name if last_m and last_m.sender else None
            last_timestamp = format_relative_time(last_m.created_at) if last_m else format_relative_time(g.created_at)

            summaries.append(
                GroupChatSummary(
                    id=g.id,
                    name=g.name,
                    avatar=g.avatar,
                    description=g.description,
                    creatorId=g.creator_id,
                    inviteCode=g.invite_code,
                    membersCount=len(members_res),
                    members=members_res,
                    lastMessage=last_msg_text,
                    lastMessageSender=last_sender_name,
                    lastTimestamp=last_timestamp,
                    unreadCount=0,
                    isGroup=True,
                )
            )

        return summaries

    async def get_group_chat(
        self,
        db: AsyncSession,
        current_user_id: str,
        group_id: str,
    ) -> GroupChatSummary:
        check_stmt = select(GroupChatMember).where(
            GroupChatMember.group_chat_id == group_id,
            GroupChatMember.user_id == current_user_id,
        )
        check_res = await db.execute(check_stmt)
        if not check_res.scalars().first():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        stmt = (
            select(GroupChat)
            .options(
                selectinload(GroupChat.members).selectinload(GroupChatMember.user),
                selectinload(GroupChat.messages).selectinload(GroupChatMessage.sender),
            )
            .where(GroupChat.id == group_id)
        )
        res = await db.execute(stmt)
        g = res.scalars().first()
        if not g:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group chat not found.")

        sorted_msgs = sorted(g.messages, key=lambda m: m.created_at) if g.messages else []
        last_m = sorted_msgs[-1] if sorted_msgs else None

        members_res = [
            GroupChatMemberResponse(
                id=m.id,
                userId=m.user_id,
                role=m.role,
                joinedAt=self._format_time(m.joined_at),
                user=UserResponse.model_validate(m.user),
            )
            for m in g.members
            if m.user
        ]

        return GroupChatSummary(
            id=g.id,
            name=g.name,
            avatar=g.avatar,
            description=g.description,
            creatorId=g.creator_id,
            inviteCode=g.invite_code,
            membersCount=len(members_res),
            members=members_res,
            lastMessage=last_m.text if last_m else None,
            lastMessageSender=last_m.sender.name if last_m and last_m.sender else None,
            lastTimestamp=format_relative_time(last_m.created_at) if last_m else format_relative_time(g.created_at),
            unreadCount=0,
            isGroup=True,
        )

    async def update_group_chat(
        self,
        db: AsyncSession,
        current_user: User,
        group_id: str,
        data: UpdateGroupChatRequest,
    ) -> GroupChatSummary:
        # Check membership and admin role
        stmt = select(GroupChatMember).where(
            GroupChatMember.group_chat_id == group_id,
            GroupChatMember.user_id == current_user.id,
        )
        res = await db.execute(stmt)
        member = res.scalars().first()
        if not member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        group_stmt = select(GroupChat).where(GroupChat.id == group_id)
        g_res = await db.execute(group_stmt)
        group = g_res.scalars().first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group chat not found.")

        if data.name:
            group.name = data.name.strip()
        if data.avatar:
            group.avatar = data.avatar
        if data.description is not None:
            group.description = data.description
        group.updated_at = datetime.now(timezone.utc)

        await db.commit()
        summary = await self.get_group_chat(db, current_user.id, group_id)

        # Broadcast update to group
        member_ids = [m.userId for m in summary.members]
        await chat_manager.send_to_users(
            member_ids,
            {
                "type": "GROUP_UPDATED",
                "group": summary.model_dump(),
            },
        )
        return summary

    async def invite_members(
        self,
        db: AsyncSession,
        current_user: User,
        group_id: str,
        member_ids: List[str],
    ) -> GroupChatSummary:
        check_stmt = select(GroupChatMember).where(
            GroupChatMember.group_chat_id == group_id,
            GroupChatMember.user_id == current_user.id,
        )
        check_res = await db.execute(check_stmt)
        if not check_res.scalars().first():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        all_members_stmt = select(GroupChatMember).where(GroupChatMember.group_chat_id == group_id)
        all_res = await db.execute(all_members_stmt)
        existing_members = all_res.scalars().all()
        existing_uids = {m.user_id for m in existing_members}

        added_uids = []
        for uid in member_ids:
            if uid and uid not in existing_uids:
                existing_uids.add(uid)
                added_uids.append(uid)
                db.add(
                    GroupChatMember(
                        group_chat_id=group_id,
                        user_id=uid,
                        role="member",
                    )
                )

        if added_uids:
            users_res = await db.execute(select(User).where(User.id.in_(added_uids)))
            added_users = users_res.scalars().all()
            names_str = ", ".join(u.name for u in added_users) if added_users else "new members"
            sys_msg = GroupChatMessage(
                group_chat_id=group_id,
                sender_id=current_user.id,
                text=f"{current_user.name} added {names_str} to the group.",
                message_type="system",
            )
            db.add(sys_msg)

        await db.commit()
        summary = await self.get_group_chat(db, current_user.id, group_id)

        await chat_manager.send_to_users(
            list(existing_uids),
            {
                "type": "GROUP_MEMBERS_UPDATED",
                "group": summary.model_dump(),
            },
        )
        return summary

    async def join_by_invite_code(
        self,
        db: AsyncSession,
        current_user: User,
        invite_code: str,
    ) -> GroupChatSummary:
        stmt = select(GroupChat).where(GroupChat.invite_code == invite_code)
        res = await db.execute(stmt)
        group = res.scalars().first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite code.")

        check_stmt = select(GroupChatMember).where(
            GroupChatMember.group_chat_id == group.id,
            GroupChatMember.user_id == current_user.id,
        )
        check_res = await db.execute(check_stmt)
        existing = check_res.scalars().first()

        if not existing:
            db.add(
                GroupChatMember(
                    group_chat_id=group.id,
                    user_id=current_user.id,
                    role="member",
                )
            )
            sys_msg = GroupChatMessage(
                group_chat_id=group.id,
                sender_id=current_user.id,
                text=f"{current_user.name} joined via invite link.",
                message_type="system",
            )
            db.add(sys_msg)
            await db.commit()

        summary = await self.get_group_chat(db, current_user.id, group.id)
        member_ids = [m.userId for m in summary.members]
        await chat_manager.send_to_users(
            member_ids,
            {
                "type": "GROUP_MEMBERS_UPDATED",
                "group": summary.model_dump(),
            },
        )
        return summary

    async def leave_group_chat(
        self,
        db: AsyncSession,
        current_user: User,
        group_id: str,
    ) -> dict:
        stmt = select(GroupChatMember).where(
            GroupChatMember.group_chat_id == group_id,
            GroupChatMember.user_id == current_user.id,
        )
        res = await db.execute(stmt)
        member = res.scalars().first()
        if not member:
            return {"success": True}

        await db.delete(member)
        sys_msg = GroupChatMessage(
            group_chat_id=group_id,
            sender_id=current_user.id,
            text=f"{current_user.name} left the group.",
            message_type="system",
        )
        db.add(sys_msg)
        await db.commit()

        rem_stmt = select(GroupChatMember.user_id).where(GroupChatMember.group_chat_id == group_id)
        rem_res = await db.execute(rem_stmt)
        rem_uids = [r[0] for r in rem_res.fetchall()]
        await chat_manager.send_to_users(
            rem_uids,
            {
                "type": "GROUP_MEMBER_LEFT",
                "groupId": group_id,
                "userId": current_user.id,
                "userName": current_user.name,
            },
        )
        return {"success": True}

    async def get_group_messages(
        self,
        db: AsyncSession,
        current_user_id: str,
        group_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[GroupChatMessageResponse]:
        check_stmt = select(GroupChatMember).where(
            GroupChatMember.group_chat_id == group_id,
            GroupChatMember.user_id == current_user_id,
        )
        check_res = await db.execute(check_stmt)
        if not check_res.scalars().first():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        stmt = (
            select(GroupChatMessage)
            .options(selectinload(GroupChatMessage.sender))
            .where(GroupChatMessage.group_chat_id == group_id)
            .order_by(GroupChatMessage.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        res = await db.execute(stmt)
        messages = res.scalars().all()

        return [
            GroupChatMessageResponse(
                id=m.id,
                groupChatId=m.group_chat_id,
                senderId=m.sender_id,
                sender=UserResponse.model_validate(m.sender)
                if m.sender
                else UserResponse(
                    id=m.sender_id,
                    name="Member",
                    email="member@connecthub.app",
                    role="Member",
                    isOnline=False,
                    isActive=True,
                ),
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

    async def send_group_message(
        self,
        db: AsyncSession,
        current_user: User,
        group_id: str,
        text: Optional[str] = "",
        message_type: Optional[str] = "text",
        media_url: Optional[str] = None,
        file_name: Optional[str] = None,
        file_size: Optional[str] = None,
        duration: Optional[str] = None,
    ) -> GroupChatMessageResponse:
        check_stmt = select(GroupChatMember).where(
            GroupChatMember.group_chat_id == group_id,
            GroupChatMember.user_id == current_user.id,
        )
        check_res = await db.execute(check_stmt)
        if not check_res.scalars().first():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        content_text = (text or "").strip()
        if not content_text and not media_url:
            raise ValueError("Message content or media cannot be empty.")

        new_msg = GroupChatMessage(
            group_chat_id=group_id,
            sender_id=current_user.id,
            text=content_text,
            message_type=message_type or "text",
            media_url=media_url,
            file_name=file_name,
            file_size=file_size,
            duration=duration,
        )
        db.add(new_msg)

        group_stmt = select(GroupChat).where(GroupChat.id == group_id)
        g_res = await db.execute(group_stmt)
        g_obj = g_res.scalars().first()
        if g_obj:
            g_obj.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(new_msg)

        resp = GroupChatMessageResponse(
            id=new_msg.id,
            groupChatId=new_msg.group_chat_id,
            senderId=new_msg.sender_id,
            sender=UserResponse.model_validate(current_user),
            text=new_msg.text,
            timestamp=self._format_time(new_msg.created_at),
            isMe=True,
            messageType=new_msg.message_type or "text",
            mediaUrl=new_msg.media_url,
            fileName=new_msg.file_name,
            fileSize=new_msg.file_size,
            duration=new_msg.duration,
        )

        member_uids = await self.get_group_member_ids(db, group_id)

        await chat_manager.send_to_users(
            member_uids,
            {
                "type": "NEW_GROUP_MESSAGE",
                "groupId": group_id,
                "message": {
                    "id": new_msg.id,
                    "groupChatId": new_msg.group_chat_id,
                    "senderId": new_msg.sender_id,
                    "sender": UserResponse.model_validate(current_user).model_dump(),
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
            exclude_user_id=current_user.id,
        )

        return resp


chat_service = ChatService()

