from fastapi import HTTPException, UploadFile, status
from app.core.storage import storage_service
from .schemas import PresignedUrlRequest, PresignedUrlResponse, UploadResponse


class MediaService:
    async def upload_file(self, file: UploadFile) -> UploadResponse:
        try:
            content = await file.read()
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty"
                )

            saved_url = await storage_service.save_file(
                file_content=content,
                original_filename=file.filename or "file.bin",
                content_type=file.content_type,
            )

            return UploadResponse(
                url=saved_url,
                filename=file.filename or "file.bin",
                contentType=file.content_type,
                size=len(content),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}",
            )

    def get_presigned_url(self, req: PresignedUrlRequest) -> PresignedUrlResponse:
        upload_url, file_url = storage_service.generate_presigned_upload_url(
            filename=req.filename, content_type=req.contentType
        )
        return PresignedUrlResponse(uploadUrl=upload_url, fileUrl=file_url)


media_service = MediaService()
