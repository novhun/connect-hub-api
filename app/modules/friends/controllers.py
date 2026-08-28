from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from app.modules.auth.schemas import UserResponse
from .schemas import FriendRequestResponse, FriendStatusResponse
from .services import friend_service


class FriendController:
    async def get_status(self, db: AsyncSession, current_user: User, other_user_id: str) -> FriendStatusResponse:
        return await friend_service.get_status(db, current_user, other_user_id)

    async def send_request(self, db: AsyncSession, current_user: User, receiver_id: str) -> FriendStatusResponse:
        return await friend_service.send_request(db, current_user, receiver_id)

    async def respond_request(
        self, db: AsyncSession, current_user: User, request_id: str, accept: bool
    ) -> FriendStatusResponse:
        return await friend_service.respond_request(db, current_user, request_id, accept)

    async def cancel_request(self, db: AsyncSession, current_user: User, request_id: str) -> dict:
        await friend_service.cancel_request(db, current_user, request_id)
        return {"success": True}

    async def unfriend(self, db: AsyncSession, current_user: User, other_user_id: str) -> dict:
        await friend_service.unfriend(db, current_user, other_user_id)
        return {"success": True}

    async def list_friends(self, db: AsyncSession, current_user: User) -> List[UserResponse]:
        return await friend_service.list_friends(db, current_user)

    async def list_requests(self, db: AsyncSession, current_user: User, direction: str) -> List[FriendRequestResponse]:
        return await friend_service.list_requests(db, current_user, direction)

    async def list_suggestions(self, db: AsyncSession, current_user: User) -> List[UserResponse]:
        return await friend_service.list_suggestions(db, current_user)


friend_controller = FriendController()
