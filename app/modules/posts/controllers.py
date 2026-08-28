from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .schemas import CommentCreate, PostCreate, PostUpdate, PostResponse, ReactionRequest
from .services import post_service


class PostController:
    async def get_feed(
        self,
        db: AsyncSession,
        current_user: Optional[User],
        skip: int,
        limit: int,
        group_name: Optional[str],
        author_id: Optional[str],
        saved_only: bool,
    ) -> List[PostResponse]:
        user_id = current_user.id if current_user else None
        return await post_service.get_feed(
            db=db,
            current_user_id=user_id,
            skip=skip,
            limit=limit,
            group_name=group_name,
            author_id=author_id,
            saved_only=saved_only,
        )

    async def get_post(self, db: AsyncSession, post_id: str, current_user: Optional[User]) -> PostResponse:
        user_id = current_user.id if current_user else None
        return await post_service.get_post_by_id(db, post_id, user_id)

    async def create_post(self, db: AsyncSession, current_user: User, post_in: PostCreate) -> PostResponse:
        return await post_service.create_post(db, current_user, post_in)

    async def update_post(
        self, db: AsyncSession, current_user: User, post_id: str, post_in: PostUpdate
    ) -> PostResponse:
        return await post_service.update_post(db, current_user.id, post_id, post_in)

    async def react(
        self, db: AsyncSession, current_user: User, post_id: str, rxn_in: ReactionRequest
    ) -> PostResponse:
        return await post_service.react_to_post(db, current_user.id, post_id, rxn_in.reaction)

    async def add_comment(
        self, db: AsyncSession, current_user: User, post_id: str, comment_in: CommentCreate
    ) -> PostResponse:
        return await post_service.add_comment(db, current_user, post_id, comment_in.content)

    async def toggle_comment_like(self, db: AsyncSession, current_user: User, comment_id: str) -> dict:
        liked = await post_service.toggle_comment_like(db, current_user.id, comment_id)
        return {"success": True, "isLiked": liked}

    async def toggle_save_post(self, db: AsyncSession, current_user: User, post_id: str) -> dict:
        saved = await post_service.toggle_save_post(db, current_user.id, post_id)
        return {"success": True, "isSaved": saved}

    async def share_post(self, db: AsyncSession, post_id: str) -> dict:
        shares_count = await post_service.share_post(db, post_id)
        return {"success": True, "sharesCount": shares_count}

    async def delete_post(self, db: AsyncSession, current_user: User, post_id: str) -> dict:
        await post_service.delete_post(db, current_user.id, post_id)
        return {"success": True, "message": "Post deleted successfully"}


post_controller = PostController()
