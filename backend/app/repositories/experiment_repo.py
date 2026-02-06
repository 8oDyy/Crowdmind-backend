from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import NotFoundError, RepoError
from app.domain.entities.experiment import Experiment
from app.infrastructure.db.supabase_client import SupabaseClient


class ExperimentRepository:
    TABLE = "experiments"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_experiment(
        self,
        title: str,
        message: str,
        mode: str,
        created_by: str,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> Experiment:
        data = {
            "id": str(uuid4()),
            "title": title,
            "description": description,
            "message": message,
            "mode": mode,
            "parameters": parameters,
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create experiment")
        return self._to_experiment(result[0])

    def get_experiment(self, experiment_id: str) -> Experiment:
        row = self._db.select_one(self.TABLE, filters={"id": experiment_id})
        if not row:
            raise NotFoundError(f"Experiment {experiment_id} not found")
        return self._to_experiment(row)


    def list_experiments(self, limit: int = 100, offset: int = 0) -> list[Experiment]:
        rows = self._db.select(
            self.TABLE,
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_desc=True,
        )
        return [self._to_experiment(r) for r in rows]

    def _to_experiment(self, row: dict[str, Any]) -> Experiment:
        return Experiment(
            id=row["id"],
            title=row["title"],
            message=row["message"],
            mode=row["mode"],
            created_by=row["created_by"],
            description=row.get("description"),
            parameters=row.get("parameters"),
            created_at=self._parse_datetime(row.get("created_at")),
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()

