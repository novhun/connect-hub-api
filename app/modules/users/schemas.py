from typing import List, Optional
from pydantic import BaseModel, Field
from app.modules.auth.schemas import UserResponse


class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    coverImage: Optional[str] = Field(default=None, alias="cover_image")
    role: Optional[str] = None
    bio: Optional[str] = None
    jobTitle: Optional[str] = Field(default=None, alias="job_title")
    location: Optional[str] = None
    website: Optional[str] = None
    isOnline: Optional[bool] = Field(default=None, alias="is_online")


class PresenceUpdate(BaseModel):
    isOnline: bool = Field(..., alias="is_online")


class UserListResponse(BaseModel):
    total: int
    users: List[UserResponse]
