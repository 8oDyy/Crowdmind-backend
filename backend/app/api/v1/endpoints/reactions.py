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
    reaction = await service.create_reaction(
        experiment_id=body.experiment_id,
        agent_id=body.agent_id,
        payload=body.payload,
    )
    return ReactionResponse(
        id=reaction.id,
        experiment_id=reaction.experiment_id,
        agent_id=reaction.agent_id,
        payload=reaction.payload,
        created_at=reaction.created_at,
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
                payload=r.payload,
                created_at=r.created_at,
            )
            for r in reactions
        ],
        count=len(reactions),
    )
