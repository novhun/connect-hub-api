from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.modules.auth.models import User
from app.modules.auth.schemas import UserResponse
from app.modules.friends.models import FriendRequest
from .models import Comment, CommentLike, Post, PostMedia, Reaction, SavedPost
from .schemas import (
    CommentResponse,
    PostCreate,
    PostUpdate,
    PostResponse,
    ReactionCount,
    ReactionType,
)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_relative_time(dt: Optional[datetime]) -> str:
    if not dt:
        return "Just now"
    dt = ensure_utc(dt)
    now = datetime.now(timezone.utc)
    diff = max(0.0, (now - dt).total_seconds())
    if diff < 60:
        return "Just now"
    elif diff < 3600:
        return f"{int(diff // 60)}m ago"
    elif diff < 86400:
        return f"{int(diff // 3600)}h ago"
    elif diff < 604800:
        return f"{int(diff // 86400)}d ago"
    else:
        return dt.strftime("%b %d, %Y")


class PostService:
    async def _format_post(
        self, db: AsyncSession, post: Post, current_user_id: Optional[str] = None
    ) -> PostResponse:
        counts = {
            "like": 0, "love": 0, "care": 0, "haha": 0,
            "wow": 0, "sad": 0, "angry": 0
        }
        user_reaction = None
        for r in post.reactions:
            if r.reaction_type in counts:
                counts[r.reaction_type] += 1
            if current_user_id and r.user_id == current_user_id:
                user_reaction = r.reaction_type

        comments_formatted = []
        for c in post.comments:
            is_liked = False
            if current_user_id:
                is_liked = any(like.user_id == current_user_id for like in c.likes)
            comments_formatted.append(
                CommentResponse(
                    id=c.id,
                    user=UserResponse.model_validate(c.user),
                    content=c.content,
                    timestamp=format_relative_time(c.created_at),
                    likes=len(c.likes) or c.likes_count,
                    isLiked=is_liked,
                )
            )

        is_saved = False
        if current_user_id:
            is_saved = any(s.user_id == current_user_id for s in post.saved_by)

        return PostResponse(
            id=post.id,
            author=UserResponse.model_validate(post.author),
            timestamp=format_relative_time(post.created_at),
            privacy=post.privacy,  # type: ignore
            content=post.content,
            images=[m.media_url for m in post.media],
            reactionCounts=ReactionCount(**counts),
            userReaction=user_reaction,  # type: ignore
            comments=comments_formatted,
            sharesCount=post.shares_count or 0,
            isSaved=is_saved,
            feeling=post.feeling,
            location=post.location,
            taggedGroup=post.tagged_group,
        )

    async def get_posts_query(self):
        return (
            select(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.media),
                selectinload(Post.reactions),
                selectinload(Post.comments).selectinload(Comment.user),
                selectinload(Post.comments).selectinload(Comment.likes),
                selectinload(Post.saved_by),
            )
            .order_by(Post.created_at.desc())
        )

    async def get_feed(
        self,
        db: AsyncSession,
        current_user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        group_name: Optional[str] = None,
        author_id: Optional[str] = None,
        saved_only: bool = False,
    ) -> List[PostResponse]:
        query = await self.get_posts_query()

        # Enforce Privacy Filters
        if not current_user_id:
            # Anonymous / non-logged in users can ONLY view public posts
            query = query.where(Post.privacy == "public")
        else:
            # Find accepted friends of the current user
            friend_stmt = select(FriendRequest).where(
                (FriendRequest.sender_id == current_user_id) | (FriendRequest.receiver_id == current_user_id),
                FriendRequest.status == "accepted",
            )
            friend_res = await db.execute(friend_stmt)
            friend_rows = friend_res.scalars().all()
            friend_ids = {
                fr.receiver_id if fr.sender_id == current_user_id else fr.sender_id
                for fr in friend_rows
            }

            if friend_ids:
                query = query.where(
                    (Post.privacy == "public")
                    | (Post.author_id == current_user_id)  # Own posts (including only_me and friends)
                    | ((Post.privacy == "friends") & (Post.author_id.in_(list(friend_ids))))  # Friends' posts
                )
            else:
                query = query.where(
                    (Post.privacy == "public")
                    | (Post.author_id == current_user_id)  # Own posts (including only_me)
                )

        if group_name:
            query = query.where(Post.tagged_group == group_name)
        if author_id:
            query = query.where(Post.author_id == author_id)
        if saved_only and current_user_id:
            query = query.join(SavedPost, SavedPost.post_id == Post.id).where(
                SavedPost.user_id == current_user_id
            )

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        posts = result.scalars().unique().all()

        return [await self._format_post(db, p, current_user_id) for p in posts]

    async def get_post_by_id(
        self, db: AsyncSession, post_id: str, current_user_id: Optional[str] = None
    ) -> PostResponse:
        query = (await self.get_posts_query()).where(Post.id == post_id)
        result = await db.execute(query)
        post = result.scalars().first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

        # Enforce single post privacy
        if post.privacy == "only_me" and post.author_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This post is private (Only Me)")
        if post.privacy == "friends" and post.author_id != current_user_id:
            if not current_user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This post is visible to friends only")
            friend_stmt = select(FriendRequest).where(
                (FriendRequest.sender_id == current_user_id) | (FriendRequest.receiver_id == current_user_id),
                FriendRequest.status == "accepted",
            )
            friend_res = await db.execute(friend_stmt)
            friend_ids = {
                fr.receiver_id if fr.sender_id == current_user_id else fr.sender_id
                for fr in friend_res.scalars().all()
            }
            if post.author_id not in friend_ids:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This post is visible to friends only")

        return await self._format_post(db, post, current_user_id)

    async def create_post(self, db: AsyncSession, current_user: User, post_in: PostCreate) -> PostResponse:
        new_post = Post(
            author_id=current_user.id,
            content=post_in.content.strip(),
            privacy=post_in.privacy,
            feeling=post_in.feeling,
            location=post_in.location,
            tagged_group=post_in.taggedGroup,
        )
        db.add(new_post)
        await db.flush()

        if post_in.images:
            for img in post_in.images:
                if img.strip():
                    media = PostMedia(post_id=new_post.id, media_url=img.strip())
                    db.add(media)

        await db.commit()
        return await self.get_post_by_id(db, new_post.id, current_user.id)

    async def react_to_post(
        self, db: AsyncSession, current_user_id: str, post_id: str, reaction_type: Optional[ReactionType]
    ) -> PostResponse:
        stmt = select(Reaction).where(
            Reaction.post_id == post_id, Reaction.user_id == current_user_id
        )
        result = await db.execute(stmt)
        existing = result.scalars().first()

        if reaction_type is None:
            if existing:
                await db.delete(existing)
                await db.commit()
        else:
            if existing:
                existing.reaction_type = reaction_type
            else:
                new_rxn = Reaction(
                    post_id=post_id, user_id=current_user_id, reaction_type=reaction_type
                )
                db.add(new_rxn)
            await db.commit()

        return await self.get_post_by_id(db, post_id, current_user_id)

    async def add_comment(
        self, db: AsyncSession, current_user: User, post_id: str, content: str
    ) -> PostResponse:
        if not content.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment cannot be empty")

        new_comment = Comment(post_id=post_id, user_id=current_user.id, content=content.strip())
        db.add(new_comment)
        await db.commit()

        return await self.get_post_by_id(db, post_id, current_user.id)

    async def toggle_comment_like(
        self, db: AsyncSession, current_user_id: str, comment_id: str
    ) -> bool:
        stmt = select(CommentLike).where(
            CommentLike.comment_id == comment_id, CommentLike.user_id == current_user_id
        )
        result = await db.execute(stmt)
        existing = result.scalars().first()
        if existing:
            await db.delete(existing)
            await db.commit()
            return False
        else:
            new_like = CommentLike(comment_id=comment_id, user_id=current_user_id)
            db.add(new_like)
            await db.commit()
            return True

    async def toggle_save_post(self, db: AsyncSession, current_user_id: str, post_id: str) -> bool:
        stmt = select(SavedPost).where(
            SavedPost.post_id == post_id, SavedPost.user_id == current_user_id
        )
        result = await db.execute(stmt)
        existing = result.scalars().first()
        if existing:
            await db.delete(existing)
            await db.commit()
            return False
        else:
            saved = SavedPost(post_id=post_id, user_id=current_user_id)
            db.add(saved)
            await db.commit()
            return True

    async def share_post(self, db: AsyncSession, post_id: str) -> int:
        stmt = select(Post).where(Post.id == post_id)
        result = await db.execute(stmt)
        post = result.scalars().first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        post.shares_count = (post.shares_count or 0) + 1
        await db.commit()
    async def update_post(
        self, db: AsyncSession, current_user_id: str, post_id: str, post_update: PostUpdate
    ) -> PostResponse:
        stmt = select(Post).options(selectinload(Post.media)).where(Post.id == post_id)
        result = await db.execute(stmt)
        post = result.scalars().first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        if post.author_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this post"
            )

        if post_update.content is not None:
            post.content = post_update.content.strip()
        if post_update.privacy is not None:
            post.privacy = post_update.privacy
        if post_update.feeling is not None:
            post.feeling = post_update.feeling
        if post_update.location is not None:
            post.location = post_update.location
        if post_update.taggedGroup is not None:
            post.tagged_group = post_update.taggedGroup

        if post_update.images is not None:
            for m in list(post.media):
                await db.delete(m)
            for img_url in post_update.images:
                new_media = PostMedia(post_id=post.id, media_url=img_url, media_type="image")
                db.add(new_media)

        await db.commit()
        return await self.get_post_by_id(db, post_id, current_user_id)

    async def delete_post(self, db: AsyncSession, current_user_id: str, post_id: str) -> bool:
        stmt = select(Post).where(Post.id == post_id)
        result = await db.execute(stmt)
        post = result.scalars().first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        if post.author_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        await db.delete(post)
        await db.commit()
        return True


post_service = PostService()
