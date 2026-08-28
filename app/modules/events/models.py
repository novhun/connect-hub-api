import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Event(Base):
    __tablename__ = "events"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    creator_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    cover_image = Column(Text, nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    creator = relationship("User", foreign_keys=[creator_id])
    attendees = relationship("EventAttendee", back_populates="event", cascade="all, delete-orphan")


class EventAttendee(Base):
    __tablename__ = "event_attendees"
    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_event_user_attendee"),)

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    event_id = Column(String(64), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    event = relationship("Event", back_populates="attendees")
    user = relationship("User", foreign_keys=[user_id])
