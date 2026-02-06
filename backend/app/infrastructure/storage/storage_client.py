from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StorageObjectMeta:
    path: str
    size: int
    checksum: str
    content_type: str


class StorageClient(ABC):
    @abstractmethod
    def upload_bytes(
        self,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> StorageObjectMeta:
        pass

    @abstractmethod
    def get_download_url(self, path: str, expires_seconds: int = 3600) -> str:
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        pass
