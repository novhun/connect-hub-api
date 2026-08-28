from fastapi import APIRouter, File, UploadFile, status
from .controllers import media_controller
from .schemas import PresignedUrlRequest, PresignedUrlResponse, UploadResponse

router = APIRouter(prefix="/media", tags=["Media & File Uploads"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """Upload media file (image/video/attachment) directly to S3/R2 or Local storage."""
    return await media_controller.upload(file)


@router.post("/presigned-url", response_model=PresignedUrlResponse)
def get_presigned_url(req: PresignedUrlRequest):
    """Generate a presigned upload URL for direct cloud uploads."""
    return media_controller.get_presigned_url(req)
