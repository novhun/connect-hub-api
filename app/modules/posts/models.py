import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Post(Base):
    __tablename__ = "posts"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    author_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    privacy = Column(String(20), default="public", nullable=False)  # 'public', 'friends', 'only_me'
    feeling = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    tagged_group = Column(String(100), nullable=True)
    shares_count = Column(Integer, default=0)
    shared_post_id = Column(String(64), ForeignKey("posts.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    author = relationship("User", back_populates="posts")
    media = relationship("PostMedia", back_populates="post", cascade="all, delete-orphan", order_by="PostMedia.id")
    reactions = relationship("Reaction", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan", order_by="Comment.created_at")
    saved_by = relationship("SavedPost", back_populates="post", cascade="all, delete-orphan")
    shared_post = relationship("Post", remote_side=[id], foreign_keys=[shared_post_id], lazy="selectin")


class PostMedia(Base):
    __tablename__ = "post_media"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    post_id = Column(String(64), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    media_url = Column(Text, nullable=False)
    media_type = Column(String(20), default="image")  # 'image', 'video'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    post = relationship("Post", back_populates="media")


class Reaction(Base):
    __tablename__ = "reactions"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_post_user_reaction"),)

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    post_id = Column(String(64), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reaction_type = Column(String(20), nullable=False)  # 'like', 'love', 'care', 'haha', 'wow', 'sad', 'angry'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    post = relationship("Post", back_populates="reactions")
    user = relationship("User", back_populates="reactions")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    post_id = Column(String(64), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(String(64), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    likes_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], back_populates="replies", foreign_keys=[parent_id])
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan", order_by="Comment.created_at", foreign_keys=[parent_id])
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")


class CommentLike(Base):
    __tablename__ = "comment_likes"
    __table_args__ = (UniqueConstraint("comment_id", "user_id", name="uq_comment_user_like"),)

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    comment_id = Column(String(64), ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reaction_type = Column(String(20), default="like")  # 'like', 'love', 'care', 'haha', 'wow', 'sad', 'angry'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    comment = relationship("Comment", back_populates="likes")


class SavedPost(Base):
    __tablename__ = "saved_posts"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_saved_post_user"),)

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    post_id = Column(String(64), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    post = relationship("Post", back_populates="saved_by")
    user = relationship("User", back_populates="saved_posts")
