from typing import Annotated

from fastapi import APIRouter, Query

from app.api.v1.schemas.reaction import (
    ReactionCreate,
    ReactionListResponse,
    ReactionResponse,
)
from app.core.dependencies import ReactionServiceDep

router = APIRouter(tags=["reactions"])


@router.post("/reactions", response_model=ReactionResponse, status_code=201)
async def create_reaction(
    body: ReactionCreate,
    service: ReactionServiceDep,
) -> ReactionResponse:
    agent_reaction = await service.create_reaction(
        experiment_id=body.experiment_id,
        agent_id=body.agent_id,
        reaction=body.reaction,
        emotion=body.emotion,
        score=body.score,
        raw_data=body.raw_data,
    )
    return ReactionResponse(
        id=agent_reaction.id,
        experiment_id=agent_reaction.experiment_id,
        agent_id=agent_reaction.agent_id,
        reaction=agent_reaction.reaction,
        emotion=agent_reaction.emotion,
        score=agent_reaction.score,
        raw_data=agent_reaction.raw_data,
        created_at=agent_reaction.created_at,
    )


@router.get("/experiments/{experiment_id}/reactions", response_model=ReactionListResponse)
async def list_reactions(
    experiment_id: str,
    service: ReactionServiceDep,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ReactionListResponse:
    reactions = service.list_reactions(
        experiment_id=experiment_id,
        limit=limit,
        offset=offset,
    )
    return ReactionListResponse(
        reactions=[
            ReactionResponse(
                id=r.id,
                experiment_id=r.experiment_id,
                agent_id=r.agent_id,
                reaction=r.reaction,
                emotion=r.emotion,
                score=r.score,
                raw_data=r.raw_data,
                created_at=r.created_at,
            )
            for r in reactions
        ],
        count=len(reactions),
    )
