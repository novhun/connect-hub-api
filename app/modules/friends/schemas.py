from typing import Literal, Optional
from pydantic import BaseModel
from app.modules.auth.schemas import UserResponse

FriendRequestStatus = Literal["pending", "accepted"]
FriendRequestDirection = Literal["incoming", "outgoing"]
FriendStatus = Literal["none", "pending_sent", "pending_received", "friends", "self"]


class FriendRequestResponse(BaseModel):
    id: str
    user: UserResponse
    status: FriendRequestStatus
    direction: FriendRequestDirection
    createdAt: str


class FriendStatusResponse(BaseModel):
    status: FriendStatus
    requestId: Optional[str] = None


class RespondRequestBody(BaseModel):
    accept: bool
