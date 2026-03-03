from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.schemas.agent import AgentListResponse, AgentResponse
from app.api.v1.schemas.response import (
    AggregateListResponse,
    AggregateOut,
    QuestionResponseListResponse,
    QuestionResponseOut,
    ResponseListResponse,
    ResponseOut,
)
from app.api.v1.schemas.survey import (
    SurveyCreate,
    SurveyListResponse,
    SurveyQuestionResponse,
    SurveyResponse,
)
from app.core.dependencies import SurveyServiceDep

router = APIRouter(prefix="/surveys", tags=["Surveys"])


@router.post("", response_model=SurveyResponse, status_code=201)
def create_survey(body: SurveyCreate, svc: SurveyServiceDep):
    questions_data = None
    if body.questions:
        questions_data = [q.model_dump() for q in body.questions]
    survey = svc.create_survey(
        title=body.title,
        mode=body.mode,
        input_text=body.input_text,
        model=body.model,
        n_agents=body.n_agents,
        seed=body.seed,
        parameters=body.parameters,
        questions=questions_data,
    )
    return _survey_to_response(survey)


@router.get("", response_model=SurveyListResponse)
def list_surveys(
    svc: SurveyServiceDep,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    surveys = svc.list_surveys(limit=limit, offset=offset)
    return SurveyListResponse(
        surveys=[_survey_to_response(s) for s in surveys],
        count=len(surveys),
    )


@router.get("/{survey_id}", response_model=SurveyResponse)
def get_survey(survey_id: str, svc: SurveyServiceDep):
    survey = svc.get_survey(survey_id)
    return _survey_to_response(survey)


@router.delete("/{survey_id}", status_code=204)
def delete_survey(survey_id: str, svc: SurveyServiceDep):
    svc.delete_survey(survey_id)


# ── Agents ───────────────────────────────────────────────

@router.get("/{survey_id}/agents", response_model=AgentListResponse)
def get_survey_agents(survey_id: str, svc: SurveyServiceDep):
    agents = svc.get_agents(survey_id)
    items = [
        AgentResponse(
            id=a.id,
            survey_id=a.survey_id,
            agent_index=a.agent_index,
            eco=a.eco,
            open=a.open,
            trust=a.trust,
            temperament=a.temperament,
            age=a.age,
            education=a.education,
            urban_rural=a.urban_rural,
            classe_sociale=a.classe_sociale,
            background=a.background,
            created_at=a.created_at,
        )
        for a in agents
    ]
    return AgentListResponse(agents=items, count=len(items))


# ── Questions ────────────────────────────────────────────

@router.get("/{survey_id}/questions", response_model=list[SurveyQuestionResponse])
def get_survey_questions(survey_id: str, svc: SurveyServiceDep):
    questions = svc.get_questions(survey_id)
    return [
        SurveyQuestionResponse(
            id=q.id,
            survey_id=q.survey_id,
            question_index=q.question_index,
            question_id=q.question_id,
            type=q.type,
            text=q.text,
            choices=q.choices,
            scale=q.scale,
        )
        for q in questions
    ]


# ── Responses (mode text) ───────────────────────────────

@router.get("/{survey_id}/responses", response_model=ResponseListResponse)
def get_survey_responses(
    survey_id: str,
    svc: SurveyServiceDep,
    limit: int = Query(default=1000, ge=1),
    offset: int = Query(default=0, ge=0),
):
    responses = svc.get_responses(survey_id)
    items = [
        ResponseOut(
            id=r.id,
            survey_id=r.survey_id,
            agent_id=r.agent_id,
            stance=r.stance,
            confidence=r.confidence,
            short_reason=r.short_reason,
            raw_llm_output=r.raw_llm_output,
            is_fallback=r.is_fallback,
            created_at=r.created_at,
        )
        for r in responses
    ]
    return ResponseListResponse(responses=items, count=len(items))


# ── Question responses (mode questionnaire) ──────────────

@router.get(
    "/{survey_id}/question-responses",
    response_model=QuestionResponseListResponse,
)
def get_survey_question_responses(survey_id: str, svc: SurveyServiceDep):
    responses = svc.get_question_responses(survey_id)
    items = [
        QuestionResponseOut(
            id=r.id,
            survey_id=r.survey_id,
            agent_id=r.agent_id,
            question_id=r.question_id,
            answer=r.answer,
            confidence=r.confidence,
            short_reason=r.short_reason,
            raw_llm_output=r.raw_llm_output,
            is_fallback=r.is_fallback,
            created_at=r.created_at,
        )
        for r in responses
    ]
    return QuestionResponseListResponse(responses=items, count=len(items))


# ── Aggregates ───────────────────────────────────────────

@router.post("/{survey_id}/aggregate", response_model=AggregateListResponse)
def compute_aggregates(survey_id: str, svc: SurveyServiceDep):
    aggregates = svc.compute_and_store_aggregates(survey_id)
    items = [
        AggregateOut(
            id=a.id,
            survey_id=a.survey_id,
            question_id=a.question_id,
            aggregation=a.aggregation,
            computed_at=a.computed_at,
        )
        for a in aggregates
    ]
    return AggregateListResponse(aggregates=items, count=len(items))


@router.get("/{survey_id}/aggregates", response_model=AggregateListResponse)
def get_aggregates(survey_id: str, svc: SurveyServiceDep):
    aggregates = svc.get_aggregates(survey_id)
    items = [
        AggregateOut(
            id=a.id,
            survey_id=a.survey_id,
            question_id=a.question_id,
            aggregation=a.aggregation,
            computed_at=a.computed_at,
        )
        for a in aggregates
    ]
    return AggregateListResponse(aggregates=items, count=len(items))


# ── Helpers ──────────────────────────────────────────────

def _survey_to_response(s) -> SurveyResponse:
    return SurveyResponse(
        id=s.id,
        title=s.title,
        mode=s.mode,
        input_text=s.input_text,
        status=s.status,
        model=s.model,
        n_agents=s.n_agents,
        seed=s.seed,
        parameters=s.parameters,
        created_by=s.created_by,
        elapsed_seconds=s.elapsed_seconds,
        started_at=s.started_at,
        completed_at=s.completed_at,
        created_at=s.created_at,
    )
