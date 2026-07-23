import asyncio
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.settings import settings


@dataclass(frozen=True)
class StoredImage:
    bucket: str
    key: str
    original_filename: str
    content_type: str | None = None

    @property
    def uri(self) -> str:
        return f"s3://{self.bucket}/{self.key}"


class S3ImageStorage:
    def __init__(self) -> None:
        if not settings.s3_bucket_name:
            raise RuntimeError("S3_BUCKET_NAME must be set to store AI estimate images.")
        import boto3

        self.bucket_name = settings.s3_bucket_name
        self.prefix = settings.ai_estimate_image_prefix.strip("/")
        self.client = boto3.client("s3", region_name=settings.aws_region)

    async def upload_ai_estimate_images(
        self,
        *,
        estimate_id: int,
        user_id: int,
        images: list[UploadFile] | None,
    ) -> list[StoredImage]:
        stored_images: list[StoredImage] = []
        for index, image in enumerate(images or []):
            body = await image.read()
            filename = image.filename or f"image-{index}.bin"
            key = self._build_key(user_id=user_id, estimate_id=estimate_id, index=index, filename=filename)
            extra_args = {"ContentType": image.content_type} if image.content_type else None
            await asyncio.to_thread(self._put_object, key, body, extra_args)
            stored_images.append(
                StoredImage(
                    bucket=self.bucket_name,
                    key=key,
                    original_filename=filename,
                    content_type=image.content_type,
                )
            )
        return stored_images

    async def delete_images(self, stored_images: list[StoredImage]) -> None:
        if not stored_images:
            return
        objects = [{"Key": image.key} for image in stored_images]
        await asyncio.to_thread(
            self.client.delete_objects,
            Bucket=self.bucket_name,
            Delete={"Objects": objects, "Quiet": True},
        )

    def _put_object(self, key: str, body: bytes, extra_args: dict[str, str] | None) -> None:
        kwargs = {
            "Bucket": self.bucket_name,
            "Key": key,
            "Body": body,
        }
        if extra_args:
            kwargs.update(extra_args)
        self.client.put_object(**kwargs)

    def _build_key(self, *, user_id: int, estimate_id: int, index: int, filename: str) -> str:
        suffix = Path(filename).suffix or ".bin"
        return f"{self.prefix}/{user_id}/{estimate_id}/{index}-{uuid.uuid4().hex}{suffix}"
