from typing import Annotated

from fastapi import APIRouter, Query

from app.api.v1.schemas.experiment import (
    ExperimentCreate,
    ExperimentResponse,
)
from app.core.dependencies import ExperimentServiceDep

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentResponse, status_code=201)
async def create_experiment(
    body: ExperimentCreate,
    service: ExperimentServiceDep,
) -> ExperimentResponse:
    experiment = service.create_experiment(
        title=body.title,
        message=body.message,
        mode=body.mode,
        created_by=body.created_by,
        description=body.description,
        parameters=body.parameters,
    )
    return ExperimentResponse(
        id=experiment.id,
        title=experiment.title,
        message=experiment.message,
        mode=experiment.mode,
        created_by=experiment.created_by,
        description=experiment.description,
        parameters=experiment.parameters,
        created_at=experiment.created_at,
    )


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: str,
    service: ExperimentServiceDep,
) -> ExperimentResponse:
    experiment = service.get_experiment(experiment_id)
    return ExperimentResponse(
        id=experiment.id,
        title=experiment.title,
        message=experiment.message,
        mode=experiment.mode,
        created_by=experiment.created_by,
        description=experiment.description,
        parameters=experiment.parameters,
        created_at=experiment.created_at,
    )


@router.get("", response_model=list[ExperimentResponse])
async def list_experiments(
    service: ExperimentServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ExperimentResponse]:
    experiments = service.list_experiments(limit=limit, offset=offset)
    return [
        ExperimentResponse(
            id=e.id,
            title=e.title,
            message=e.message,
            mode=e.mode,
            created_by=e.created_by,
            description=e.description,
            parameters=e.parameters,
            created_at=e.created_at,
        )
        for e in experiments
    ]
