from typing import Any

from app.core.errors import RepoError
from app.domain.entities.experiment_agent import ExperimentAgent
from app.infrastructure.db.supabase_client import SupabaseClient


class ExperimentAgentRepository:
    TABLE = "experiment_agents"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def add_agent_to_experiment(
        self,
        experiment_id: str,
        agent_id: str,
        model_version_id: str,
    ) -> ExperimentAgent:
        data = {
            "experiment_id": experiment_id,
            "agent_id": agent_id,
            "model_version_id": model_version_id,
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to add agent to experiment")
        return self._to_experiment_agent(result[0])

    def list_experiment_agents(
        self,
        experiment_id: str,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[ExperimentAgent]:
        rows = self._db.select(
            self.TABLE,
            filters={"experiment_id": experiment_id},
            limit=limit,
            offset=offset,
        )
        return [self._to_experiment_agent(r) for r in rows]

    def remove_agent_from_experiment(
        self,
        experiment_id: str,
        agent_id: str,
    ) -> None:
        self._db.delete(
            self.TABLE,
            filters={"experiment_id": experiment_id, "agent_id": agent_id},
        )

    def _to_experiment_agent(self, row: dict[str, Any]) -> ExperimentAgent:
        return ExperimentAgent(
            experiment_id=row["experiment_id"],
            agent_id=row["agent_id"],
            model_version_id=row["model_version_id"],
        )
