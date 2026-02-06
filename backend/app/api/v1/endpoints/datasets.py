from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.v1.schemas.dataset import (
    DatasetCreate,
    DatasetResponse,
    GenerateRowsResponse,
)
from app.core.dependencies import DatasetServiceDep
from app.domain.enums.common import ExportFormat

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    body: DatasetCreate,
    service: DatasetServiceDep,
) -> DatasetResponse:
    dataset = service.create_dataset(
        name=body.name,
        version=body.version,
        labels=body.labels,
        schema_def=body.schema_def,
    )
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        version=dataset.version,
        schema_def=dataset.schema_def,
        labels=dataset.labels,
        created_at=dataset.created_at,
    )


@router.post("/{dataset_id}/generate", response_model=GenerateRowsResponse)
async def generate_rows(
    dataset_id: str,
    service: DatasetServiceDep,
    n: Annotated[int, Query(ge=1, le=10000)] = 100,
    seed: int | None = None,
) -> GenerateRowsResponse:
    inserted = service.generate_rows(dataset_id=dataset_id, n=n, seed=seed)
    return GenerateRowsResponse(inserted=inserted)


@router.get("/{dataset_id}/export")
async def export_dataset(
    dataset_id: str,
    service: DatasetServiceDep,
    format: ExportFormat = ExportFormat.JSONL,
) -> StreamingResponse:
    generator = service.export_dataset(dataset_id=dataset_id, format=format)

    if format == ExportFormat.JSONL:
        media_type = "application/x-ndjson"
        filename = f"dataset_{dataset_id}.jsonl"
    else:
        media_type = "text/csv"
        filename = f"dataset_{dataset_id}.csv"

    return StreamingResponse(
        generator,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    service: DatasetServiceDep,
) -> DatasetResponse:
    dataset = service.get_dataset(dataset_id)
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        version=dataset.version,
        schema_def=dataset.schema_def,
        labels=dataset.labels,
        created_at=dataset.created_at,
    )
