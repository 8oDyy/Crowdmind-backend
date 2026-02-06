from datetime import datetime
from typing import Any

from pydantic import Field

from app.api.v1.schemas.common import BaseSchema


class DatasetCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(default="1.0", max_length=50)
    labels: list[str] | None = None
    schema_def: dict[str, Any] | None = Field(default=None, alias="schema")


class DatasetResponse(BaseSchema):
    id: str
    name: str
    version: str
    schema_def: dict[str, Any] | None = Field(default=None, serialization_alias="schema")
    labels: list[str] | None = None
    created_at: datetime


class GenerateRowsResponse(BaseSchema):
    inserted: int


class DatasetRowResponse(BaseSchema):
    id: str
    dataset_id: str
    input_data: dict[str, Any]
    label: str
    meta: dict[str, Any] | None = None
    created_at: datetime
