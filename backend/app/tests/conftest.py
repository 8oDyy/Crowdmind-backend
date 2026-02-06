from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import (
    get_dataset_repo,
    get_model_repo,
    get_storage_client,
)
from app.domain.entities.dataset import Dataset, DatasetVersion
from app.domain.entities.model import Model, ModelVersion
from app.infrastructure.storage.storage_client import StorageClient, StorageObjectMeta
from app.main import app


class FakeDatasetRepository:
    def __init__(self):
        self._datasets: dict[str, dict[str, Any]] = {}

    def create_dataset(
        self,
        name: str,
        dataset_type: str,
        created_by: str,
        description: str | None = None,
    ) -> Dataset:
        dataset_id = str(uuid4())
        dataset = Dataset(
            id=dataset_id,
            name=name,
            dataset_type=dataset_type,
            created_by=created_by,
            description=description,
            created_at=datetime.utcnow(),
        )
        self._datasets[dataset_id] = {
            "id": dataset_id,
            "name": name,
            "dataset_type": dataset_type,
            "created_by": created_by,
            "description": description,
            "created_at": dataset.created_at,
        }
        return dataset

    def get_dataset(self, dataset_id: str) -> Dataset:
        if dataset_id not in self._datasets:
            from app.core.errors import NotFoundError
            raise NotFoundError(f"Dataset {dataset_id} not found")
        d = self._datasets[dataset_id]
        return Dataset(
            id=d["id"],
            name=d["name"],
            dataset_type=d["dataset_type"],
            created_by=d["created_by"],
            description=d.get("description"),
            created_at=d["created_at"],
        )

    def list_datasets(self, limit: int = 100, offset: int = 0) -> list[Dataset]:
        datasets = list(self._datasets.values())[offset:offset + limit]
        return [
            Dataset(
                id=d["id"],
                name=d["name"],
                dataset_type=d["dataset_type"],
                created_by=d["created_by"],
                description=d.get("description"),
                created_at=d["created_at"],
            )
            for d in datasets
        ]


class FakeDatasetVersionRepository:
    def __init__(self):
        self._versions: dict[str, dict[str, Any]] = {}

    def create_version(
        self,
        dataset_id: str,
        version: str,
        file_path: str,
        format: str,
        checksum: str,
        size_kb: int,
        schema: dict[str, Any] | None = None,
        stats: dict[str, Any] | None = None,
    ) -> DatasetVersion:
        version_id = str(uuid4())
        dataset_version = DatasetVersion(
            id=version_id,
            dataset_id=dataset_id,
            version=version,
            file_path=file_path,
            format=format,
            checksum=checksum,
            size_kb=size_kb,
            schema=schema,
            stats=stats,
            created_at=datetime.utcnow(),
        )
        self._versions[version_id] = {
            "id": version_id,
            "dataset_id": dataset_id,
            "version": version,
            "file_path": file_path,
            "format": format,
            "checksum": checksum,
            "size_kb": size_kb,
            "schema": schema,
            "stats": stats,
            "created_at": dataset_version.created_at,
        }
        return dataset_version

    def get_version(self, version_id: str) -> DatasetVersion:
        if version_id not in self._versions:
            from app.core.errors import NotFoundError
            raise NotFoundError(f"Dataset version {version_id} not found")
        v = self._versions[version_id]
        return DatasetVersion(
            id=v["id"],
            dataset_id=v["dataset_id"],
            version=v["version"],
            file_path=v["file_path"],
            format=v["format"],
            checksum=v["checksum"],
            size_kb=v["size_kb"],
            schema=v.get("schema"),
            stats=v.get("stats"),
            created_at=v["created_at"],
        )

    def list_versions(
        self,
        dataset_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DatasetVersion]:
        versions = [
            v for v in self._versions.values()
            if v["dataset_id"] == dataset_id
        ][offset:offset + limit]
        return [
            DatasetVersion(
                id=v["id"],
                dataset_id=v["dataset_id"],
                version=v["version"],
                file_path=v["file_path"],
                format=v["format"],
                checksum=v["checksum"],
                size_kb=v["size_kb"],
                schema=v.get("schema"),
                stats=v.get("stats"),
                created_at=v["created_at"],
            )
            for v in versions
        ]


class FakeModelRepository:
    def __init__(self):
        self._models: dict[str, dict[str, Any]] = {}

    def create_model(
        self,
        name: str,
        framework: str,
        description: str | None = None,
    ) -> Model:
        model_id = str(uuid4())
        model = Model(
            id=model_id,
            name=name,
            framework=framework,
            description=description,
            created_at=datetime.utcnow(),
        )
        self._models[model_id] = {
            "id": model_id,
            "name": name,
            "framework": framework,
            "description": description,
            "created_at": model.created_at,
        }
        return model

    def get_model(self, model_id: str) -> Model:
        if model_id not in self._models:
            from app.core.errors import NotFoundError
            raise NotFoundError(f"Model {model_id} not found")
        m = self._models[model_id]
        return Model(
            id=m["id"],
            name=m["name"],
            framework=m["framework"],
            description=m.get("description"),
            created_at=m["created_at"],
        )

    def list_models(self, limit: int = 100, offset: int = 0) -> list[Model]:
        models = list(self._models.values())[offset:offset + limit]
        return [
            Model(
                id=m["id"],
                name=m["name"],
                framework=m["framework"],
                description=m.get("description"),
                created_at=m["created_at"],
            )
            for m in models
        ]


class FakeModelVersionRepository:
    def __init__(self):
        self._versions: dict[str, dict[str, Any]] = {}

    def create_version(
        self,
        model_id: str,
        version: str,
        file_path: str,
        checksum: str,
        size_kb: int,
    ) -> ModelVersion:
        version_id = str(uuid4())
        model_version = ModelVersion(
            id=version_id,
            model_id=model_id,
            version=version,
            file_path=file_path,
            checksum=checksum,
            size_kb=size_kb,
            created_at=datetime.utcnow(),
        )
        self._versions[version_id] = {
            "id": version_id,
            "model_id": model_id,
            "version": version,
            "file_path": file_path,
            "checksum": checksum,
            "size_kb": size_kb,
            "created_at": model_version.created_at,
        }
        return model_version

    def get_version(self, version_id: str) -> ModelVersion:
        if version_id not in self._versions:
            from app.core.errors import NotFoundError
            raise NotFoundError(f"Model version {version_id} not found")
        v = self._versions[version_id]
        return ModelVersion(
            id=v["id"],
            model_id=v["model_id"],
            version=v["version"],
            file_path=v["file_path"],
            checksum=v["checksum"],
            size_kb=v["size_kb"],
            created_at=v["created_at"],
        )

    def list_versions(
        self,
        model_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelVersion]:
        versions = [
            v for v in self._versions.values()
            if v["model_id"] == model_id
        ][offset:offset + limit]
        return [
            ModelVersion(
                id=v["id"],
                model_id=v["model_id"],
                version=v["version"],
                file_path=v["file_path"],
                checksum=v["checksum"],
                size_kb=v["size_kb"],
                created_at=v["created_at"],
            )
            for v in versions
        ]


class FakeStorageClient(StorageClient):
    def __init__(self):
        self._files: dict[str, bytes] = {}

    def upload_bytes(
        self,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> StorageObjectMeta:
        import hashlib
        self._files[path] = content
        return StorageObjectMeta(
            path=path,
            size=len(content),
            checksum=hashlib.sha256(content).hexdigest(),
            content_type=content_type,
        )

    def get_download_url(self, path: str, expires_seconds: int = 3600) -> str:
        return f"https://fake-storage.example.com/{path}?expires={expires_seconds}"

    def delete(self, path: str) -> None:
        if path in self._files:
            del self._files[path]


@pytest.fixture
def fake_dataset_repo() -> FakeDatasetRepository:
    return FakeDatasetRepository()


@pytest.fixture
def fake_dataset_version_repo() -> FakeDatasetVersionRepository:
    return FakeDatasetVersionRepository()


@pytest.fixture
def fake_model_repo() -> FakeModelRepository:
    return FakeModelRepository()


@pytest.fixture
def fake_model_version_repo() -> FakeModelVersionRepository:
    return FakeModelVersionRepository()


@pytest.fixture
def fake_storage() -> FakeStorageClient:
    return FakeStorageClient()


@pytest.fixture
def client(
    fake_dataset_repo: FakeDatasetRepository,
    fake_dataset_version_repo: FakeDatasetVersionRepository,
    fake_model_repo: FakeModelRepository,
    fake_model_version_repo: FakeModelVersionRepository,
    fake_storage: FakeStorageClient,
) -> TestClient:
    from app.core.dependencies import get_dataset_version_repo, get_model_version_repo
    
    app.dependency_overrides[get_dataset_repo] = lambda: fake_dataset_repo
    app.dependency_overrides[get_dataset_version_repo] = lambda: fake_dataset_version_repo
    app.dependency_overrides[get_model_repo] = lambda: fake_model_repo
    app.dependency_overrides[get_model_version_repo] = lambda: fake_model_version_repo
    app.dependency_overrides[get_storage_client] = lambda: fake_storage

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
