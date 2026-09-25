from typing import Literal, Optional
from pydantic import BaseModel
from app.modules.auth.schemas import UserResponse

NotificationType = Literal[
    "like",
    "comment",
    "share",
    "group",
    "call",
    "friend_request",
    "friend_accept",
    "message",
]


class NotificationResponse(BaseModel):
    id: str
    user: UserResponse
    type: str  # 'like', 'comment', 'share', 'group', 'call', 'friend_request', 'friend_accept', 'message'
    content: str
    target: Optional[str] = None
    timestamp: str
    isRead: bool

