from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.modules.auth.models import User
from app.modules.auth.schemas import UserResponse
from app.modules.posts.services import format_relative_time
from .models import Notification
from .schemas import NotificationResponse, NotificationType


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

        return [
            NotificationResponse(
                id=n.id,
                user=UserResponse.model_validate(n.sender),
                type=n.type,  # type: ignore
                content=n.content,
                target=n.target,
                timestamp=format_relative_time(n.created_at),
                isRead=n.is_read,
            )
            for n in notifs
        ]

    async def create_notification(
        self,
        db: AsyncSession,
        recipient_id: str,
        sender_id: str,
        type: NotificationType,
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

    async def mark_read(self, db: AsyncSession, current_user: User, notif_id: str) -> bool:
        stmt = select(Notification).where(
            Notification.id == notif_id, Notification.recipient_id == current_user.id
        )
        result = await db.execute(stmt)
        notif = result.scalars().first()
        if notif:
            notif.is_read = True
            await db.commit()
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
        return True


notification_service = NotificationService()
