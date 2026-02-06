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
from app.domain.entities.dataset import Dataset, DatasetRow
from app.domain.entities.model import Model
from app.infrastructure.storage.storage_client import StorageClient, StorageObjectMeta
from app.main import app
from app.repositories.dataset_repo import DatasetRepository
from app.repositories.model_repo import ModelRepository


class FakeDatasetRepository:
    def __init__(self):
        self._datasets: dict[str, dict[str, Any]] = {}
        self._rows: dict[str, list[dict[str, Any]]] = {}

    def create_dataset(
        self,
        name: str,
        version: str,
        schema_def: dict[str, Any] | None = None,
        labels: list[str] | None = None,
    ) -> Dataset:
        dataset_id = str(uuid4())
        dataset = Dataset(
            id=dataset_id,
            name=name,
            version=version,
            schema_def=schema_def,
            labels=labels,
            created_at=datetime.utcnow(),
        )
        self._datasets[dataset_id] = {
            "id": dataset_id,
            "name": name,
            "version": version,
            "schema_def": schema_def,
            "labels": labels,
            "created_at": dataset.created_at,
        }
        self._rows[dataset_id] = []
        return dataset

    def get_dataset(self, dataset_id: str) -> Dataset:
        if dataset_id not in self._datasets:
            from app.core.errors import NotFoundError
            raise NotFoundError(f"Dataset {dataset_id} not found")
        d = self._datasets[dataset_id]
        return Dataset(
            id=d["id"],
            name=d["name"],
            version=d["version"],
            schema_def=d.get("schema_def"),
            labels=d.get("labels"),
            created_at=d["created_at"],
        )

    def insert_rows(self, dataset_id: str, rows: list[dict[str, Any]]) -> int:
        if dataset_id not in self._rows:
            self._rows[dataset_id] = []
        for row in rows:
            self._rows[dataset_id].append({
                "id": str(uuid4()),
                "dataset_id": dataset_id,
                "input_data": row.get("input_data", {}),
                "label": row.get("label", ""),
                "meta": row.get("meta"),
                "created_at": datetime.utcnow(),
            })
        return len(rows)

    def list_rows(
        self,
        dataset_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DatasetRow]:
        rows = self._rows.get(dataset_id, [])[offset:offset + limit]
        return [
            DatasetRow(
                id=r["id"],
                dataset_id=r["dataset_id"],
                input_data=r["input_data"],
                label=r["label"],
                meta=r.get("meta"),
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def count_rows(self, dataset_id: str) -> int:
        return len(self._rows.get(dataset_id, []))


class FakeModelRepository:
    def __init__(self):
        self._models: dict[str, dict[str, Any]] = {}

    def create_model(
        self,
        name: str,
        version: str,
        target_device: str | None = None,
        labels: list[str] | None = None,
    ) -> Model:
        model_id = str(uuid4())
        model = Model(
            id=model_id,
            name=name,
            version=version,
            target_device=target_device,
            labels=labels,
            created_at=datetime.utcnow(),
        )
        self._models[model_id] = {
            "id": model_id,
            "name": name,
            "version": version,
            "target_device": target_device,
            "labels": labels,
            "storage_path": None,
            "checksum": None,
            "size": None,
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
            version=m["version"],
            target_device=m.get("target_device"),
            labels=m.get("labels"),
            storage_path=m.get("storage_path"),
            checksum=m.get("checksum"),
            size=m.get("size"),
            created_at=m["created_at"],
        )

    def attach_file(
        self,
        model_id: str,
        storage_path: str,
        checksum: str,
        size: int,
    ) -> Model:
        if model_id not in self._models:
            from app.core.errors import NotFoundError
            raise NotFoundError(f"Model {model_id} not found")
        self._models[model_id]["storage_path"] = storage_path
        self._models[model_id]["checksum"] = checksum
        self._models[model_id]["size"] = size
        return self.get_model(model_id)

    def list_models(self, limit: int = 100, offset: int = 0) -> list[Model]:
        models = list(self._models.values())[offset:offset + limit]
        return [
            Model(
                id=m["id"],
                name=m["name"],
                version=m["version"],
                target_device=m.get("target_device"),
                labels=m.get("labels"),
                storage_path=m.get("storage_path"),
                checksum=m.get("checksum"),
                size=m.get("size"),
                created_at=m["created_at"],
            )
            for m in models
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
def fake_model_repo() -> FakeModelRepository:
    return FakeModelRepository()


@pytest.fixture
def fake_storage() -> FakeStorageClient:
    return FakeStorageClient()


@pytest.fixture
def client(
    fake_dataset_repo: FakeDatasetRepository,
    fake_model_repo: FakeModelRepository,
    fake_storage: FakeStorageClient,
) -> TestClient:
    app.dependency_overrides[get_dataset_repo] = lambda: fake_dataset_repo
    app.dependency_overrides[get_model_repo] = lambda: fake_model_repo
    app.dependency_overrides[get_storage_client] = lambda: fake_storage

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
