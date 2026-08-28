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
        if "is_online" in update_data:
            user.is_online = update_data["is_online"]
        if "name" in update_data and update_data["name"]:
            user.name = update_data["name"].strip()
        if "avatar" in update_data and update_data["avatar"]:
            user.avatar = update_data["avatar"]
        if "role" in update_data:
            user.role = update_data["role"]
        if "bio" in update_data:
            user.bio = update_data["bio"]
        if "jobTitle" in update_data:
            user.job_title = update_data["jobTitle"]
        if "location" in update_data:
            user.location = update_data["location"]

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
