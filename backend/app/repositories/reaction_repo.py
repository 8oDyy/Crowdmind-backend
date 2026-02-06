from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import RepoError
from app.domain.entities.reaction import Reaction
from app.infrastructure.db.supabase_client import SupabaseClient


class ReactionRepository:
    TABLE = "reactions"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_reaction(
        self,
        experiment_id: str,
        agent_id: str,
        payload: dict[str, Any],
    ) -> Reaction:
        data = {
            "id": str(uuid4()),
            "experiment_id": experiment_id,
            "agent_id": agent_id,
            "payload": payload,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create reaction")
        return self._to_reaction(result[0])

    def list_reactions(
        self,
        experiment_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Reaction]:
        rows = self._db.select(
            self.TABLE,
            filters={"experiment_id": experiment_id},
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_desc=True,
        )
        return [self._to_reaction(r) for r in rows]

    def _to_reaction(self, row: dict[str, Any]) -> Reaction:
        return Reaction(
            id=row["id"],
            experiment_id=row["experiment_id"],
            agent_id=row["agent_id"],
            payload=row.get("payload", {}),
            created_at=self._parse_datetime(row.get("created_at")),
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()
