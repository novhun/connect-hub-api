from typing import List, Optional
from pydantic import BaseModel, Field
from app.modules.auth.schemas import UserResponse


class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[str] = None
    bio: Optional[str] = None
    jobTitle: Optional[str] = None
    location: Optional[str] = None
    isOnline: Optional[bool] = Field(default=None, alias="is_online")


class PresenceUpdate(BaseModel):
    isOnline: bool = Field(..., alias="is_online")


class UserListResponse(BaseModel):
    total: int
    users: List[UserResponse]
