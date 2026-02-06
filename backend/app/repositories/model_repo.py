from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import NotFoundError, RepoError
from app.domain.entities.model import Model, ModelVersion
from app.infrastructure.db.supabase_client import SupabaseClient


class ModelRepository:
    TABLE = "ml_models"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_model(
        self,
        name: str,
        framework: str,
        description: str | None = None,
    ) -> Model:
        data = {
            "id": str(uuid4()),
            "name": name,
            "framework": framework,
            "description": description,
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
            framework=row["framework"],
            description=row.get("description"),
            created_at=self._parse_datetime(row.get("created_at")),
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()


class ModelVersionRepository:
    TABLE = "ml_model_versions"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_version(
        self,
        model_id: str,
        version: str,
        file_path: str,
        checksum: str,
        size_kb: int,
    ) -> ModelVersion:
        data = {
            "id": str(uuid4()),
            "model_id": model_id,
            "version": version,
            "file_path": file_path,
            "checksum": checksum,
            "size_kb": size_kb,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create model version")
        return self._to_model_version(result[0])

    def get_version(self, version_id: str) -> ModelVersion:
        row = self._db.select_one(self.TABLE, filters={"id": version_id})
        if not row:
            raise NotFoundError(f"Model version {version_id} not found")
        return self._to_model_version(row)

    def list_versions(
        self,
        model_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelVersion]:
        rows = self._db.select(
            self.TABLE,
            filters={"model_id": model_id},
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_desc=True,
        )
        return [self._to_model_version(r) for r in rows]

    def _to_model_version(self, row: dict[str, Any]) -> ModelVersion:
        return ModelVersion(
            id=row["id"],
            model_id=row["model_id"],
            version=row["version"],
            file_path=row["file_path"],
            checksum=row["checksum"],
            size_kb=row["size_kb"],
            created_at=self._parse_datetime(row.get("created_at")),
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()
