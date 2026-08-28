import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class FriendRequest(Base):
    __tablename__ = "friend_requests"
    __table_args__ = (UniqueConstraint("sender_id", "receiver_id", name="uq_friend_request_pair"),)

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    sender_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="pending", nullable=False)  # 'pending', 'accepted'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    responded_at = Column(DateTime(timezone=True), nullable=True)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
