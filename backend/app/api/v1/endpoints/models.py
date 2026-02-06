from typing import Annotated

from fastapi import APIRouter, File, Query, UploadFile

from app.api.v1.schemas.model import (
    ModelCreate,
    ModelDownloadResponse,
    ModelResponse,
    ModelUploadResponse,
)
from app.core.dependencies import ModelServiceDep

router = APIRouter(prefix="/models", tags=["models"])


@router.post("", response_model=ModelResponse, status_code=201)
async def create_model(
    body: ModelCreate,
    service: ModelServiceDep,
) -> ModelResponse:
    model = service.create_model(
        name=body.name,
        version=body.version,
        target_device=body.target_device,
        labels=body.labels,
    )
    return ModelResponse(
        id=model.id,
        name=model.name,
        version=model.version,
        target_device=model.target_device,
        labels=model.labels,
        storage_path=model.storage_path,
        checksum=model.checksum,
        size=model.size,
        created_at=model.created_at,
    )


@router.post("/{model_id}/upload", response_model=ModelUploadResponse)
async def upload_model_file(
    model_id: str,
    service: ModelServiceDep,
    file: UploadFile = File(...),
) -> ModelUploadResponse:
    content = await file.read()
    content_type = file.content_type or "application/octet-stream"

    model = service.upload_tflite(
        model_id=model_id,
        file_bytes=content,
        content_type=content_type,
    )

    return ModelUploadResponse(
        model_id=model.id,
        checksum=model.checksum or "",
        size=model.size or 0,
        storage_path=model.storage_path or "",
    )


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    service: ModelServiceDep,
) -> ModelResponse:
    model = service.get_model(model_id)
    return ModelResponse(
        id=model.id,
        name=model.name,
        version=model.version,
        target_device=model.target_device,
        labels=model.labels,
        storage_path=model.storage_path,
        checksum=model.checksum,
        size=model.size,
        created_at=model.created_at,
    )


@router.get("/{model_id}/download", response_model=ModelDownloadResponse)
async def get_download_url(
    model_id: str,
    service: ModelServiceDep,
    expires: Annotated[int, Query(ge=60, le=86400)] = 3600,
) -> ModelDownloadResponse:
    url = service.get_download_url(model_id=model_id, expires_seconds=expires)
    return ModelDownloadResponse(url=url)
