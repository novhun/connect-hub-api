from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StoryCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    storyImage: str = Field(..., validation_alias="storyImage")
    caption: Optional[str] = None


class StoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    userId: str
    userName: str
    userAvatar: str
    storyImage: str = Field(..., validation_alias="story_image")
    timestamp: str
    caption: Optional[str] = None
    viewed: bool = False
