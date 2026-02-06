from fastapi import APIRouter

from app.api.v1.schemas.experiment import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentStatusResponse,
)
from app.core.dependencies import ExperimentServiceDep

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentResponse, status_code=201)
async def create_experiment(
    body: ExperimentCreate,
    service: ExperimentServiceDep,
) -> ExperimentResponse:
    experiment = service.create_experiment(
        name=body.name,
        scenario=body.scenario,
    )
    return ExperimentResponse(
        id=experiment.id,
        name=experiment.name,
        status=experiment.status,
        scenario=experiment.scenario,
        started_at=experiment.started_at,
        ended_at=experiment.ended_at,
        created_at=experiment.created_at,
    )


@router.post("/{experiment_id}/start", response_model=ExperimentStatusResponse)
async def start_experiment(
    experiment_id: str,
    service: ExperimentServiceDep,
) -> ExperimentStatusResponse:
    experiment = service.start_experiment(experiment_id)
    return ExperimentStatusResponse(
        id=experiment.id,
        status=experiment.status,
        message="Experiment started",
    )


@router.post("/{experiment_id}/stop", response_model=ExperimentStatusResponse)
async def stop_experiment(
    experiment_id: str,
    service: ExperimentServiceDep,
) -> ExperimentStatusResponse:
    experiment = service.stop_experiment(experiment_id)
    return ExperimentStatusResponse(
        id=experiment.id,
        status=experiment.status,
        message="Experiment stopped",
    )


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: str,
    service: ExperimentServiceDep,
) -> ExperimentResponse:
    experiment = service.get_experiment(experiment_id)
    return ExperimentResponse(
        id=experiment.id,
        name=experiment.name,
        status=experiment.status,
        scenario=experiment.scenario,
        started_at=experiment.started_at,
        ended_at=experiment.ended_at,
        created_at=experiment.created_at,
    )
