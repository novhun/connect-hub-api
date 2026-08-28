from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.modules.auth.models import User
from app.modules.posts.services import format_relative_time
from .models import Story, StoryView
from .schemas import StoryCreate, StoryResponse


class StoryService:
    async def get_active_stories(
        self, db: AsyncSession, current_user_id: Optional[str] = None
    ) -> List[StoryResponse]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(Story)
            .options(selectinload(Story.user), selectinload(Story.views))
            .where(Story.expires_at > now)
            .order_by(Story.created_at.desc())
        )
        result = await db.execute(stmt)
        stories = result.scalars().all()

        formatted = []
        for s in stories:
            viewed = False
            if current_user_id:
                viewed = any(v.user_id == current_user_id for v in s.views)
            formatted.append(
                StoryResponse(
                    id=s.id,
                    userId=s.user_id,
                    userName=s.user.name,
                    userAvatar=s.user.avatar or "https://api.dicebear.com/7.x/avataaars/svg?seed=user",
                    storyImage=s.story_image,
                    timestamp=format_relative_time(s.created_at),
                    caption=s.caption,
                    viewed=viewed,
                )
            )
        return formatted

    async def create_story(
        self, db: AsyncSession, current_user: User, story_in: StoryCreate
    ) -> StoryResponse:
        new_story = Story(
            user_id=current_user.id,
            story_image=story_in.storyImage,
            caption=story_in.caption,
        )
        db.add(new_story)
        await db.commit()
        await db.refresh(new_story)

        return StoryResponse(
            id=new_story.id,
            userId=current_user.id,
            userName=current_user.name,
            userAvatar=current_user.avatar or "https://api.dicebear.com/7.x/avataaars/svg?seed=user",
            storyImage=new_story.story_image,
            timestamp="Just now",
            caption=new_story.caption,
            viewed=False,
        )

    async def mark_story_viewed(
        self, db: AsyncSession, current_user_id: str, story_id: str
    ) -> bool:
        stmt = select(StoryView).where(
            StoryView.story_id == story_id, StoryView.user_id == current_user_id
        )
        result = await db.execute(stmt)
        if not result.scalars().first():
            view = StoryView(story_id=story_id, user_id=current_user_id)
            db.add(view)
            await db.commit()
        return True

    async def delete_story(self, db: AsyncSession, current_user_id: str, story_id: str) -> bool:
        stmt = select(Story).where(Story.id == story_id)
        result = await db.execute(stmt)
        story = result.scalars().first()
        if not story:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
        if story.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        await db.delete(story)
        await db.commit()
        return True


story_service = StoryService()
