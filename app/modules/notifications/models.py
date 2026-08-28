import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    recipient_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(30), nullable=False)  # 'like', 'comment', 'share', 'group', 'call'
    content = Column(Text, nullable=False)
    target = Column(String(100), nullable=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="notifications")
    sender = relationship("User", foreign_keys=[sender_id])
