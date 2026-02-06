import hashlib
from typing import Any

from app.core.config import get_settings
from app.core.errors import StorageError
from app.infrastructure.storage.storage_client import StorageClient, StorageObjectMeta


class SupabaseStorageClient(StorageClient):
    def __init__(self, url: str, key: str, bucket: str):
        self._url = url
        self._key = key
        self._bucket = bucket
        self._client: Any = None

    def _get_storage(self) -> Any:
        if self._client is None:
            if not self._url or not self._key:
                raise StorageError("Supabase URL and KEY must be configured")
            try:
                from supabase import create_client
                client = create_client(self._url, self._key)
                self._client = client.storage
            except ImportError:
                raise StorageError("supabase package not installed")
        return self._client

    def upload_bytes(
        self,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> StorageObjectMeta:
        try:
            storage = self._get_storage()
            checksum = hashlib.sha256(content).hexdigest()
            storage.from_(self._bucket).upload(
                path=path,
                file=content,
                file_options={"content-type": content_type},
            )
            return StorageObjectMeta(
                path=path,
                size=len(content),
                checksum=checksum,
                content_type=content_type,
            )
        except Exception as e:
            raise StorageError(f"Upload failed: {e}")

    def get_download_url(self, path: str, expires_seconds: int = 3600) -> str:
        try:
            storage = self._get_storage()
            response = storage.from_(self._bucket).create_signed_url(
                path=path,
                expires_in=expires_seconds,
            )
            if isinstance(response, dict) and "signedURL" in response:
                return response["signedURL"]
            return response.get("signedUrl", str(response))
        except Exception as e:
            raise StorageError(f"Failed to generate signed URL: {e}")

    def delete(self, path: str) -> None:
        try:
            storage = self._get_storage()
            storage.from_(self._bucket).remove([path])
        except Exception as e:
            raise StorageError(f"Delete failed: {e}")


_storage_client: StorageClient | None = None


def get_storage_client() -> StorageClient:
    global _storage_client
    if _storage_client is None:
        settings = get_settings()
        _storage_client = SupabaseStorageClient(
            url=settings.SUPABASE_URL,
            key=settings.SUPABASE_SERVICE_ROLE_KEY,
            bucket=settings.SUPABASE_STORAGE_BUCKET,
        )
    return _storage_client


def reset_storage_client() -> None:
    global _storage_client
    _storage_client = None
