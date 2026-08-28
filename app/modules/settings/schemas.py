from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

AudienceType = Literal["public", "friends", "only_me"]


class SettingsUpdate(BaseModel):
    pushNotifications: Optional[bool] = None
    callRingtone: Optional[bool] = None
    defaultAudience: Optional[AudienceType] = None
    showOnlineStatus: Optional[bool] = None


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    pushNotifications: bool = Field(default=True, validation_alias="push_notifications")
    callRingtone: bool = Field(default=True, validation_alias="call_ringtone")
    defaultAudience: AudienceType = Field(default="public", validation_alias="default_audience")
    showOnlineStatus: bool = Field(default=True, validation_alias="show_online_status")
