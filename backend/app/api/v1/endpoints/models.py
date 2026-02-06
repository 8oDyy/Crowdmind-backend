from typing import Annotated

from fastapi import APIRouter, File, Query, UploadFile

from app.api.v1.schemas.model import (
    ModelCreate,
    ModelResponse,
    ModelVersionCreate,
    ModelVersionDownloadResponse,
    ModelVersionResponse,
    ModelVersionUploadResponse,
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
        framework=body.framework,
        description=body.description,
    )
    return ModelResponse(
        id=model.id,
        name=model.name,
        framework=model.framework,
        description=model.description,
        created_at=model.created_at,
    )


@router.post("/{model_id}/versions", response_model=ModelVersionUploadResponse, status_code=201)
async def create_model_version(
    model_id: str,
    version: str,
    service: ModelServiceDep,
    file: UploadFile = File(...),
) -> ModelVersionUploadResponse:
    content = await file.read()
    content_type = file.content_type or "application/octet-stream"

    model_version = service.create_version(
        model_id=model_id,
        version=version,
        file_bytes=content,
        content_type=content_type,
    )

    return ModelVersionUploadResponse(
        id=model_version.id,
        model_id=model_version.model_id,
        version=model_version.version,
        checksum=model_version.checksum,
        size_kb=model_version.size_kb,
        file_path=model_version.file_path,
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
        framework=model.framework,
        description=model.description,
        created_at=model.created_at,
    )


@router.get("/{model_id}/versions", response_model=list[ModelVersionResponse])
async def list_model_versions(
    model_id: str,
    service: ModelServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ModelVersionResponse]:
    versions = service.list_versions(model_id=model_id, limit=limit, offset=offset)
    return [
        ModelVersionResponse(
            id=v.id,
            model_id=v.model_id,
            version=v.version,
            file_path=v.file_path,
            checksum=v.checksum,
            size_kb=v.size_kb,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.get("/versions/{version_id}/download", response_model=ModelVersionDownloadResponse)
async def get_version_download_url(
    version_id: str,
    service: ModelServiceDep,
    expires: Annotated[int, Query(ge=60, le=86400)] = 3600,
) -> ModelVersionDownloadResponse:
    url = service.get_download_url(version_id=version_id, expires_seconds=expires)
    return ModelVersionDownloadResponse(url=url)


@router.get("", response_model=list[ModelResponse])
async def list_models(
    service: ModelServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ModelResponse]:
    models = service.list_models(limit=limit, offset=offset)
    return [
        ModelResponse(
            id=m.id,
            name=m.name,
            framework=m.framework,
            description=m.description,
            created_at=m.created_at,
        )
        for m in models
    ]
