from typing import List, Optional
from pydantic import BaseModel
from app.modules.auth.schemas import UserResponse


class DirectMessage(BaseModel):
    id: str
    senderId: str
    text: str = ""
    timestamp: str
    isMe: bool
    messageType: Optional[str] = "text"  # 'text', 'voice', 'file', 'sticker', 'image'
    mediaUrl: Optional[str] = None
    fileName: Optional[str] = None
    fileSize: Optional[str] = None
    duration: Optional[str] = None


class SendMessageRequest(BaseModel):
    text: Optional[str] = ""
    messageType: Optional[str] = "text"
    mediaUrl: Optional[str] = None
    fileName: Optional[str] = None
    fileSize: Optional[str] = None
    duration: Optional[str] = None


class ConversationSummary(BaseModel):
    user: UserResponse
    lastMessage: Optional[str] = None
    lastTimestamp: Optional[str] = None
    unreadCount: int = 0
