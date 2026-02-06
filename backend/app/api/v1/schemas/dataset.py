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


class ArchetypeDefinition(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100, description="Nom de l'archétype")
    description: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Description de l'archétype pour guider la génération",
    )


class GenerateArchetypeRequest(BaseSchema):
    version: str = Field(..., min_length=1, max_length=50)
    archetype_1: ArchetypeDefinition = Field(
        ...,
        description="Premier archétype avec son nom et sa description",
    )
    archetype_2: ArchetypeDefinition = Field(
        ...,
        description="Deuxième archétype avec son nom et sa description",
    )
    n_per_archetype: int = Field(default=5000, ge=100, le=50000)
    seed: int | None = None
    topics: list[str] | None = Field(
        default=None,
        description="Sujets optionnels pour varier les opinions générées",
    )


class DatasetVersionDownloadResponse(BaseSchema):
    url: str
