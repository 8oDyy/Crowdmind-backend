from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import NotFoundError, RepoError
from app.domain.entities.dataset import Dataset, DatasetVersion, TrainingRun
from app.infrastructure.db.supabase_client import SupabaseClient


class DatasetRepository:
    TABLE = "datasets"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_dataset(
        self,
        name: str,
        dataset_type: str,
        created_by: str,
        description: str | None = None,
    ) -> Dataset:
        data = {
            "id": str(uuid4()),
            "name": name,
            "description": description,
            "dataset_type": dataset_type,
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create dataset")
        return self._to_dataset(result[0])

    def get_dataset(self, dataset_id: str) -> Dataset:
        row = self._db.select_one(self.TABLE, filters={"id": dataset_id})
        if not row:
            raise NotFoundError(f"Dataset {dataset_id} not found")
        return self._to_dataset(row)

    def list_datasets(self, limit: int = 100, offset: int = 0) -> list[Dataset]:
        rows = self._db.select(
            self.TABLE,
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_desc=True,
        )
        return [self._to_dataset(r) for r in rows]

    def _to_dataset(self, row: dict[str, Any]) -> Dataset:
        return Dataset(
            id=row["id"],
            name=row["name"],
            dataset_type=row["dataset_type"],
            created_by=row["created_by"],
            description=row.get("description"),
            created_at=self._parse_datetime(row.get("created_at")),
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()


class DatasetVersionRepository:
    TABLE = "dataset_versions"

    def __init__(self, db: SupabaseClient):
        self._db = db

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
        data = {
            "id": str(uuid4()),
            "dataset_id": dataset_id,
            "version": version,
            "file_path": file_path,
            "format": format,
            "checksum": checksum,
            "size_kb": size_kb,
            "schema": schema,
            "stats": stats,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create dataset version")
        return self._to_version(result[0])

    def get_version(self, version_id: str) -> DatasetVersion:
        row = self._db.select_one(self.TABLE, filters={"id": version_id})
        if not row:
            raise NotFoundError(f"Dataset version {version_id} not found")
        return self._to_version(row)

    def list_versions(
        self,
        dataset_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DatasetVersion]:
        rows = self._db.select(
            self.TABLE,
            filters={"dataset_id": dataset_id},
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_desc=True,
        )
        return [self._to_version(r) for r in rows]

    def _to_version(self, row: dict[str, Any]) -> DatasetVersion:
        return DatasetVersion(
            id=row["id"],
            dataset_id=row["dataset_id"],
            version=row["version"],
            file_path=row["file_path"],
            format=row["format"],
            checksum=row["checksum"],
            size_kb=row["size_kb"],
            schema=row.get("schema"),
            stats=row.get("stats"),
            created_at=self._parse_datetime(row.get("created_at")),
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()


class TrainingRunRepository:
    TABLE = "training_runs"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_run(
        self,
        dataset_version_id: str,
        model_id: str,
        status: str = "queued",
        parameters: dict[str, Any] | None = None,
    ) -> TrainingRun:
        data = {
            "id": str(uuid4()),
            "dataset_version_id": dataset_version_id,
            "model_id": model_id,
            "status": status,
            "parameters": parameters,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create training run")
        return self._to_run(result[0])

    def get_run(self, run_id: str) -> TrainingRun:
        row = self._db.select_one(self.TABLE, filters={"id": run_id})
        if not row:
            raise NotFoundError(f"Training run {run_id} not found")
        return self._to_run(row)

    def update_status(
        self,
        run_id: str,
        status: str,
        metrics: dict[str, Any] | None = None,
        output_model_version_id: str | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> TrainingRun:
        data: dict[str, Any] = {"status": status}
        if metrics is not None:
            data["metrics"] = metrics
        if output_model_version_id is not None:
            data["output_model_version_id"] = output_model_version_id
        if started_at is not None:
            data["started_at"] = started_at.isoformat()
        if finished_at is not None:
            data["finished_at"] = finished_at.isoformat()

        result = self._db.update(self.TABLE, data=data, filters={"id": run_id})
        if not result:
            raise NotFoundError(f"Training run {run_id} not found")
        return self._to_run(result[0])

    def list_runs(
        self,
        dataset_version_id: str | None = None,
        model_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TrainingRun]:
        filters = {}
        if dataset_version_id:
            filters["dataset_version_id"] = dataset_version_id
        if model_id:
            filters["model_id"] = model_id

        rows = self._db.select(
            self.TABLE,
            filters=filters if filters else None,
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_desc=True,
        )
        return [self._to_run(r) for r in rows]

    def _to_run(self, row: dict[str, Any]) -> TrainingRun:
        return TrainingRun(
            id=row["id"],
            dataset_version_id=row["dataset_version_id"],
            model_id=row["model_id"],
            status=row["status"],
            output_model_version_id=row.get("output_model_version_id"),
            parameters=row.get("parameters"),
            metrics=row.get("metrics"),
            logs_path=row.get("logs_path"),
            started_at=self._parse_datetime_opt(row.get("started_at")),
            finished_at=self._parse_datetime_opt(row.get("finished_at")),
            created_at=self._parse_datetime(row.get("created_at")),
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()

    def _parse_datetime_opt(self, value: Any) -> datetime | None:
        if value is None:
            return None
        return self._parse_datetime(value)
