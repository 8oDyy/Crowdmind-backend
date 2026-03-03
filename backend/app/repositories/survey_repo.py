from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import NotFoundError, RepoError
from app.domain.entities.survey import Survey
from app.infrastructure.db.supabase_client import SupabaseClient


class SurveyRepository:
    TABLE = "surveys"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_survey(
        self,
        title: str,
        mode: str,
        input_text: str | None = None,
        model: str = "llama-3.3-70b-versatile",
        n_agents: int = 100,
        seed: int = 42,
        parameters: dict[str, Any] | None = None,
        created_by: str | None = None,
    ) -> Survey:
        data: dict[str, Any] = {
            "id": str(uuid4()),
            "title": title,
            "mode": mode,
            "input_text": input_text,
            "status": "pending",
            "model": model,
            "n_agents": n_agents,
            "seed": seed,
            "parameters": parameters,
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create survey")
        return self._to_entity(result[0])

    def get_survey(self, survey_id: str) -> Survey:
        row = self._db.select_one(self.TABLE, filters={"id": survey_id})
        if not row:
            raise NotFoundError(f"Survey {survey_id} not found")
        return self._to_entity(row)

    def list_surveys(
        self,
        limit: int = 100,
        offset: int = 0,
        created_by: str | None = None,
    ) -> list[Survey]:
        filters = {"created_by": created_by} if created_by else None
        rows = self._db.select(
            self.TABLE,
            filters=filters,
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_desc=True,
        )
        return [self._to_entity(r) for r in rows]

    def update_survey(self, survey_id: str, data: dict[str, Any]) -> Survey:
        result = self._db.update(self.TABLE, data, filters={"id": survey_id})
        if not result:
            raise NotFoundError(f"Survey {survey_id} not found")
        return self._to_entity(result[0])

    def delete_survey(self, survey_id: str) -> None:
        self._db.delete(self.TABLE, filters={"id": survey_id})

    def _to_entity(self, row: dict[str, Any]) -> Survey:
        return Survey(
            id=row["id"],
            title=row["title"],
            mode=row["mode"],
            input_text=row.get("input_text"),
            status=row.get("status", "pending"),
            model=row.get("model", "llama-3.3-70b-versatile"),
            n_agents=row.get("n_agents", 100),
            seed=row.get("seed", 42),
            parameters=row.get("parameters"),
            created_by=row.get("created_by"),
            elapsed_seconds=row.get("elapsed_seconds"),
            started_at=self._parse_dt(row.get("started_at")),
            completed_at=self._parse_dt(row.get("completed_at")),
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
