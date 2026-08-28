from typing import Literal, Optional
from pydantic import BaseModel
from app.modules.auth.schemas import UserResponse

NotificationType = Literal["like", "comment", "share", "group", "call"]


class NotificationResponse(BaseModel):
    id: str
    user: UserResponse
    type: NotificationType
    content: str
    target: Optional[str] = None
    timestamp: str
    isRead: bool
