from datetime import datetime
from typing import Any

from pydantic import Field

from app.api.v1.schemas.common import BaseSchema


class ReactionCreate(BaseSchema):
    experiment_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    payload: dict[str, Any]


class ReactionResponse(BaseSchema):
    id: str
    experiment_id: str
    agent_id: str
    payload: dict[str, Any]
    created_at: datetime


class ReactionListResponse(BaseSchema):
    reactions: list[ReactionResponse]
    count: int
