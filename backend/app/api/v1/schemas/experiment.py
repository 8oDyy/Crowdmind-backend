from datetime import datetime
from typing import Any

from pydantic import Field

from app.api.v1.schemas.common import BaseSchema


class ExperimentCreate(BaseSchema):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    mode: str = Field(..., pattern="^(polling|ab_test|free)$")
    created_by: str = Field(..., min_length=1)
    description: str | None = None
    parameters: dict[str, Any] | None = None


class ExperimentResponse(BaseSchema):
    id: str
    title: str
    message: str
    mode: str
    created_by: str
    description: str | None = None
    parameters: dict[str, Any] | None = None
    created_at: datetime
