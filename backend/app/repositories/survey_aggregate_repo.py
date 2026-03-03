from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import RepoError
from app.domain.entities.survey_aggregate import SurveyAggregate
from app.infrastructure.db.supabase_client import SupabaseClient


class SurveyAggregateRepository:
    TABLE = "survey_aggregates"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def upsert_aggregate(
        self,
        survey_id: str,
        aggregation: dict[str, Any],
        question_id: str | None = None,
    ) -> SurveyAggregate:
        data: dict[str, Any] = {
            "id": str(uuid4()),
            "survey_id": survey_id,
            "question_id": question_id,
            "aggregation": aggregation,
            "computed_at": datetime.utcnow().isoformat(),
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to upsert survey aggregate")
        return self._to_entity(result[0])

    def get_aggregates(self, survey_id: str) -> list[SurveyAggregate]:
        rows = self._db.select(
            self.TABLE,
            filters={"survey_id": survey_id},
            order_by="computed_at",
        )
        return [self._to_entity(r) for r in rows]

    def delete_by_survey(self, survey_id: str) -> None:
        self._db.delete(self.TABLE, filters={"survey_id": survey_id})

    def _to_entity(self, row: dict[str, Any]) -> SurveyAggregate:
        return SurveyAggregate(
            id=row["id"],
            survey_id=row["survey_id"],
            question_id=row.get("question_id"),
            aggregation=row.get("aggregation", {}),
            computed_at=self._parse_dt(row.get("computed_at")) or datetime.utcnow(),
        )

    @staticmethod
    def _parse_dt(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return None
