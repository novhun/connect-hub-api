from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .models import Event, EventAttendee
from .schemas import EventCreate, EventResponse


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def format_event_date(dt: datetime) -> str:
    dt = ensure_utc(dt)
    time_str = dt.strftime("%I:%M %p").lstrip("0")
    return f"{dt.strftime('%a, %b %d')} • {time_str}"


class EventService:
    async def _format_event(
        self, db: AsyncSession, event: Event, current_user_id: Optional[str] = None
    ) -> EventResponse:
        stmt = select(func.count(EventAttendee.id)).where(EventAttendee.event_id == event.id)
        res = await db.execute(stmt)
        attendees_count = res.scalar() or 0

        is_attending = False
        if current_user_id:
            stmt = select(EventAttendee).where(
                EventAttendee.event_id == event.id, EventAttendee.user_id == current_user_id
            )
            res = await db.execute(stmt)
            is_attending = res.scalars().first() is not None

        return EventResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            location=event.location,
            category=event.category,
            coverImage=event.cover_image,
            startAt=ensure_utc(event.start_at).isoformat(),
            date=format_event_date(event.start_at),
            attendeesCount=attendees_count,
            isAttending=is_attending,
            isCreator=bool(current_user_id and current_user_id == event.creator_id),
            creatorId=event.creator_id,
        )

    async def list_events(
        self, db: AsyncSession, current_user_id: Optional[str], skip: int = 0, limit: int = 50
    ) -> List[EventResponse]:
        stmt = select(Event).order_by(Event.start_at.asc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        events = result.scalars().all()
        return [await self._format_event(db, e, current_user_id) for e in events]

    async def get_event_by_id(
        self, db: AsyncSession, event_id: str, current_user_id: Optional[str]
    ) -> EventResponse:
        stmt = select(Event).where(Event.id == event_id)
        result = await db.execute(stmt)
        event = result.scalars().first()
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return await self._format_event(db, event, current_user_id)

    async def create_event(
        self, db: AsyncSession, current_user: User, data: EventCreate
    ) -> EventResponse:
        event = Event(
            creator_id=current_user.id,
            title=data.title.strip(),
            description=data.description,
            location=data.location.strip(),
            category=data.category,
            cover_image=data.coverImage,
            start_at=data.startAt,
        )
        db.add(event)
        await db.flush()

        # Creator auto-attends their own event
        db.add(EventAttendee(event_id=event.id, user_id=current_user.id))
        await db.commit()

        return await self.get_event_by_id(db, event.id, current_user.id)

    async def attend_event(
        self, db: AsyncSession, current_user: User, event_id: str
    ) -> EventResponse:
        stmt = select(Event).where(Event.id == event_id)
        result = await db.execute(stmt)
        if not result.scalars().first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        stmt = select(EventAttendee).where(
            EventAttendee.event_id == event_id, EventAttendee.user_id == current_user.id
        )
        result = await db.execute(stmt)
        if not result.scalars().first():
            db.add(EventAttendee(event_id=event_id, user_id=current_user.id))
            await db.commit()

        return await self.get_event_by_id(db, event_id, current_user.id)

    async def leave_event(
        self, db: AsyncSession, current_user: User, event_id: str
    ) -> EventResponse:
        stmt = select(EventAttendee).where(
            EventAttendee.event_id == event_id, EventAttendee.user_id == current_user.id
        )
        result = await db.execute(stmt)
        attendee = result.scalars().first()
        if attendee:
            await db.delete(attendee)
            await db.commit()
        return await self.get_event_by_id(db, event_id, current_user.id)

    async def delete_event(self, db: AsyncSession, current_user: User, event_id: str) -> bool:
        stmt = select(Event).where(Event.id == event_id)
        result = await db.execute(stmt)
        event = result.scalars().first()
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        if event.creator_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        await db.delete(event)
        await db.commit()
        return True


event_service = EventService()
