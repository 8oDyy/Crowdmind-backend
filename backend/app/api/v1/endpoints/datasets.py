from typing import Annotated

from fastapi import APIRouter, File, Query, UploadFile

from app.api.v1.schemas.dataset import (
    DatasetCreate,
    DatasetResponse,
    DatasetVersionDownloadResponse,
    DatasetVersionResponse,
    DatasetVersionUploadResponse,
    GenerateArchetypeRequest,
)
from app.core.dependencies import DatasetServiceDep

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    body: DatasetCreate,
    service: DatasetServiceDep,
) -> DatasetResponse:
    dataset = service.create_dataset(
        name=body.name,
        dataset_type=body.dataset_type,
        created_by=body.created_by,
        description=body.description,
    )
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        dataset_type=dataset.dataset_type,
        created_by=dataset.created_by,
        description=dataset.description,
        created_at=dataset.created_at,
    )


@router.get("", response_model=list[DatasetResponse])
async def list_datasets(
    service: DatasetServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DatasetResponse]:
    datasets = service.list_datasets(limit=limit, offset=offset)
    return [
        DatasetResponse(
            id=d.id,
            name=d.name,
            dataset_type=d.dataset_type,
            created_by=d.created_by,
            description=d.description,
            created_at=d.created_at,
        )
        for d in datasets
    ]


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    service: DatasetServiceDep,
) -> DatasetResponse:
    dataset = service.get_dataset(dataset_id)
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        dataset_type=dataset.dataset_type,
        created_by=dataset.created_by,
        description=dataset.description,
        created_at=dataset.created_at,
    )


@router.post("/{dataset_id}/versions", response_model=DatasetVersionUploadResponse, status_code=201)
async def create_dataset_version(
    dataset_id: str,
    version: str,
    format: str,
    service: DatasetServiceDep,
    file: UploadFile = File(...),
) -> DatasetVersionUploadResponse:
    content = await file.read()
    content_type = file.content_type or "application/octet-stream"

    dataset_version = service.create_version(
        dataset_id=dataset_id,
        version=version,
        file_bytes=content,
        format=format,
        content_type=content_type,
    )

    return DatasetVersionUploadResponse(
        id=dataset_version.id,
        dataset_id=dataset_version.dataset_id,
        version=dataset_version.version,
        file_path=dataset_version.file_path,
        format=dataset_version.format,
        checksum=dataset_version.checksum,
        size_kb=dataset_version.size_kb,
    )


@router.post("/{dataset_id}/generate", response_model=DatasetVersionResponse, status_code=201)
async def generate_archetype_dataset(
    dataset_id: str,
    body: GenerateArchetypeRequest,
    service: DatasetServiceDep,
) -> DatasetVersionResponse:
    """Génère un dataset d'entraînement pour les 2 archétypes spécifiés."""
    version = service.generate_archetype_dataset(
        dataset_id=dataset_id,
        version=body.version,
        archetype_1_name=body.archetype_1.name,
        archetype_1_description=body.archetype_1.description,
        archetype_2_name=body.archetype_2.name,
        archetype_2_description=body.archetype_2.description,
        n_per_archetype=body.n_per_archetype,
        seed=body.seed,
        topics=body.topics,
    )
    return DatasetVersionResponse(
        id=version.id,
        dataset_id=version.dataset_id,
        version=version.version,
        file_path=version.file_path,
        format=version.format,
        checksum=version.checksum,
        size_kb=version.size_kb,
        schema=version.schema,
        stats=version.stats,
        created_at=version.created_at,
    )


@router.get("/{dataset_id}/versions", response_model=list[DatasetVersionResponse])
async def list_dataset_versions(
    dataset_id: str,
    service: DatasetServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DatasetVersionResponse]:
    versions = service.list_versions(dataset_id=dataset_id, limit=limit, offset=offset)
    return [
        DatasetVersionResponse(
            id=v.id,
            dataset_id=v.dataset_id,
            version=v.version,
            file_path=v.file_path,
            format=v.format,
            checksum=v.checksum,
            size_kb=v.size_kb,
            schema=v.schema,
            stats=v.stats,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.get("/versions/{version_id}/download", response_model=DatasetVersionDownloadResponse)
async def get_version_download_url(
    version_id: str,
    service: DatasetServiceDep,
    expires: Annotated[int, Query(ge=60, le=86400)] = 3600,
) -> DatasetVersionDownloadResponse:
    url = service.get_download_url(version_id=version_id, expires_seconds=expires)
    return DatasetVersionDownloadResponse(url=url)
