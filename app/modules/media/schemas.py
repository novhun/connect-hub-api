from typing import Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    url: str
    filename: str
    contentType: Optional[str] = None
    size: int


class PresignedUrlRequest(BaseModel):
    filename: str
    contentType: str


class PresignedUrlResponse(BaseModel):
    uploadUrl: Optional[str] = None
    fileUrl: str
