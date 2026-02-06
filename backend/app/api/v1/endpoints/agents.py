from typing import Annotated

from fastapi import APIRouter, Query

from app.api.v1.schemas.agent import (
    AgentCreate,
    AgentResponse,
)
from app.core.dependencies import AgentServiceDep

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    body: AgentCreate,
    service: AgentServiceDep,
) -> AgentResponse:
    agent = service.create_agent(
        label=body.label,
        demographics=body.demographics,
        traits=body.traits,
    )
    return AgentResponse(
        id=agent.id,
        label=agent.label,
        demographics=agent.demographics,
        traits=agent.traits,
        created_at=agent.created_at,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    service: AgentServiceDep,
) -> AgentResponse:
    agent = service.get_agent(agent_id)
    return AgentResponse(
        id=agent.id,
        label=agent.label,
        demographics=agent.demographics,
        traits=agent.traits,
        created_at=agent.created_at,
    )


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    service: AgentServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AgentResponse]:
    agents = service.list_agents(limit=limit, offset=offset)
    return [
        AgentResponse(
            id=a.id,
            label=a.label,
            demographics=a.demographics,
            traits=a.traits,
            created_at=a.created_at,
        )
        for a in agents
    ]
