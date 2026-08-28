from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.auth.schemas import UserResponse


class UserUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: Optional[str] = None
    avatar: Optional[str] = None
    coverImage: Optional[str] = Field(default=None, validation_alias="cover_image")
    role: Optional[str] = None
    bio: Optional[str] = None
    jobTitle: Optional[str] = Field(default=None, validation_alias="job_title")
    location: Optional[str] = None
    website: Optional[str] = None
    isOnline: Optional[bool] = Field(default=None, validation_alias="is_online")


class PresenceUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    isOnline: bool = Field(..., validation_alias="is_online")


class UserListResponse(BaseModel):
    total: int
    users: List[UserResponse]

