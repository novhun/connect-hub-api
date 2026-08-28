from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from app.modules.auth.schemas import UserResponse
from .schemas import PresenceUpdate, UserListResponse, UserUpdate
from .services import user_service


class UserController:
    async def list_users(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        query: Optional[str] = None,
        only_online: Optional[bool] = None,
    ) -> List[UserResponse]:
        users = await user_service.get_users(
            db=db, skip=skip, limit=limit, query=query, only_online=only_online
        )
        return [UserResponse.model_validate(u) for u in users]

    async def get_user_profile(self, db: AsyncSession, user_id: str) -> UserResponse:
        user = await user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserResponse.model_validate(user)

    async def update_profile(self, db: AsyncSession, current_user: User, data: UserUpdate) -> UserResponse:
        updated = await user_service.update_profile(db, current_user, data)
        return UserResponse.model_validate(updated)

    async def update_presence(
        self, db: AsyncSession, current_user: User, data: PresenceUpdate
    ) -> UserResponse:
        updated = await user_service.set_presence(db, current_user, data.isOnline)
        return UserResponse.model_validate(updated)


user_controller = UserController()
