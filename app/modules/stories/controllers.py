from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .schemas import StoryCreate, StoryResponse
from .services import story_service


class StoryController:
    async def list_stories(
        self, db: AsyncSession, current_user: Optional[User]
    ) -> List[StoryResponse]:
        user_id = current_user.id if current_user else None
        return await story_service.get_active_stories(db, user_id)

    async def create_story(
        self, db: AsyncSession, current_user: User, story_in: StoryCreate
    ) -> StoryResponse:
        return await story_service.create_story(db, current_user, story_in)

    async def mark_viewed(self, db: AsyncSession, current_user: User, story_id: str) -> dict:
        await story_service.mark_story_viewed(db, current_user.id, story_id)
        return {"success": True}

    async def delete_story(self, db: AsyncSession, current_user: User, story_id: str) -> dict:
        await story_service.delete_story(db, current_user.id, story_id)
        return {"success": True, "message": "Story deleted successfully"}


story_controller = StoryController()
