from typing import Any

from app.domain.entities.experiment import Experiment
from app.repositories.experiment_repo import ExperimentRepository


class ExperimentService:
    def __init__(self, repo: ExperimentRepository):
        self._repo = repo

    def create_experiment(
        self,
        title: str,
        message: str,
        mode: str,
        created_by: str,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> Experiment:
        return self._repo.create_experiment(
            title=title,
            message=message,
            mode=mode,
            created_by=created_by,
            description=description,
            parameters=parameters,
        )

    def get_experiment(self, experiment_id: str) -> Experiment:
        return self._repo.get_experiment(experiment_id)

    def list_experiments(self, limit: int = 100, offset: int = 0) -> list[Experiment]:
        return self._repo.list_experiments(limit=limit, offset=offset)
