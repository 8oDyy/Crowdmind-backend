from typing import Any

from app.core.errors import ValidationError
from app.domain.entities.experiment import Experiment
from app.domain.enums.common import ExperimentStatus
from app.repositories.experiment_repo import ExperimentRepository


class ExperimentService:
    def __init__(self, repo: ExperimentRepository):
        self._repo = repo

    def create_experiment(
        self,
        name: str,
        scenario: dict[str, Any] | None = None,
    ) -> Experiment:
        return self._repo.create_experiment(name=name, scenario=scenario)

    def get_experiment(self, experiment_id: str) -> Experiment:
        return self._repo.get_experiment(experiment_id)

    def start_experiment(self, experiment_id: str) -> Experiment:
        experiment = self._repo.get_experiment(experiment_id)
        if experiment.status == ExperimentStatus.RUNNING:
            raise ValidationError("Experiment is already running")
        return self._repo.set_status(experiment_id, ExperimentStatus.RUNNING)

    def stop_experiment(self, experiment_id: str) -> Experiment:
        experiment = self._repo.get_experiment(experiment_id)
        if experiment.status == ExperimentStatus.STOPPED:
            raise ValidationError("Experiment is already stopped")
        return self._repo.set_status(experiment_id, ExperimentStatus.STOPPED)

    def list_experiments(self, limit: int = 100, offset: int = 0) -> list[Experiment]:
        return self._repo.list_experiments(limit=limit, offset=offset)
