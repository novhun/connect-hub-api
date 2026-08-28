from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from app.core.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    push_notifications = Column(Boolean, default=True)
    call_ringtone = Column(Boolean, default=True)
    default_audience = Column(String(20), default="public")  # 'public', 'friends', 'only_me'
    show_online_status = Column(Boolean, default=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
