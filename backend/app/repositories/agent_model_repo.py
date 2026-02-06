from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import RepoError
from app.domain.entities.agent_model import AgentModel
from app.infrastructure.db.supabase_client import SupabaseClient


class AgentModelRepository:
    TABLE = "agent_models"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def assign_model(
        self,
        agent_id: str,
        model_version_id: str,
    ) -> AgentModel:
        data = {
            "id": str(uuid4()),
            "agent_id": agent_id,
            "model_version_id": model_version_id,
            "assigned_at": datetime.utcnow().isoformat(),
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to assign model to agent")
        return self._to_agent_model(result[0])

    def get_current_model(self, agent_id: str) -> AgentModel | None:
        rows = self._db.select(
            self.TABLE,
            filters={"agent_id": agent_id},
            limit=1,
            order_by="assigned_at",
            order_desc=True,
        )
        return self._to_agent_model(rows[0]) if rows else None

    def list_agent_models(
        self,
        agent_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentModel]:
        rows = self._db.select(
            self.TABLE,
            filters={"agent_id": agent_id},
            limit=limit,
            offset=offset,
            order_by="assigned_at",
            order_desc=True,
        )
        return [self._to_agent_model(r) for r in rows]

    def _to_agent_model(self, row: dict[str, Any]) -> AgentModel:
        return AgentModel(
            id=row["id"],
            agent_id=row["agent_id"],
            model_version_id=row["model_version_id"],
            assigned_at=self._parse_datetime(row.get("assigned_at")),
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()
