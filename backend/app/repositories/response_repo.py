from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import NotFoundError, RepoError
from app.domain.entities.response import Response
from app.infrastructure.db.supabase_client import SupabaseClient


class ResponseRepository:
    TABLE = "responses"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_response(self, data: dict[str, Any]) -> Response:
        if "id" not in data:
            data["id"] = str(uuid4())
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow().isoformat()
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create response")
        return self._to_entity(result[0])

    def create_responses_batch(self, rows: list[dict[str, Any]]) -> list[Response]:
        for r in rows:
            if "id" not in r:
                r["id"] = str(uuid4())
            if "created_at" not in r:
                r["created_at"] = datetime.utcnow().isoformat()
        result = self._db.insert(self.TABLE, rows)
        if not result:
            raise RepoError("Failed to create responses batch")
        return [self._to_entity(r) for r in result]

    def get_response(self, response_id: str) -> Response:
        row = self._db.select_one(self.TABLE, filters={"id": response_id})
        if not row:
            raise NotFoundError(f"Response {response_id} not found")
        return self._to_entity(row)

    def list_responses_by_survey(
        self,
        survey_id: str,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[Response]:
        rows = self._db.select(
            self.TABLE,
            filters={"survey_id": survey_id},
            limit=limit,
            offset=offset,
            order_by="created_at",
        )
        return [self._to_entity(r) for r in rows]

    def delete_responses_by_survey(self, survey_id: str) -> None:
        self._db.delete(self.TABLE, filters={"survey_id": survey_id})

    def _to_entity(self, row: dict[str, Any]) -> Response:
        return Response(
            id=row["id"],
            survey_id=row["survey_id"],
            agent_id=row["agent_id"],
            stance=row.get("stance"),
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
