from datetime import datetime
from typing import Any

from pydantic import Field

from app.api.v1.schemas.common import BaseSchema
from app.domain.enums.common import AgentType


class AgentCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    type: AgentType
    traits: dict[str, Any] | None = None


class AgentResponse(BaseSchema):
    id: str
    name: str
    type: AgentType
    traits: dict[str, Any] | None = None
    current_model_id: str | None = None
    created_at: datetime


class AgentAssignModelResponse(BaseSchema):
    agent_id: str
    model_id: str
    message: str = "Model assigned successfully"
