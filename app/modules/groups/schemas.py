from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class GroupCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    icon: str
    coverImage: Optional[str] = Field(default=None, validation_alias="coverImage")
    description: str
    isPrivate: bool = Field(default=False, validation_alias="isPrivate")


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    coverImage: Optional[str] = Field(default=None, validation_alias="coverImage")
    description: Optional[str] = None
    isPrivate: Optional[bool] = Field(default=None, validation_alias="isPrivate")


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    icon: str
    coverImage: Optional[str] = Field(default=None, validation_alias="cover_image")
    description: str
    isPrivate: bool = Field(default=False, validation_alias="is_private")
    membersCount: str
    membersNumber: int
    isManaged: bool = False
    joined: bool = False
    recentPostsCount: int = 0
