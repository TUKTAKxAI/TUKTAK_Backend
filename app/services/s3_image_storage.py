import asyncio
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

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
        if not self.bucket:
            return f"/uploads/{self.key}"
        return f"s3://{self.bucket}/{self.key}"


class S3ImageStorage:
    def __init__(self) -> None:
        self.bucket_name = settings.s3_bucket_name
        self.prefix = settings.ai_estimate_image_prefix.strip("/")
        self.local_root = settings.local_upload_path
        self.client = None
        if self.bucket_name:
            import boto3

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
            if self.client and self.bucket_name:
                await asyncio.to_thread(self._put_object, key, body, extra_args)
                bucket = self.bucket_name
            else:
                await asyncio.to_thread(self._write_local_file, key, body)
                bucket = ""
            stored_images.append(
                StoredImage(
                    bucket=bucket,
                    key=key,
                    original_filename=filename,
                    content_type=image.content_type,
                )
            )
        return stored_images

    async def delete_images(self, stored_images: list[StoredImage]) -> None:
        if not stored_images:
            return
        if not self.client or not self.bucket_name:
            await asyncio.to_thread(self._delete_local_images, stored_images)
            return
        objects = [{"Key": image.key} for image in stored_images]
        await asyncio.to_thread(
            self.client.delete_objects,
            Bucket=self.bucket_name,
            Delete={"Objects": objects, "Quiet": True},
        )

    def _put_object(self, key: str, body: bytes, extra_args: dict[str, str] | None) -> None:
        if not self.client or not self.bucket_name:
            raise RuntimeError("S3 client is not configured.")
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

    def _write_local_file(self, key: str, body: bytes) -> None:
        target = (self.local_root / key).resolve()
        if not target.is_relative_to(self.local_root):
            raise RuntimeError("Invalid upload path.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)

    def _delete_local_images(self, stored_images: list[StoredImage]) -> None:
        for image in stored_images:
            target = (self.local_root / image.key).resolve()
            if target.is_relative_to(self.local_root) and target.exists():
                target.unlink()


def display_image_url(image_url: str) -> str:
    if not image_url.startswith("s3://"):
        return image_url
    parts = image_url.removeprefix("s3://").split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return image_url
    bucket, key = parts
    try:
        import boto3

        client = boto3.client("s3", region_name=settings.aws_region)
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=settings.s3_presigned_url_expires_seconds,
        )
    except Exception:
        encoded_key = quote(key, safe="/")
        return f"https://{bucket}.s3.{settings.aws_region}.amazonaws.com/{encoded_key}"


def display_image_urls(image_urls: list[str] | None) -> list[str]:
    return [display_image_url(image_url) for image_url in image_urls or [] if image_url]
