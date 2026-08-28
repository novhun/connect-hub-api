from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.services import get_current_user, get_optional_current_user
from .controllers import post_controller
from .schemas import CommentCreate, PostCreate, PostResponse, ReactionRequest

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("", response_model=List[PostResponse])
async def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    group: Optional[str] = None,
    author_id: Optional[str] = None,
    saved_only: bool = False,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve posts feed with optional group or saved filter."""
    return await post_controller.get_feed(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        group_name=group,
        author_id=author_id,
        saved_only=saved_only,
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single post by ID."""
    return await post_controller.get_post(db, post_id, current_user)


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_in: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new post."""
    return await post_controller.create_post(db, current_user, post_in)


@router.post("/{post_id}/react", response_model=PostResponse)
async def react_to_post(
    post_id: str,
    rxn_in: ReactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """React or unreact to a post with like, love, care, haha, wow, sad, angry."""
    return await post_controller.react(db, current_user, post_id, rxn_in)


@router.post("/{post_id}/comments", response_model=PostResponse)
async def add_comment(
    post_id: str,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a comment to a post."""
    return await post_controller.add_comment(db, current_user, post_id, comment_in)


@router.post("/comments/{comment_id}/like")
async def toggle_comment_like(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Like or unlike a comment."""
    return await post_controller.toggle_comment_like(db, current_user, comment_id)


@router.post("/{post_id}/save")
async def toggle_save_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save or unsave a post."""
    return await post_controller.toggle_save_post(db, current_user, post_id)


@router.post("/{post_id}/share")
async def share_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Increment share count on a post."""
    return await post_controller.share_post(db, post_id)


@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a post created by current user."""
    return await post_controller.delete_post(db, current_user, post_id)
