from typing import Any

from app.domain.entities.reaction import AgentReaction
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
        reaction: str,
        emotion: str,
        score: float | None = None,
        raw_data: dict[str, Any] | None = None,
    ) -> AgentReaction:
        agent_reaction = self._repo.create_reaction(
            experiment_id=experiment_id,
            agent_id=agent_id,
            reaction=reaction,
            emotion=emotion,
            score=score,
            raw_data=raw_data,
        )
        await self._realtime.broadcast(
            experiment_id=experiment_id,
            event_type="reaction_created",
            data={
                "id": agent_reaction.id,
                "experiment_id": agent_reaction.experiment_id,
                "agent_id": agent_reaction.agent_id,
                "reaction": agent_reaction.reaction,
                "emotion": agent_reaction.emotion,
                "score": agent_reaction.score,
                "raw_data": agent_reaction.raw_data,
                "created_at": agent_reaction.created_at.isoformat(),
            },
        )
        return agent_reaction

    def list_reactions(
        self,
        experiment_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentReaction]:
        return self._repo.list_reactions(
            experiment_id=experiment_id,
            limit=limit,
            offset=offset,
        )
