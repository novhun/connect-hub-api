import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.modules.auth.models import User
from app.modules.auth.schemas import UserResponse
from app.modules.posts.services import format_relative_time
from .models import Notification
from .schemas import NotificationResponse

logger = logging.getLogger("connect_hub.notifications")


class NotificationService:
    async def get_notifications(
        self, db: AsyncSession, current_user: User, skip: int = 0, limit: int = 50
    ) -> List[NotificationResponse]:
        stmt = (
            select(Notification)
            .options(selectinload(Notification.sender))
            .where(Notification.recipient_id == current_user.id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        notifs = result.scalars().all()

        formatted_list = []
        for n in notifs:
            sender_resp = (
                UserResponse.model_validate(n.sender)
                if n.sender
                else UserResponse(
                    id=n.sender_id,
                    name="ConnectHub User",
                    email="",
                    role="Member",
                    isOnline=False,
                    isActive=True,
                )
            )
            formatted_list.append(
                NotificationResponse(
                    id=n.id,
                    user=sender_resp,
                    type=n.type,
                    content=n.content,
                    target=n.target,
                    timestamp=format_relative_time(n.created_at),
                    isRead=n.is_read,
                )
            )
        return formatted_list

    async def create_notification(
        self,
        db: AsyncSession,
        recipient_id: str,
        sender_id: str,
        type: str,
        content: str,
        target: Optional[str] = None,
    ) -> Notification:
        notif = Notification(
            recipient_id=recipient_id,
            sender_id=sender_id,
            type=type,
            content=content,
            target=target,
            is_read=False,
        )
        db.add(notif)
        await db.commit()
        await db.refresh(notif)
        return notif

    async def create_and_send_notification(
        self,
        db: AsyncSession,
        recipient_id: str,
        sender_id: str,
        type: str,
        content: str,
        target: Optional[str] = None,
    ) -> Optional[NotificationResponse]:
        """
        Creates a persistent notification in DB and immediately pushes it
        to the recipient's active WebSocket connection in real time.
        """
        if not recipient_id or not sender_id or recipient_id == sender_id:
            return None

        try:
            notif = Notification(
                recipient_id=recipient_id,
                sender_id=sender_id,
                type=type,
                content=content,
                target=target,
                is_read=False,
            )
            db.add(notif)
            await db.commit()
            await db.refresh(notif)

            sender_user = await db.get(User, sender_id)
            if sender_user:
                sender_resp = UserResponse.model_validate(sender_user)
            else:
                sender_resp = UserResponse(
                    id=sender_id,
                    name="ConnectHub User",
                    email="",
                    role="Member",
                    isOnline=False,
                    isActive=True,
                )

            notif_resp = NotificationResponse(
                id=notif.id,
                user=sender_resp,
                type=notif.type,
                content=notif.content,
                target=notif.target,
                timestamp="Just now",
                isRead=False,
            )

            # Broadcast via WebSocket in real-time
            from app.modules.chat.services import chat_manager
            await chat_manager.send_personal_message(
                recipient_id,
                {
                    "type": "NOTIFICATION",
                    "notification": notif_resp.model_dump(),
                },
            )
            logger.info(f"Delivered real-time notification to user {recipient_id}: {type} - {content}")
            return notif_resp
        except Exception as e:
            logger.error(f"Error creating/sending real-time notification to {recipient_id}: {e}", exc_info=True)
            return None

    async def mark_read(self, db: AsyncSession, current_user: User, notif_id: str) -> bool:
        stmt = select(Notification).where(
            Notification.id == notif_id, Notification.recipient_id == current_user.id
        )
        result = await db.execute(stmt)
        notif = result.scalars().first()
        if notif:
            notif.is_read = True
            await db.commit()

            # Broadcast live state update to user's active devices
            try:
                from app.modules.chat.services import chat_manager
                await chat_manager.send_personal_message(
                    current_user.id,
                    {
                        "type": "NOTIFICATION_READ",
                        "notificationId": notif_id,
                    },
                )
            except Exception:
                pass
        return True

    async def mark_all_read(self, db: AsyncSession, current_user: User) -> bool:
        stmt = select(Notification).where(
            Notification.recipient_id == current_user.id, Notification.is_read == False
        )
        result = await db.execute(stmt)
        notifs = result.scalars().all()
        for n in notifs:
            n.is_read = True
        await db.commit()

        try:
            from app.modules.chat.services import chat_manager
            await chat_manager.send_personal_message(
                current_user.id,
                {
                    "type": "NOTIFICATIONS_ALL_READ",
                },
            )
        except Exception:
            pass
        return True


notification_service = NotificationService()

