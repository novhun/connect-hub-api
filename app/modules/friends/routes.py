from typing import List, Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.schemas import UserResponse
from app.modules.auth.services import get_current_user
from .controllers import friend_controller
from .schemas import FriendRequestResponse, FriendStatusResponse, RespondRequestBody

router = APIRouter(prefix="/friends", tags=["Friends"])


@router.get("", response_model=List[UserResponse])
async def list_friends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's accepted friends."""
    return await friend_controller.list_friends(db, current_user)


@router.get("/requests", response_model=List[FriendRequestResponse])
async def list_requests(
    direction: Literal["incoming", "outgoing"] = Query("incoming"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List pending friend requests (incoming by default)."""
    return await friend_controller.list_requests(db, current_user, direction)


@router.get("/suggestions", response_model=List[UserResponse])
async def list_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List users not yet connected to current user."""
    return await friend_controller.list_suggestions(db, current_user)


@router.get("/status/{user_id}", response_model=FriendStatusResponse)
async def get_status(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the friend relationship status with another user."""
    return await friend_controller.get_status(db, current_user, user_id)


@router.post("/request/{user_id}", response_model=FriendStatusResponse)
async def send_request(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a friend request to a user."""
    return await friend_controller.send_request(db, current_user, user_id)


@router.post("/respond/{request_id}", response_model=FriendStatusResponse)
async def respond_request(
    request_id: str,
    data: RespondRequestBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept or decline an incoming friend request."""
    return await friend_controller.respond_request(db, current_user, request_id, data.accept)


@router.delete("/request/{request_id}")
async def cancel_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending outgoing friend request."""
    return await friend_controller.cancel_request(db, current_user, request_id)


@router.delete("/{user_id}")
async def unfriend(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove an existing friend connection."""
    return await friend_controller.unfriend(db, current_user, user_id)
