from datetime import datetime
from typing import Any

from pydantic import Field

from app.api.v1.schemas.common import BaseSchema


class ReactionCreate(BaseSchema):
    experiment_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    reaction: str = Field(..., pattern="^(accept|reject|doubt)$")
    emotion: str = Field(..., pattern="^(joy|anger|fear|neutral)$")
    score: float | None = None
    raw_data: dict[str, Any] | None = None


class ReactionResponse(BaseSchema):
    id: str
    experiment_id: str
    agent_id: str
    reaction: str
    emotion: str
    score: float | None = None
    raw_data: dict[str, Any] | None = None
    created_at: datetime


class ReactionListResponse(BaseSchema):
    reactions: list[ReactionResponse]
    count: int
