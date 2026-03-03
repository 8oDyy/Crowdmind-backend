from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import RepoError
from app.domain.entities.survey_question import SurveyQuestion
from app.infrastructure.db.supabase_client import SupabaseClient


class SurveyQuestionRepository:
    TABLE = "survey_questions"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_questions_batch(
        self, questions: list[dict[str, Any]]
    ) -> list[SurveyQuestion]:
        for q in questions:
            if "id" not in q:
                q["id"] = str(uuid4())
            if "created_at" not in q:
                q["created_at"] = datetime.utcnow().isoformat()
        result = self._db.insert(self.TABLE, questions)
        if not result:
            raise RepoError("Failed to create survey questions")
        return [self._to_entity(r) for r in result]

    def list_by_survey(self, survey_id: str) -> list[SurveyQuestion]:
        rows = self._db.select(
            self.TABLE,
            filters={"survey_id": survey_id},
            order_by="question_index",
        )
        return [self._to_entity(r) for r in rows]

    def delete_by_survey(self, survey_id: str) -> None:
        self._db.delete(self.TABLE, filters={"survey_id": survey_id})

    def _to_entity(self, row: dict[str, Any]) -> SurveyQuestion:
        return SurveyQuestion(
            id=row["id"],
            survey_id=row["survey_id"],
            question_index=int(row["question_index"]),
            question_id=row["question_id"],
            type=row["type"],
            text=row["text"],
            choices=row.get("choices"),
            scale=row.get("scale"),
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
