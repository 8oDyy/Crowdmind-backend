from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.errors import NotFoundError, RepoError
from app.domain.entities.agent import Agent
from app.infrastructure.db.supabase_client import SupabaseClient


class AgentRepository:
    TABLE = "agents"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_agent(self, data: dict[str, Any]) -> Agent:
        if "id" not in data:
            data["id"] = str(uuid4())
        if "created_at" not in data:
            data["created_at"] = datetime.now(UTC).isoformat()
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create agent")
        return self._to_entity(result[0])

    def create_agents_batch(self, agents_data: list[dict[str, Any]]) -> list[Agent]:
        for a in agents_data:
            if "id" not in a:
                a["id"] = str(uuid4())
            if "created_at" not in a:
                a["created_at"] = datetime.now(UTC).isoformat()
        result = self._db.insert(self.TABLE, agents_data)
        if not result:
            raise RepoError("Failed to create agents batch")
        return [self._to_entity(r) for r in result]

    def get_agent(self, agent_id: str) -> Agent:
        row = self._db.select_one(self.TABLE, filters={"id": agent_id})
        if not row:
            raise NotFoundError(f"Agent {agent_id} not found")
        return self._to_entity(row)

    def list_agents_by_survey(
        self,
        survey_id: str,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[Agent]:
        rows = self._db.select(
            self.TABLE,
            filters={"survey_id": survey_id},
            limit=limit,
            offset=offset,
            order_by="agent_index",
        )
        return [self._to_entity(r) for r in rows]

    def delete_agents_by_survey(self, survey_id: str) -> None:
        self._db.delete(self.TABLE, filters={"survey_id": survey_id})

    def _to_entity(self, row: dict[str, Any]) -> Agent:
        return Agent(
            id=row["id"],
            survey_id=row["survey_id"],
            agent_index=row["agent_index"],
            eco=float(row["eco"]),
            open=float(row["open"]),
            trust=float(row["trust"]),
            temperament=float(row["temperament"]),
            age=int(row["age"]),
            education=row["education"],
            urban_rural=row["urban_rural"],
            classe_sociale=row["classe_sociale"],
            background=row["background"],
            created_at=self._parse_dt(row.get("created_at")) or datetime.now(UTC),
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
