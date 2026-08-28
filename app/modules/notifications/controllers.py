from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .schemas import NotificationResponse
from .services import notification_service


class NotificationController:
    async def list_notifications(
        self, db: AsyncSession, current_user: User, skip: int, limit: int
    ) -> List[NotificationResponse]:
        return await notification_service.get_notifications(db, current_user, skip, limit)

    async def mark_read(self, db: AsyncSession, current_user: User, notif_id: str) -> dict:
        await notification_service.mark_read(db, current_user, notif_id)
        return {"success": True}

    async def mark_all_read(self, db: AsyncSession, current_user: User) -> dict:
        await notification_service.mark_all_read(db, current_user)
        return {"success": True}


notification_controller = NotificationController()
