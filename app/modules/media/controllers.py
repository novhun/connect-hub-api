from fastapi import UploadFile
from .schemas import PresignedUrlRequest, PresignedUrlResponse, UploadResponse
from .services import media_service


class MediaController:
    async def upload(self, file: UploadFile) -> UploadResponse:
        return await media_service.upload_file(file)

    def get_presigned_url(self, req: PresignedUrlRequest) -> PresignedUrlResponse:
        return media_service.get_presigned_url(req)


media_controller = MediaController()
