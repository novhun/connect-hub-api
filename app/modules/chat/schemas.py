from typing import List, Optional
from pydantic import BaseModel
from app.modules.auth.schemas import UserResponse


class DirectMessage(BaseModel):
    id: str
    senderId: str
    text: str
    timestamp: str
    isMe: bool


class SendMessageRequest(BaseModel):
    text: str


class ConversationSummary(BaseModel):
    user: UserResponse
    lastMessage: Optional[str] = None
    lastTimestamp: Optional[str] = None
    unreadCount: int = 0
