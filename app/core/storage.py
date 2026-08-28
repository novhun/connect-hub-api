import os
import uuid
import logging
from typing import Optional, Tuple
import aiofiles
from .config import settings

logger = logging.getLogger("connect_hub.storage")


class StorageService:
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE.lower()
        self.s3_client = None
        self._init_s3()

    def _init_s3(self):
        if self.storage_type in ["s3", "r2"] and settings.S3_ACCESS_KEY_ID:
            try:
                import boto3
                from botocore.config import Config

                kwargs = {
                    "service_name": "s3",
                    "aws_access_key_id": settings.S3_ACCESS_KEY_ID,
                    "aws_secret_access_key": settings.S3_SECRET_ACCESS_KEY,
                    "region_name": settings.S3_REGION,
                    "config": Config(signature_version="s3v4"),
                }
                if settings.S3_ENDPOINT_URL:
                    kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

                self.s3_client = boto3.client(**kwargs)
                logger.info(f"Initialized S3/R2 storage client for bucket '{settings.S3_BUCKET_NAME}'")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}. Falling back to local storage.")
                self.storage_type = "local"
        else:
            self.storage_type = "local"
            # Ensure local uploads directory exists
            os.makedirs(settings.LOCAL_UPLOAD_DIR, exist_ok=True)

    async def save_file(
        self, file_content: bytes, original_filename: str, content_type: Optional[str] = None
    ) -> str:
        """
        Saves a file to either S3/R2 or local filesystem, returning the accessible URL.
        """
        ext = os.path.splitext(original_filename)[1].lower() or ".bin"
        unique_name = f"{uuid.uuid4().hex}{ext}"

        if self.storage_type in ["s3", "r2"] and self.s3_client:
            try:
                extra_args = {}
                if content_type:
                    extra_args["ContentType"] = content_type

                self.s3_client.put_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=unique_name,
                    Body=file_content,
                    **extra_args,
                )

                if settings.S3_PUBLIC_URL:
                    return f"{settings.S3_PUBLIC_URL.rstrip('/')}/{unique_name}"
                elif settings.S3_ENDPOINT_URL:
                    return f"{settings.S3_ENDPOINT_URL.rstrip('/')}/{settings.S3_BUCKET_NAME}/{unique_name}"
                else:
                    return f"https://{settings.S3_BUCKET_NAME}.s3.amazonaws.com/{unique_name}"
            except Exception as e:
                logger.error(f"S3 upload error: {e}. Saving locally instead.")

        # Local storage fallback
        os.makedirs(settings.LOCAL_UPLOAD_DIR, exist_ok=True)
        local_path = os.path.join(settings.LOCAL_UPLOAD_DIR, unique_name)
        async with aiofiles.open(local_path, "wb") as out_file:
            await out_file.write(file_content)

        return f"/uploads/{unique_name}"

    def generate_presigned_upload_url(
        self, filename: str, content_type: str, expires_in: int = 3600
    ) -> Tuple[Optional[str], str]:
        """
        Generates a presigned PUT URL for direct client-to-S3 uploads.
        Returns (presigned_url, final_public_file_url).
        """
        ext = os.path.splitext(filename)[1].lower() or ".bin"
        unique_name = f"{uuid.uuid4().hex}{ext}"

        if self.storage_type in ["s3", "r2"] and self.s3_client:
            try:
                url = self.s3_client.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={
                        "Bucket": settings.S3_BUCKET_NAME,
                        "Key": unique_name,
                        "ContentType": content_type,
                    },
                    ExpiresIn=expires_in,
                )
                public_url = (
                    f"{settings.S3_PUBLIC_URL.rstrip('/')}/{unique_name}"
                    if settings.S3_PUBLIC_URL
                    else f"https://{settings.S3_BUCKET_NAME}.s3.amazonaws.com/{unique_name}"
                )
                return url, public_url
            except Exception as e:
                logger.error(f"Error generating presigned URL: {e}")
                return None, f"/uploads/{unique_name}"

        return None, f"/uploads/{unique_name}"


storage_service = StorageService()
