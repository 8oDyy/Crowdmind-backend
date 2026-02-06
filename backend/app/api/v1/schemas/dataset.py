from datetime import datetime
from typing import Any

from pydantic import Field

from app.api.v1.schemas.common import BaseSchema


class DatasetCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    dataset_type: str = Field(..., pattern="^(synthetic|scraped|mixed)$")
    created_by: str = Field(..., min_length=1)
    description: str | None = None


class DatasetResponse(BaseSchema):
    id: str
    name: str
    dataset_type: str
    created_by: str
    description: str | None = None
    created_at: datetime


class DatasetVersionCreate(BaseSchema):
    version: str = Field(..., min_length=1, max_length=50)
    format: str = Field(..., pattern="^(csv|json|parquet|zip)$")


class DatasetVersionResponse(BaseSchema):
    id: str
    dataset_id: str
    version: str
    file_path: str
    format: str
    checksum: str
    size_kb: int
    schema: dict[str, Any] | None = None
    stats: dict[str, Any] | None = None
    created_at: datetime


class DatasetVersionUploadResponse(BaseSchema):
    id: str
    dataset_id: str
    version: str
    file_path: str
    format: str
    checksum: str
    size_kb: int


class GenerateSyntheticRequest(BaseSchema):
    version: str = Field(..., min_length=1, max_length=50)
    n: int = Field(default=100, ge=1, le=10000)
    seed: int | None = None
    labels: list[str] | None = None


class DatasetVersionDownloadResponse(BaseSchema):
    url: str
