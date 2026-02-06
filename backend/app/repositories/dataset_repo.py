from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import NotFoundError, RepoError
from app.domain.entities.dataset import Dataset, DatasetRow
from app.infrastructure.db.supabase_client import SupabaseClient


class DatasetRepository:
    TABLE_DATASETS = "datasets"
    TABLE_DATASET_ROWS = "dataset_rows"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_dataset(
        self,
        name: str,
        version: str,
        schema_def: dict[str, Any] | None = None,
        labels: list[str] | None = None,
    ) -> Dataset:
        data = {
            "id": str(uuid4()),
            "name": name,
            "version": version,
            "schema_def": schema_def,
            "labels": labels,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self._db.insert(self.TABLE_DATASETS, data)
        if not result:
            raise RepoError("Failed to create dataset")
        return self._to_dataset(result[0])

    def get_dataset(self, dataset_id: str) -> Dataset:
        row = self._db.select_one(self.TABLE_DATASETS, filters={"id": dataset_id})
        if not row:
            raise NotFoundError(f"Dataset {dataset_id} not found")
        return self._to_dataset(row)

    def insert_rows(self, dataset_id: str, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        data = []
        for row in rows:
            data.append({
                "id": str(uuid4()),
                "dataset_id": dataset_id,
                "input_data": row.get("input_data", {}),
                "label": row.get("label", ""),
                "meta": row.get("meta"),
                "created_at": datetime.utcnow().isoformat(),
            })
        result = self._db.insert(self.TABLE_DATASET_ROWS, data)
        return len(result)

    def list_rows(
        self,
        dataset_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DatasetRow]:
        rows = self._db.select(
            self.TABLE_DATASET_ROWS,
            filters={"dataset_id": dataset_id},
            limit=limit,
            offset=offset,
            order_by="created_at",
        )
        return [self._to_dataset_row(r) for r in rows]

    def count_rows(self, dataset_id: str) -> int:
        rows = self._db.select(
            self.TABLE_DATASET_ROWS,
            columns="id",
            filters={"dataset_id": dataset_id},
        )
        return len(rows)

    def _to_dataset(self, row: dict[str, Any]) -> Dataset:
        return Dataset(
            id=row["id"],
            name=row["name"],
            version=row["version"],
            schema_def=row.get("schema_def"),
            labels=row.get("labels"),
            created_at=self._parse_datetime(row.get("created_at")),
        )

    def _to_dataset_row(self, row: dict[str, Any]) -> DatasetRow:
        return DatasetRow(
            id=row["id"],
            dataset_id=row["dataset_id"],
            input_data=row.get("input_data", {}),
            label=row.get("label", ""),
            meta=row.get("meta"),
            created_at=self._parse_datetime(row.get("created_at")),
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()
