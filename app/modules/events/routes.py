from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.services import get_current_user, get_optional_current_user
from .controllers import event_controller
from .schemas import EventCreate, EventMemberResponse, EventResponse, EventUpdate

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=List[EventResponse])
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List upcoming community events."""
    return await event_controller.list_events(db, current_user, skip, limit)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get event details."""
    return await event_controller.get_event(db, event_id, current_user)


@router.get("/{event_id}/members", response_model=List[EventMemberResponse])
@router.get("/{event_id}/attendees", response_model=List[EventMemberResponse])
async def get_event_members(
    event_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get list of all members/attendees joining this event."""
    return await event_controller.get_members(db, event_id)


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new community event."""
    return await event_controller.create_event(db, current_user, data)


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit an event created by the current user."""
    return await event_controller.update_event(db, current_user, event_id, data)


@router.post("/{event_id}/attend", response_model=EventResponse)
async def attend_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark current user as attending an event."""
    return await event_controller.attend_event(db, current_user, event_id)


@router.post("/{event_id}/leave", response_model=EventResponse)
async def leave_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove current user from an event's attendees."""
    return await event_controller.leave_event(db, current_user, event_id)


@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an event created by the current user."""
    return await event_controller.delete_event(db, current_user, event_id)
