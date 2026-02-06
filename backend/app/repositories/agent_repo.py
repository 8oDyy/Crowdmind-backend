from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import NotFoundError, RepoError
from app.domain.entities.agent import Agent
from app.domain.enums.common import AgentType
from app.infrastructure.db.supabase_client import SupabaseClient


class AgentRepository:
    TABLE = "agents"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_agent(
        self,
        name: str,
        agent_type: AgentType,
        traits: dict[str, Any] | None = None,
    ) -> Agent:
        data = {
            "id": str(uuid4()),
            "name": name,
            "type": agent_type.value,
            "traits": traits,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create agent")
        return self._to_agent(result[0])

    def get_agent(self, agent_id: str) -> Agent:
        row = self._db.select_one(self.TABLE, filters={"id": agent_id})
        if not row:
            raise NotFoundError(f"Agent {agent_id} not found")
        return self._to_agent(row)

    def assign_model(self, agent_id: str, model_id: str) -> Agent:
        result = self._db.update(
            self.TABLE,
            data={"current_model_id": model_id},
            filters={"id": agent_id},
        )
        if not result:
            raise NotFoundError(f"Agent {agent_id} not found")
        return self._to_agent(result[0])

    def list_agents(self, limit: int = 100, offset: int = 0) -> list[Agent]:
        rows = self._db.select(
            self.TABLE,
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_desc=True,
        )
        return [self._to_agent(r) for r in rows]

    def _to_agent(self, row: dict[str, Any]) -> Agent:
        return Agent(
            id=row["id"],
            name=row["name"],
            type=AgentType(row["type"]),
            traits=row.get("traits"),
            current_model_id=row.get("current_model_id"),
            created_at=self._parse_datetime(row.get("created_at")),
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()
