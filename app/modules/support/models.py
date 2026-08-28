import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # 'user' or 'assistant'
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
