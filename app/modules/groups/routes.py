from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.services import get_current_user, get_optional_current_user
from .controllers import group_controller
from .schemas import GroupCreate, GroupMemberResponse, GroupResponse, GroupUpdate

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("", response_model=List[GroupResponse])
async def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all discovery and joined groups."""
    return await group_controller.list_groups(db, current_user, skip, limit)


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get group details."""
    return await group_controller.get_group(db, group_id, current_user)


@router.get("/{group_id}/members", response_model=List[GroupMemberResponse])
async def get_group_members(
    group_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all joined members of the group."""
    return await group_controller.get_members(db, group_id)


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_in: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new group community."""
    return await group_controller.create_group(db, current_user, group_in)


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str,
    group_in: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update group details (Admin/Creator only)."""
    return await group_controller.update_group(db, current_user, group_id, group_in)


@router.post("/{group_id}/join", response_model=GroupResponse)
async def join_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a group."""
    return await group_controller.join_group(db, current_user, group_id)


@router.post("/{group_id}/leave", response_model=GroupResponse)
async def leave_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave a group."""
    return await group_controller.leave_group(db, current_user, group_id)


@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a group created by current user."""
    return await group_controller.delete_group(db, current_user, group_id)
