import secrets
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def generate_invite_code() -> str:
    return secrets.token_urlsafe(8)


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    sender_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, default="", nullable=False)
    message_type = Column(String(32), default="text", nullable=True)  # 'text', 'voice', 'file', 'sticker', 'image'
    media_url = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(String(32), nullable=True)
    duration = Column(String(32), nullable=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")


class GroupChat(Base):
    __tablename__ = "group_chats"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(150), nullable=False)
    avatar = Column(Text, nullable=True)
    description = Column(Text, default="", nullable=True)
    creator_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invite_code = Column(String(32), unique=True, default=generate_invite_code, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    creator = relationship("User", foreign_keys=[creator_id])
    members = relationship("GroupChatMember", back_populates="group_chat", cascade="all, delete-orphan")
    messages = relationship("GroupChatMessage", back_populates="group_chat", cascade="all, delete-orphan")


class GroupChatMember(Base):
    __tablename__ = "group_chat_members"
    __table_args__ = (UniqueConstraint("group_chat_id", "user_id", name="uq_group_chat_user_member"),)

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    group_chat_id = Column(String(64), ForeignKey("group_chats.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), default="member")  # 'admin', 'member'
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    group_chat = relationship("GroupChat", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])


class GroupChatMessage(Base):
    __tablename__ = "group_chat_messages"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    group_chat_id = Column(String(64), ForeignKey("group_chats.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, default="", nullable=False)
    message_type = Column(String(32), default="text", nullable=True)  # 'text', 'voice', 'file', 'sticker', 'image', 'system'
    media_url = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(String(32), nullable=True)
    duration = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    group_chat = relationship("GroupChat", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

