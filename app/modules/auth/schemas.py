from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer


class UserBase(BaseModel):
    name: str
    email: EmailStr
    avatar: Optional[str] = None
    role: Optional[str] = "Member"
    bio: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    token: str
    new_password: str = Field(..., min_length=6)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    email: EmailStr
    avatar: Optional[str] = None
    role: Optional[str] = "Member"
    bio: Optional[str] = None
    jobTitle: Optional[str] = Field(default=None, validation_alias="job_title")
    location: Optional[str] = None
    isOnline: bool = Field(default=False, validation_alias="is_online")
    lastSeen: Optional[str] = Field(default=None, validation_alias="last_seen")
    isActive: bool = Field(default=True, validation_alias="is_active")
    createdAt: Optional[datetime] = Field(default=None, validation_alias="created_at")

    @field_serializer("createdAt")
    def serialize_created_at(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
