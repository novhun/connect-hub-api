import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class CallSession(Base):
    __tablename__ = "call_sessions"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    caller_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = Column(String(64), default=generate_uuid, index=True)
    call_type = Column(String(20), default="audio", nullable=False)  # 'audio', 'video'
    status = Column(String(20), default="initiating", nullable=False)  # 'initiating', 'ringing', 'connected', 'completed', 'missed', 'declined'
    duration_seconds = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    caller = relationship("User", foreign_keys=[caller_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
