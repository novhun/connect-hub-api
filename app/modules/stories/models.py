import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Story(Base):
    __tablename__ = "stories"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    story_image = Column(Text, nullable=False)
    caption = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(hours=24),
        index=True,
    )

    user = relationship("User", back_populates="stories")
    views = relationship("StoryView", back_populates="story", cascade="all, delete-orphan")


class StoryView(Base):
    __tablename__ = "story_views"
    __table_args__ = (UniqueConstraint("story_id", "user_id", name="uq_story_user_view"),)

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    story_id = Column(String(64), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    viewed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    story = relationship("Story", back_populates="views")
    user = relationship("User")
