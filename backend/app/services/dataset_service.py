import csv
import io
import random
from typing import Any

from faker import Faker

from app.core.config import Settings
from app.domain.entities.dataset import Dataset, DatasetVersion
from app.infrastructure.storage.storage_client import StorageClient
from app.repositories.dataset_repo import DatasetRepository, DatasetVersionRepository


class DatasetService:
    def __init__(
        self,
        dataset_repo: DatasetRepository,
        version_repo: DatasetVersionRepository,
        storage: StorageClient,
        settings: Settings,
    ):
        self._dataset_repo = dataset_repo
        self._version_repo = version_repo
        self._storage = storage
        self._settings = settings

    def create_dataset(
        self,
        name: str,
        dataset_type: str,
        created_by: str,
        description: str | None = None,
    ) -> Dataset:
        return self._dataset_repo.create_dataset(
            name=name,
            dataset_type=dataset_type,
            created_by=created_by,
            description=description,
        )

    def get_dataset(self, dataset_id: str) -> Dataset:
        return self._dataset_repo.get_dataset(dataset_id)

    def list_datasets(self, limit: int = 100, offset: int = 0) -> list[Dataset]:
        return self._dataset_repo.list_datasets(limit=limit, offset=offset)

    def create_version(
        self,
        dataset_id: str,
        version: str,
        file_bytes: bytes,
        format: str,
        content_type: str = "application/octet-stream",
        schema: dict[str, Any] | None = None,
        stats: dict[str, Any] | None = None,
    ) -> DatasetVersion:
        self._dataset_repo.get_dataset(dataset_id)

        path = f"datasets/{dataset_id}/{version}.{format}"
        meta = self._storage.upload_bytes(
            path=path,
            content=file_bytes,
            content_type=content_type,
        )

        size_kb = meta.size // 1024

        return self._version_repo.create_version(
            dataset_id=dataset_id,
            version=version,
            file_path=meta.path,
            format=format,
            checksum=meta.checksum,
            size_kb=size_kb,
            schema=schema,
            stats=stats,
        )

    def get_version(self, version_id: str) -> DatasetVersion:
        return self._version_repo.get_version(version_id)

    def list_versions(
        self,
        dataset_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DatasetVersion]:
        return self._version_repo.list_versions(
            dataset_id=dataset_id,
            limit=limit,
            offset=offset,
        )

    def generate_synthetic_version(
        self,
        dataset_id: str,
        version: str,
        n: int = 100,
        seed: int | None = None,
        labels: list[str] | None = None,
    ) -> DatasetVersion:
        self._dataset_repo.get_dataset(dataset_id)

        fake = Faker()
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        labels = labels or ["class_0", "class_1", "class_2"]
        num_features = 5
        feature_names = [f"feature_{i}" for i in range(1, num_features + 1)]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(feature_names + ["label"])

        labels_data = []
        for _ in range(n):
            row = [fake.pyfloat(min_value=-3.0, max_value=3.0) for _ in range(num_features)]
            label = random.choice(labels)
            labels_data.append(label)
            row.append(label)
            writer.writerow(row)

        content = output.getvalue().encode("utf-8")

        label_dist = {label: labels_data.count(label) for label in labels}
        stats = {
            "row_count": n,
            "num_features": num_features,
            "label_distribution": label_dist,
        }

        return self.create_version(
            dataset_id=dataset_id,
            version=version,
            file_bytes=content,
            format="csv",
            content_type="text/csv",
            schema={
                "features": feature_names,
                "label_column": "label",
                "labels": labels,
            },
            stats=stats,
        )

    def get_download_url(self, version_id: str, expires_seconds: int = 3600) -> str:
        version = self._version_repo.get_version(version_id)
        return self._storage.get_download_url(version.file_path, expires_seconds)
