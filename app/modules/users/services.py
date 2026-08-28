from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .schemas import UserUpdate


class UserService:
    async def get_users(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        query: Optional[str] = None,
        only_online: Optional[bool] = None,
    ) -> List[User]:
        stmt = select(User).where(User.is_active == True)
        if query:
            stmt = stmt.where(User.name.ilike(f"%{query}%") | User.email.ilike(f"%{query}%"))
        if only_online is not None:
            stmt = stmt.where(User.is_online == only_online)
        stmt = stmt.offset(skip).limit(limit).order_by(User.is_online.desc(), User.name.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        stmt = select(User).where(User.id == user_id, User.is_active == True)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def update_profile(self, db: AsyncSession, user: User, data: UserUpdate) -> User:
        update_data = data.model_dump(exclude_unset=True)

        if data.name is not None:
            user.name = data.name.strip()
        elif "name" in update_data and update_data["name"]:
            user.name = update_data["name"].strip()

        if data.avatar is not None:
            user.avatar = data.avatar
        elif "avatar" in update_data:
            user.avatar = update_data["avatar"]

        if data.coverImage is not None:
            user.cover_image = data.coverImage
        elif "cover_image" in update_data or "coverImage" in update_data:
            user.cover_image = update_data.get("cover_image") or update_data.get("coverImage")

        if data.role is not None:
            user.role = data.role
        elif "role" in update_data:
            user.role = update_data["role"]

        if data.bio is not None:
            user.bio = data.bio
        elif "bio" in update_data:
            user.bio = update_data["bio"]

        if data.jobTitle is not None:
            user.job_title = data.jobTitle
        elif "job_title" in update_data or "jobTitle" in update_data:
            user.job_title = update_data.get("job_title") or update_data.get("jobTitle")

        if data.location is not None:
            user.location = data.location
        elif "location" in update_data:
            user.location = update_data["location"]

        if data.website is not None:
            user.website = data.website
        elif "website" in update_data:
            user.website = update_data["website"]

        if data.isOnline is not None:
            user.is_online = data.isOnline
        elif "is_online" in update_data or "isOnline" in update_data:
            user.is_online = update_data.get("is_online") or update_data.get("isOnline")

        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        return user

    async def set_presence(self, db: AsyncSession, user: User, is_online: bool) -> User:
        user.is_online = is_online
        if not is_online:
            user.last_seen = "Just now"
        await db.commit()
        await db.refresh(user)
        return user


user_service = UserService()
