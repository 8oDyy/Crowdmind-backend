from datetime import datetime
from typing import Any

from pydantic import Field

from app.api.v1.schemas.common import BaseSchema


class AgentCreate(BaseSchema):
    label: str = Field(..., min_length=1, max_length=255)
    demographics: dict[str, Any] | None = None
    traits: dict[str, Any] | None = None


class AgentResponse(BaseSchema):
    id: str
    label: str
    demographics: dict[str, Any] | None = None
    traits: dict[str, Any] | None = None
    created_at: datetime
