import io
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from app.config import settings


class MinioStorage:
    def __init__(self, client: Minio) -> None:
        self._client = client
        self._bucket = settings.minio_bucket

    def _ensure_bucket(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self._ensure_bucket()
        self._client.put_object(
            self._bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return key

    def download(self, key: str) -> bytes:
        response = self._client.get_object(self._bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, key: str) -> None:
        try:
            self._client.remove_object(self._bucket, key)
        except S3Error:
            pass

    def presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        from datetime import timedelta
        return self._client.presigned_get_object(
            self._bucket, key, expires=timedelta(seconds=expires_seconds)
        )

    def ping(self) -> bool:
        try:
            self._client.list_buckets()
            return True
        except Exception:
            return False


_storage_instance: MinioStorage | None = None


def get_storage() -> MinioStorage:
    global _storage_instance
    if _storage_instance is None:
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        _storage_instance = MinioStorage(client)
    return _storage_instance
