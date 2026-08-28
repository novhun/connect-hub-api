from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .schemas import GroupCreate, GroupResponse, GroupUpdate
from .services import group_service


class GroupController:
    async def list_groups(
        self, db: AsyncSession, current_user: Optional[User], skip: int, limit: int
    ) -> List[GroupResponse]:
        user_id = current_user.id if current_user else None
        return await group_service.list_groups(db, user_id, skip, limit)

    async def get_group(
        self, db: AsyncSession, group_id: str, current_user: Optional[User]
    ) -> GroupResponse:
        user_id = current_user.id if current_user else None
        return await group_service.get_group_by_id(db, group_id, user_id)

    async def create_group(
        self, db: AsyncSession, current_user: User, group_in: GroupCreate
    ) -> GroupResponse:
        return await group_service.create_group(db, current_user, group_in)

    async def join_group(
        self, db: AsyncSession, current_user: User, group_id: str
    ) -> GroupResponse:
        return await group_service.join_group(db, current_user, group_id)

    async def leave_group(
        self, db: AsyncSession, current_user: User, group_id: str
    ) -> GroupResponse:
        return await group_service.leave_group(db, current_user, group_id)

    async def delete_group(self, db: AsyncSession, current_user: User, group_id: str) -> dict:
        await group_service.delete_group(db, current_user, group_id)
        return {"success": True, "message": "Group deleted successfully"}


group_controller = GroupController()
