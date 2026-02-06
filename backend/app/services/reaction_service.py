from typing import Any

from app.domain.entities.reaction import Reaction
from app.repositories.reaction_repo import ReactionRepository
from app.services.realtime_service import RealtimeService


class ReactionService:
    def __init__(self, repo: ReactionRepository, realtime: RealtimeService):
        self._repo = repo
        self._realtime = realtime

    async def create_reaction(
        self,
        experiment_id: str,
        agent_id: str,
        payload: dict[str, Any],
    ) -> Reaction:
        reaction = self._repo.create_reaction(
            experiment_id=experiment_id,
            agent_id=agent_id,
            payload=payload,
        )
        await self._realtime.broadcast(
            experiment_id=experiment_id,
            event_type="reaction_created",
            data={
                "id": reaction.id,
                "experiment_id": reaction.experiment_id,
                "agent_id": reaction.agent_id,
                "payload": reaction.payload,
                "created_at": reaction.created_at.isoformat(),
            },
        )
        return reaction

    def list_reactions(
        self,
        experiment_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Reaction]:
        return self._repo.list_reactions(
            experiment_id=experiment_id,
            limit=limit,
            offset=offset,
        )
