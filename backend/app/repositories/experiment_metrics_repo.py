from datetime import datetime
from typing import Any

from app.core.errors import NotFoundError, RepoError
from app.domain.entities.experiment_metrics import ExperimentMetrics
from app.infrastructure.db.supabase_client import SupabaseClient


class ExperimentMetricsRepository:
    TABLE = "experiment_metrics"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def save_metrics(
        self,
        experiment_id: str,
        metrics: dict[str, Any],
    ) -> ExperimentMetrics:
        data = {
            "experiment_id": experiment_id,
            "metrics": metrics,
            "computed_at": datetime.utcnow().isoformat(),
        }
        existing = self._db.select_one(
            self.TABLE,
            filters={"experiment_id": experiment_id},
        )
        if existing:
            result = self._db.update(
                self.TABLE,
                data=data,
                filters={"experiment_id": experiment_id},
            )
        else:
            result = self._db.insert(self.TABLE, data)
        
        if not result:
            raise RepoError("Failed to save experiment metrics")
        return self._to_metrics(result[0])

    def get_metrics(self, experiment_id: str) -> ExperimentMetrics | None:
        row = self._db.select_one(
            self.TABLE,
            filters={"experiment_id": experiment_id},
        )
        return self._to_metrics(row) if row else None

    def _to_metrics(self, row: dict[str, Any]) -> ExperimentMetrics:
        return ExperimentMetrics(
            experiment_id=row["experiment_id"],
            metrics=row["metrics"],
            computed_at=self._parse_datetime(row.get("computed_at")),
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()
