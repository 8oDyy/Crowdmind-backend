from datetime import datetime

from pydantic import Field

from app.api.v1.schemas.common import BaseSchema


class ModelCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(..., min_length=1, max_length=50)
    target_device: str | None = None
    labels: list[str] | None = None


class ModelResponse(BaseSchema):
    id: str
    name: str
    version: str
    target_device: str | None = None
    labels: list[str] | None = None
    storage_path: str | None = None
    checksum: str | None = None
    size: int | None = None
    created_at: datetime


class ModelUploadResponse(BaseSchema):
    model_id: str
    checksum: str
    size: int
    storage_path: str


class ModelDownloadResponse(BaseSchema):
    url: str
