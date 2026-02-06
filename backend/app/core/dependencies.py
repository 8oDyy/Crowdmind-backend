from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.infrastructure.db.supabase_client import SupabaseClient, get_supabase_client
from app.infrastructure.storage.storage_client import StorageClient
from app.infrastructure.storage.supabase_storage import get_storage_client
from app.repositories.agent_repo import AgentRepository
from app.repositories.dataset_repo import DatasetRepository
from app.repositories.experiment_repo import ExperimentRepository
from app.repositories.model_repo import ModelRepository
from app.repositories.reaction_repo import ReactionRepository
from app.services.agent_service import AgentService
from app.services.dataset_service import DatasetService
from app.services.experiment_service import ExperimentService
from app.services.model_service import ModelService
from app.services.reaction_service import ReactionService
from app.services.realtime_service import RealtimeService

SettingsDep = Annotated[Settings, Depends(get_settings)]
SupabaseDep = Annotated[SupabaseClient, Depends(get_supabase_client)]
StorageDep = Annotated[StorageClient, Depends(get_storage_client)]


def get_dataset_repo(db: SupabaseDep) -> DatasetRepository:
    return DatasetRepository(db)


def get_model_repo(db: SupabaseDep) -> ModelRepository:
    return ModelRepository(db)


def get_agent_repo(db: SupabaseDep) -> AgentRepository:
    return AgentRepository(db)


def get_experiment_repo(db: SupabaseDep) -> ExperimentRepository:
    return ExperimentRepository(db)


def get_reaction_repo(db: SupabaseDep) -> ReactionRepository:
    return ReactionRepository(db)


DatasetRepoDep = Annotated[DatasetRepository, Depends(get_dataset_repo)]
ModelRepoDep = Annotated[ModelRepository, Depends(get_model_repo)]
AgentRepoDep = Annotated[AgentRepository, Depends(get_agent_repo)]
ExperimentRepoDep = Annotated[ExperimentRepository, Depends(get_experiment_repo)]
ReactionRepoDep = Annotated[ReactionRepository, Depends(get_reaction_repo)]


_realtime_service: RealtimeService | None = None


def get_realtime_service() -> RealtimeService:
    global _realtime_service
    if _realtime_service is None:
        _realtime_service = RealtimeService()
    return _realtime_service


RealtimeServiceDep = Annotated[RealtimeService, Depends(get_realtime_service)]


def get_dataset_service(repo: DatasetRepoDep) -> DatasetService:
    return DatasetService(repo)


def get_model_service(
    repo: ModelRepoDep,
    storage: StorageDep,
    settings: SettingsDep,
) -> ModelService:
    return ModelService(repo, storage, settings)


def get_agent_service(repo: AgentRepoDep) -> AgentService:
    return AgentService(repo)


def get_experiment_service(repo: ExperimentRepoDep) -> ExperimentService:
    return ExperimentService(repo)


def get_reaction_service(
    repo: ReactionRepoDep,
    realtime: RealtimeServiceDep,
) -> ReactionService:
    return ReactionService(repo, realtime)


DatasetServiceDep = Annotated[DatasetService, Depends(get_dataset_service)]
ModelServiceDep = Annotated[ModelService, Depends(get_model_service)]
AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]
ExperimentServiceDep = Annotated[ExperimentService, Depends(get_experiment_service)]
ReactionServiceDep = Annotated[ReactionService, Depends(get_reaction_service)]
