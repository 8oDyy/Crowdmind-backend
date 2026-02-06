from fastapi import APIRouter

from app.api.v1.schemas.agent import (
    AgentAssignModelResponse,
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
        name=body.name,
        agent_type=body.type,
        traits=body.traits,
    )
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        type=agent.type,
        traits=agent.traits,
        current_model_id=agent.current_model_id,
        created_at=agent.created_at,
    )


@router.post("/{agent_id}/assign-model/{model_id}", response_model=AgentAssignModelResponse)
async def assign_model_to_agent(
    agent_id: str,
    model_id: str,
    service: AgentServiceDep,
) -> AgentAssignModelResponse:
    agent = service.assign_model(agent_id=agent_id, model_id=model_id)
    return AgentAssignModelResponse(
        agent_id=agent.id,
        model_id=model_id,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    service: AgentServiceDep,
) -> AgentResponse:
    agent = service.get_agent(agent_id)
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        type=agent.type,
        traits=agent.traits,
        current_model_id=agent.current_model_id,
        created_at=agent.created_at,
    )
