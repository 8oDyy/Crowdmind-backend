from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.infrastructure.db.supabase_client import SupabaseClient, get_supabase_client
from app.repositories.agent_repo import AgentRepository
from app.repositories.response_repo import ResponseRepository
from app.repositories.survey_aggregate_repo import SurveyAggregateRepository
from app.repositories.survey_question_repo import SurveyQuestionRepository
from app.repositories.survey_question_response_repo import SurveyQuestionResponseRepository
from app.repositories.survey_repo import SurveyRepository
from app.services.realtime_service import RealtimeService
from app.services.survey_service import SurveyService

SettingsDep = Annotated[Settings, Depends(get_settings)]
SupabaseDep = Annotated[SupabaseClient, Depends(get_supabase_client)]


# ── Repositories ─────────────────────────────────────────

def get_survey_repo(db: SupabaseDep) -> SurveyRepository:
    return SurveyRepository(db)


def get_agent_repo(db: SupabaseDep) -> AgentRepository:
    return AgentRepository(db)


def get_response_repo(db: SupabaseDep) -> ResponseRepository:
    return ResponseRepository(db)


def get_survey_aggregate_repo(db: SupabaseDep) -> SurveyAggregateRepository:
    return SurveyAggregateRepository(db)


def get_survey_question_repo(db: SupabaseDep) -> SurveyQuestionRepository:
    return SurveyQuestionRepository(db)


def get_survey_question_response_repo(db: SupabaseDep) -> SurveyQuestionResponseRepository:
    return SurveyQuestionResponseRepository(db)


SurveyRepoDep = Annotated[SurveyRepository, Depends(get_survey_repo)]
AgentRepoDep = Annotated[AgentRepository, Depends(get_agent_repo)]
ResponseRepoDep = Annotated[ResponseRepository, Depends(get_response_repo)]
AggregateRepoDep = Annotated[SurveyAggregateRepository, Depends(get_survey_aggregate_repo)]
QuestionRepoDep = Annotated[SurveyQuestionRepository, Depends(get_survey_question_repo)]
QuestionResponseRepoDep = Annotated[SurveyQuestionResponseRepository, Depends(get_survey_question_response_repo)]


# ── Realtime ─────────────────────────────────────────────

_realtime_service: RealtimeService | None = None


def get_realtime_service() -> RealtimeService:
    global _realtime_service
    if _realtime_service is None:
        _realtime_service = RealtimeService()
    return _realtime_service


RealtimeServiceDep = Annotated[RealtimeService, Depends(get_realtime_service)]


# ── Services ─────────────────────────────────────────────

def get_survey_service(
    survey_repo: SurveyRepoDep,
    agent_repo: AgentRepoDep,
    response_repo: ResponseRepoDep,
    aggregate_repo: AggregateRepoDep,
    question_repo: QuestionRepoDep,
    question_response_repo: QuestionResponseRepoDep,
) -> SurveyService:
    return SurveyService(
        survey_repo=survey_repo,
        agent_repo=agent_repo,
        response_repo=response_repo,
        aggregate_repo=aggregate_repo,
        question_repo=question_repo,
        question_response_repo=question_response_repo,
    )


SurveyServiceDep = Annotated[SurveyService, Depends(get_survey_service)]
