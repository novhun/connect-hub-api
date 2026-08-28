from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .schemas import EventCreate, EventMemberResponse, EventResponse, EventUpdate
from .services import event_service


class EventController:
    async def list_events(
        self, db: AsyncSession, current_user: Optional[User], skip: int, limit: int
    ) -> List[EventResponse]:
        user_id = current_user.id if current_user else None
        return await event_service.list_events(db, user_id, skip, limit)

    async def get_event(
        self, db: AsyncSession, event_id: str, current_user: Optional[User]
    ) -> EventResponse:
        user_id = current_user.id if current_user else None
        return await event_service.get_event_by_id(db, event_id, user_id)

    async def create_event(
        self, db: AsyncSession, current_user: User, data: EventCreate
    ) -> EventResponse:
        return await event_service.create_event(db, current_user, data)

    async def update_event(
        self, db: AsyncSession, current_user: User, event_id: str, data: EventUpdate
    ) -> EventResponse:
        return await event_service.update_event(db, current_user, event_id, data)

    async def get_members(
        self, db: AsyncSession, event_id: str
    ) -> List[EventMemberResponse]:
        return await event_service.get_event_members(db, event_id)

    async def attend_event(
        self, db: AsyncSession, current_user: User, event_id: str
    ) -> EventResponse:
        return await event_service.attend_event(db, current_user, event_id)

    async def leave_event(
        self, db: AsyncSession, current_user: User, event_id: str
    ) -> EventResponse:
        return await event_service.leave_event(db, current_user, event_id)

    async def delete_event(self, db: AsyncSession, current_user: User, event_id: str) -> dict:
        await event_service.delete_event(db, current_user, event_id)
        return {"success": True, "message": "Event deleted successfully"}


event_controller = EventController()
