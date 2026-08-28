from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.services import get_current_user, get_optional_current_user
from .controllers import story_controller
from .schemas import StoryCreate, StoryResponse

router = APIRouter(prefix="/stories", tags=["Stories"])


@router.get("", response_model=List[StoryResponse])
async def list_stories(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all active 24h stories."""
    return await story_controller.list_stories(db, current_user)


@router.post("", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    story_in: StoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish a new story."""
    return await story_controller.create_story(db, current_user, story_in)


@router.post("/{story_id}/view")
async def mark_story_viewed(
    story_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a story as viewed by current user."""
    return await story_controller.mark_viewed(db, current_user, story_id)


@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a story."""
    return await story_controller.delete_story(db, current_user, story_id)
