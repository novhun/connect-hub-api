from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.auth.schemas import UserResponse

CallType = Literal["audio", "video"]
CallStatus = Literal["initiating", "ringing", "connected", "completed", "missed", "declined"]


class CallInitiateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    receiverId: Optional[str] = Field(default=None, validation_alias="receiverId")
    groupId: Optional[str] = Field(default=None, validation_alias="groupId")
    callType: CallType = Field(default="audio", validation_alias="callType")


class CallStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: CallStatus
    durationSeconds: Optional[int] = Field(default=None, validation_alias="durationSeconds")


class CallSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    callerId: str = Field(..., validation_alias="caller_id")
    receiverId: Optional[str] = Field(default=None, validation_alias="receiver_id")
    groupId: Optional[str] = Field(default=None, validation_alias="group_id")
    isGroupCall: bool = Field(default=False, validation_alias="is_group_call")
    roomId: str = Field(..., validation_alias="room_id")
    callType: CallType = Field(..., validation_alias="call_type")
    status: CallStatus
    durationSeconds: int = Field(default=0, validation_alias="duration_seconds")


class CallLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    user: UserResponse
    type: Literal["incoming", "outgoing"]
    date: str
    status: Literal["missed", "completed", "declined"]
    duration: Optional[str] = None
    callType: CallType = Field(..., validation_alias="call_type")
    groupId: Optional[str] = None
    groupName: Optional[str] = None
    isGroupCall: bool = False
