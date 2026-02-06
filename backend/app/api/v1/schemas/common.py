from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class HealthResponse(BaseSchema):
    status: str = "ok"


class ErrorDetail(BaseSchema):
    message: str
    status_code: int
    details: Any | None = None


class ErrorResponse(BaseSchema):
    error: ErrorDetail


class PaginationParams(BaseSchema):
    limit: int = 100
    offset: int = 0
