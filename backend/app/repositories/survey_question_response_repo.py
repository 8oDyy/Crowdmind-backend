from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import RepoError
from app.domain.entities.survey_question_response import SurveyQuestionResponse
from app.infrastructure.db.supabase_client import SupabaseClient


class SurveyQuestionResponseRepository:
    TABLE = "survey_question_responses"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_batch(self, rows: list[dict[str, Any]]) -> list[SurveyQuestionResponse]:
        for r in rows:
            if "id" not in r:
                r["id"] = str(uuid4())
            if "created_at" not in r:
                r["created_at"] = datetime.utcnow().isoformat()
        result = self._db.insert(self.TABLE, rows)
        if not result:
            raise RepoError("Failed to create survey question responses")
        return [self._to_entity(r) for r in result]

    def list_by_survey(
        self,
        survey_id: str,
        limit: int = 5000,
        offset: int = 0,
    ) -> list[SurveyQuestionResponse]:
        rows = self._db.select(
            self.TABLE,
            filters={"survey_id": survey_id},
            limit=limit,
            offset=offset,
            order_by="created_at",
        )
        return [self._to_entity(r) for r in rows]

    def list_by_survey_and_question(
        self,
        survey_id: str,
        question_id: str,
    ) -> list[SurveyQuestionResponse]:
        rows = self._db.select(
            self.TABLE,
            filters={"survey_id": survey_id, "question_id": question_id},
            order_by="created_at",
        )
        return [self._to_entity(r) for r in rows]

    def delete_by_survey(self, survey_id: str) -> None:
        self._db.delete(self.TABLE, filters={"survey_id": survey_id})

    def _to_entity(self, row: dict[str, Any]) -> SurveyQuestionResponse:
        return SurveyQuestionResponse(
            id=row["id"],
            survey_id=row["survey_id"],
            agent_id=row["agent_id"],
            question_id=row["question_id"],
            answer=row["answer"],
            confidence=float(row.get("confidence", 0.5)),
            short_reason=row.get("short_reason"),
            raw_llm_output=row.get("raw_llm_output"),
            is_fallback=bool(row.get("is_fallback", False)),
            created_at=self._parse_dt(row.get("created_at")) or datetime.utcnow(),
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
