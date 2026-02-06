from typing import Any

from app.domain.entities.agent import Agent
from app.repositories.agent_repo import AgentRepository


class AgentService:
    def __init__(self, repo: AgentRepository):
        self._repo = repo

    def create_agent(
        self,
        label: str,
        demographics: dict[str, Any] | None = None,
        traits: dict[str, Any] | None = None,
    ) -> Agent:
        return self._repo.create_agent(
            label=label,
            demographics=demographics,
            traits=traits,
        )

    def get_agent(self, agent_id: str) -> Agent:
        return self._repo.get_agent(agent_id)

    def list_agents(self, limit: int = 100, offset: int = 0) -> list[Agent]:
        return self._repo.list_agents(limit=limit, offset=offset)
