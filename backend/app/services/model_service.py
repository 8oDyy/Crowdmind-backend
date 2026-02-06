import hashlib

from app.core.config import Settings
from app.core.errors import ValidationError
from app.domain.entities.model import Model
from app.infrastructure.storage.storage_client import StorageClient
from app.repositories.model_repo import ModelRepository


class ModelService:
    def __init__(
        self,
        repo: ModelRepository,
        storage: StorageClient,
        settings: Settings,
    ):
        self._repo = repo
        self._storage = storage
        self._settings = settings

    def create_model(
        self,
        name: str,
        version: str,
        target_device: str | None = None,
        labels: list[str] | None = None,
    ) -> Model:
        return self._repo.create_model(
            name=name,
            version=version,
            target_device=target_device,
            labels=labels,
        )

    def get_model(self, model_id: str) -> Model:
        return self._repo.get_model(model_id)

    def upload_tflite(
        self,
        model_id: str,
        file_bytes: bytes,
        content_type: str = "application/octet-stream",
    ) -> Model:
        model = self._repo.get_model(model_id)

        if len(file_bytes) > self._settings.max_upload_bytes:
            raise ValidationError(
                f"File too large. Max size: {self._settings.MAX_UPLOAD_MB}MB"
            )

        checksum = hashlib.sha256(file_bytes).hexdigest()
        path = f"models/{model_id}/{model.version}.tflite"

        meta = self._storage.upload_bytes(
            path=path,
            content=file_bytes,
            content_type=content_type,
        )

        return self._repo.attach_file(
            model_id=model_id,
            storage_path=meta.path,
            checksum=meta.checksum,
            size=meta.size,
        )

    def get_download_url(self, model_id: str, expires_seconds: int = 3600) -> str:
        model = self._repo.get_model(model_id)
        if not model.storage_path:
            raise ValidationError(f"Model {model_id} has no uploaded file")
        return self._storage.get_download_url(model.storage_path, expires_seconds)

    def list_models(self, limit: int = 100, offset: int = 0) -> list[Model]:
        return self._repo.list_models(limit=limit, offset=offset)
