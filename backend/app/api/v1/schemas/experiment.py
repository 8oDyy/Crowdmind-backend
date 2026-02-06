from datetime import datetime
from typing import Any

from pydantic import Field

from app.api.v1.schemas.common import BaseSchema
from app.domain.enums.common import ExperimentStatus


class ExperimentCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    scenario: dict[str, Any] | None = None


class ExperimentResponse(BaseSchema):
    id: str
    name: str
    status: ExperimentStatus
    scenario: dict[str, Any] | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime


class ExperimentStatusResponse(BaseSchema):
    id: str
    status: ExperimentStatus
    message: str
