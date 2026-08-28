from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.schemas import UserResponse
from app.modules.auth.services import get_current_user
from .controllers import user_controller
from .schemas import PresenceUpdate, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    query: Optional[str] = None,
    only_online: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """List users for explore/contacts/messenger."""
    return await user_controller.list_users(
        db=db, skip=skip, limit=limit, query=query, only_online=only_online
    )


@router.get("/profile/{user_id}", response_model=UserResponse)
async def get_user_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get a user profile by ID."""
    return await user_controller.get_user_profile(db=db, user_id=user_id)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile information."""
    return await user_controller.update_profile(db=db, current_user=current_user, data=data)


@router.patch("/presence", response_model=UserResponse)
async def update_presence(
    data: PresenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update online/offline presence status."""
    return await user_controller.update_presence(db=db, current_user=current_user, data=data)
