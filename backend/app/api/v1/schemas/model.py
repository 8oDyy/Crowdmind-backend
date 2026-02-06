from datetime import datetime

from pydantic import Field

from app.api.v1.schemas.common import BaseSchema


class ModelCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    framework: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class ModelResponse(BaseSchema):
    id: str
    name: str
    framework: str
    description: str | None = None
    created_at: datetime


class ModelVersionCreate(BaseSchema):
    version: str = Field(..., min_length=1, max_length=50)


class ModelVersionResponse(BaseSchema):
    id: str
    model_id: str
    version: str
    file_path: str
    checksum: str
    size_kb: int
    created_at: datetime


class ModelVersionUploadResponse(BaseSchema):
    id: str
    model_id: str
    version: str
    checksum: str
    size_kb: int
    file_path: str


class ModelVersionDownloadResponse(BaseSchema):
    url: str
