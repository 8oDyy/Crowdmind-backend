from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import NotFoundError, RepoError
from app.domain.entities.experiment import Experiment
from app.domain.enums.common import ExperimentStatus
from app.infrastructure.db.supabase_client import SupabaseClient


class ExperimentRepository:
    TABLE = "experiments"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_experiment(
        self,
        name: str,
        scenario: dict[str, Any] | None = None,
    ) -> Experiment:
        data = {
            "id": str(uuid4()),
            "name": name,
            "status": ExperimentStatus.DRAFT.value,
            "scenario": scenario,
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

    def set_status(
        self,
        experiment_id: str,
        status: ExperimentStatus,
    ) -> Experiment:
        update_data: dict[str, Any] = {"status": status.value}
        if status == ExperimentStatus.RUNNING:
            update_data["started_at"] = datetime.utcnow().isoformat()
        elif status == ExperimentStatus.STOPPED:
            update_data["ended_at"] = datetime.utcnow().isoformat()

        result = self._db.update(
            self.TABLE,
            data=update_data,
            filters={"id": experiment_id},
        )
        if not result:
            raise NotFoundError(f"Experiment {experiment_id} not found")
        return self._to_experiment(result[0])

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
            name=row["name"],
            status=ExperimentStatus(row["status"]),
            scenario=row.get("scenario"),
            started_at=self._parse_datetime_opt(row.get("started_at")),
            ended_at=self._parse_datetime_opt(row.get("ended_at")),
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
