import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Group(Base):
    __tablename__ = "groups"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(150), nullable=False, unique=True, index=True)
    icon = Column(Text, nullable=False)
    cover_image = Column(Text, nullable=True)
    description = Column(Text, nullable=False)
    is_private = Column(Boolean, default=False)
    creator_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    creator = relationship("User", back_populates="created_groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_user_member"),)

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    group_id = Column(String(64), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), default="member")  # 'admin', 'moderator', 'member'
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")
