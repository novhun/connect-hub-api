from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str
    description: Optional[str] = None
    location: str
    category: Optional[str] = None
    coverImage: Optional[str] = Field(default=None, validation_alias="coverImage")
    startAt: datetime = Field(..., validation_alias="startAt")


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    description: Optional[str] = None
    location: str
    category: Optional[str] = None
    coverImage: Optional[str] = Field(default=None, validation_alias="cover_image")
    startAt: str
    date: str
    attendeesCount: int = 0
    isAttending: bool = False
    isCreator: bool = False
    creatorId: str = Field(..., validation_alias="creator_id")
