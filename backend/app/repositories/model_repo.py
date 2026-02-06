from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import NotFoundError, RepoError
from app.domain.entities.model import Model
from app.infrastructure.db.supabase_client import SupabaseClient


class ModelRepository:
    TABLE = "ml_models"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_model(
        self,
        name: str,
        version: str,
        target_device: str | None = None,
        labels: list[str] | None = None,
    ) -> Model:
        data = {
            "id": str(uuid4()),
            "name": name,
            "version": version,
            "target_device": target_device,
            "labels": labels,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create model")
        return self._to_model(result[0])

    def get_model(self, model_id: str) -> Model:
        row = self._db.select_one(self.TABLE, filters={"id": model_id})
        if not row:
            raise NotFoundError(f"Model {model_id} not found")
        return self._to_model(row)

    def attach_file(
        self,
        model_id: str,
        storage_path: str,
        checksum: str,
        size: int,
    ) -> Model:
        result = self._db.update(
            self.TABLE,
            data={
                "storage_path": storage_path,
                "checksum": checksum,
                "size": size,
            },
            filters={"id": model_id},
        )
        if not result:
            raise NotFoundError(f"Model {model_id} not found")
        return self._to_model(result[0])

    def list_models(self, limit: int = 100, offset: int = 0) -> list[Model]:
        rows = self._db.select(
            self.TABLE,
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_desc=True,
        )
        return [self._to_model(r) for r in rows]

    def _to_model(self, row: dict[str, Any]) -> Model:
        return Model(
            id=row["id"],
            name=row["name"],
            version=row["version"],
            target_device=row.get("target_device"),
            labels=row.get("labels"),
            storage_path=row.get("storage_path"),
            checksum=row.get("checksum"),
            size=row.get("size"),
            created_at=self._parse_datetime(row.get("created_at")),
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()
