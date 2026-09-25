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


# --- GROUP CHAT SCHEMAS ---

class GroupChatMemberResponse(BaseModel):
    id: str
    userId: str
    role: str
    joinedAt: Optional[str] = None
    user: UserResponse


class CreateGroupChatRequest(BaseModel):
    name: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    memberIds: List[str] = []


class UpdateGroupChatRequest(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    description: Optional[str] = None


class InviteMembersRequest(BaseModel):
    memberIds: List[str]


class GroupChatMessageResponse(BaseModel):
    id: str
    groupChatId: str
    senderId: str
    sender: UserResponse
    text: str = ""
    timestamp: str
    isMe: bool
    messageType: Optional[str] = "text"  # 'text', 'voice', 'file', 'sticker', 'image', 'system'
    mediaUrl: Optional[str] = None
    fileName: Optional[str] = None
    fileSize: Optional[str] = None
    duration: Optional[str] = None


class SendGroupMessageRequest(BaseModel):
    text: Optional[str] = ""
    messageType: Optional[str] = "text"
    mediaUrl: Optional[str] = None
    fileName: Optional[str] = None
    fileSize: Optional[str] = None
    duration: Optional[str] = None


class GroupChatSummary(BaseModel):
    id: str
    name: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    creatorId: str
    inviteCode: Optional[str] = None
    membersCount: int = 0
    members: List[GroupChatMemberResponse] = []
    lastMessage: Optional[str] = None
    lastMessageSender: Optional[str] = None
    lastTimestamp: Optional[str] = None
    unreadCount: int = 0
    isGroup: bool = True

