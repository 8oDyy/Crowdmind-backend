
from app.core.config import Settings
from app.core.errors import ValidationError
from app.domain.entities.model import Model, ModelVersion
from app.infrastructure.storage.storage_client import StorageClient
from app.repositories.model_repo import ModelRepository, ModelVersionRepository


class ModelService:
    def __init__(
        self,
        model_repo: ModelRepository,
        version_repo: ModelVersionRepository,
        storage: StorageClient,
        settings: Settings,
    ):
        self._model_repo = model_repo
        self._version_repo = version_repo
        self._storage = storage
        self._settings = settings

    def create_model(
        self,
        name: str,
        framework: str,
        description: str | None = None,
    ) -> Model:
        return self._model_repo.create_model(
            name=name,
            framework=framework,
            description=description,
        )

    def get_model(self, model_id: str) -> Model:
        return self._model_repo.get_model(model_id)

    def list_models(self, limit: int = 100, offset: int = 0) -> list[Model]:
        return self._model_repo.list_models(limit=limit, offset=offset)

    def create_version(
        self,
        model_id: str,
        version: str,
        file_bytes: bytes,
        content_type: str = "application/octet-stream",
    ) -> ModelVersion:
        model = self._model_repo.get_model(model_id)

        if len(file_bytes) > self._settings.max_upload_bytes:
            raise ValidationError(
                f"File too large. Max size: {self._settings.MAX_UPLOAD_MB}MB"
            )

        path = f"models/{model_id}/{version}.tflite"

        meta = self._storage.upload_bytes(
            path=path,
            content=file_bytes,
            content_type=content_type,
        )

        size_kb = meta.size // 1024

        return self._version_repo.create_version(
            model_id=model_id,
            version=version,
            file_path=meta.path,
            checksum=meta.checksum,
            size_kb=size_kb,
        )

    def get_version(self, version_id: str) -> ModelVersion:
        return self._version_repo.get_version(version_id)

    def list_versions(
        self,
        model_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelVersion]:
        return self._version_repo.list_versions(
            model_id=model_id,
            limit=limit,
            offset=offset,
        )

    def get_download_url(self, version_id: str, expires_seconds: int = 3600) -> str:
        version = self._version_repo.get_version(version_id)
        return self._storage.get_download_url(version.file_path, expires_seconds)
