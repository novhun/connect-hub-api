from typing import List, Literal
from pydantic import BaseModel, ConfigDict, Field

SenderType = Literal["user", "assistant"]


class SendSupportMessageRequest(BaseModel):
    text: str = Field(..., min_length=1)


class SupportMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    sender: SenderType
    text: str
    timestamp: str


class SendSupportMessageResponse(BaseModel):
    userMessage: SupportMessageResponse
    assistantMessage: SupportMessageResponse


class SupportHistoryResponse(BaseModel):
    messages: List[SupportMessageResponse]
