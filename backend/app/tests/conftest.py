from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import (
    get_agent_repo,
    get_response_repo,
    get_survey_aggregate_repo,
    get_survey_question_repo,
    get_survey_question_response_repo,
    get_survey_repo,
)
from app.domain.entities.agent import Agent
from app.domain.entities.response import Response
from app.domain.entities.survey import Survey
from app.domain.entities.survey_aggregate import SurveyAggregate
from app.domain.entities.survey_question import SurveyQuestion
from app.domain.entities.survey_question_response import SurveyQuestionResponse
from app.main import app

# ── Fake Repositories ────────────────────────────────────


class FakeSurveyRepository:
    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    def create_survey(self, **kwargs) -> Survey:
        sid = str(uuid4())
        row = {"id": sid, "created_at": datetime.utcnow().isoformat(), **kwargs}
        row.setdefault("status", "pending")
        self._store[sid] = row
        return self._to_entity(row)

    def get_survey(self, survey_id: str) -> Survey:
        if survey_id not in self._store:
            from app.core.errors import NotFoundError

            raise NotFoundError(f"Survey {survey_id} not found")
        return self._to_entity(self._store[survey_id])

    def list_surveys(self, limit=100, offset=0, created_by=None) -> list[Survey]:
        rows = list(self._store.values())
        if created_by:
            rows = [r for r in rows if r.get("created_by") == created_by]
        return [self._to_entity(r) for r in rows[offset : offset + limit]]

    def update_survey(self, survey_id: str, data: dict) -> Survey:
        if survey_id not in self._store:
            from app.core.errors import NotFoundError

            raise NotFoundError(f"Survey {survey_id} not found")
        self._store[survey_id].update(data)
        return self._to_entity(self._store[survey_id])

    def delete_survey(self, survey_id: str) -> None:
        self._store.pop(survey_id, None)

    def _to_entity(self, row: dict) -> Survey:
        return Survey(
            id=row["id"],
            title=row.get("title", ""),
            mode=row.get("mode", "text"),
            input_text=row.get("input_text"),
            status=row.get("status", "pending"),
            model=row.get("model", "llama-3.3-70b-versatile"),
            n_agents=row.get("n_agents", 100),
            seed=row.get("seed", 42),
            parameters=row.get("parameters"),
            created_by=row.get("created_by"),
            elapsed_seconds=row.get("elapsed_seconds"),
        )


class FakeAgentRepository:
    def __init__(self):
        self._store: list[dict[str, Any]] = []

    def create_agents_batch(self, agents_data: list[dict]) -> list[Agent]:
        result = []
        for a in agents_data:
            a.setdefault("id", str(uuid4()))
            a.setdefault("created_at", datetime.utcnow().isoformat())
            self._store.append(a)
            result.append(self._to_entity(a))
        return result

    def list_agents_by_survey(self, survey_id: str, limit=1000, offset=0) -> list[Agent]:
        rows = [a for a in self._store if a.get("survey_id") == survey_id]
        return [self._to_entity(r) for r in rows[offset : offset + limit]]

    def delete_agents_by_survey(self, survey_id: str) -> None:
        self._store = [a for a in self._store if a.get("survey_id") != survey_id]

    def _to_entity(self, row: dict) -> Agent:
        return Agent(
            id=row["id"],
            survey_id=row["survey_id"],
            agent_index=row.get("agent_index", 0),
            eco=row.get("eco", 0),
            open=row.get("open", 0),
            trust=row.get("trust", 0.5),
            temperament=row.get("temperament", 0.5),
            age=row.get("age", 30),
            education=row.get("education", "bac+3"),
            urban_rural=row.get("urban_rural", "urbain"),
            classe_sociale=row.get("classe_sociale", "moyenne"),
            background=row.get("background", ""),
        )


class FakeResponseRepository:
    def __init__(self):
        self._store: list[dict[str, Any]] = []

    def create_responses_batch(self, rows: list[dict]) -> list[Response]:
        result = []
        for r in rows:
            r.setdefault("id", str(uuid4()))
            self._store.append(r)
            result.append(self._to_entity(r))
        return result

    def list_responses_by_survey(self, survey_id: str, limit=1000, offset=0) -> list[Response]:
        rows = [r for r in self._store if r.get("survey_id") == survey_id]
        return [self._to_entity(r) for r in rows[offset : offset + limit]]

    def delete_responses_by_survey(self, survey_id: str) -> None:
        self._store = [r for r in self._store if r.get("survey_id") != survey_id]

    def _to_entity(self, row: dict) -> Response:
        return Response(
            id=row["id"],
            survey_id=row["survey_id"],
            agent_id=row["agent_id"],
            stance=row.get("stance"),
            confidence=row.get("confidence", 0.5),
            short_reason=row.get("short_reason"),
            raw_llm_output=row.get("raw_llm_output"),
            is_fallback=row.get("is_fallback", False),
        )


class FakeSurveyAggregateRepository:
    def __init__(self):
        self._store: list[dict[str, Any]] = []

    def upsert_aggregate(self, survey_id, aggregation, question_id=None) -> SurveyAggregate:
        row = {
            "id": str(uuid4()),
            "survey_id": survey_id,
            "question_id": question_id,
            "aggregation": aggregation,
            "computed_at": datetime.utcnow(),
        }
        self._store.append(row)
        return SurveyAggregate(**row)

    def get_aggregates(self, survey_id: str) -> list[SurveyAggregate]:
        return [SurveyAggregate(**r) for r in self._store if r["survey_id"] == survey_id]

    def delete_by_survey(self, survey_id: str) -> None:
        self._store = [r for r in self._store if r["survey_id"] != survey_id]


class FakeSurveyQuestionRepository:
    def __init__(self):
        self._store: list[dict[str, Any]] = []

    def create_questions_batch(self, questions: list[dict]) -> list[SurveyQuestion]:
        result = []
        for q in questions:
            q.setdefault("id", str(uuid4()))
            self._store.append(q)
            result.append(self._to_entity(q))
        return result

    def list_by_survey(self, survey_id: str) -> list[SurveyQuestion]:
        rows = [q for q in self._store if q.get("survey_id") == survey_id]
        return [self._to_entity(q) for q in rows]

    def delete_by_survey(self, survey_id: str) -> None:
        self._store = [q for q in self._store if q.get("survey_id") != survey_id]

    def _to_entity(self, row: dict) -> SurveyQuestion:
        return SurveyQuestion(
            id=row["id"],
            survey_id=row["survey_id"],
            question_index=row.get("question_index", 0),
            question_id=row["question_id"],
            type=row["type"],
            text=row["text"],
            choices=row.get("choices"),
            scale=row.get("scale"),
        )


class FakeSurveyQuestionResponseRepository:
    def __init__(self):
        self._store: list[dict[str, Any]] = []

    def create_batch(self, rows: list[dict]) -> list[SurveyQuestionResponse]:
        result = []
        for r in rows:
            r.setdefault("id", str(uuid4()))
            self._store.append(r)
            result.append(self._to_entity(r))
        return result

    def list_by_survey(self, survey_id: str, limit=5000, offset=0) -> list[SurveyQuestionResponse]:
        rows = [r for r in self._store if r.get("survey_id") == survey_id]
        return [self._to_entity(r) for r in rows[offset : offset + limit]]

    def list_by_survey_and_question(self, survey_id, question_id) -> list[SurveyQuestionResponse]:
        rows = [
            r
            for r in self._store
            if r.get("survey_id") == survey_id and r.get("question_id") == question_id
        ]
        return [self._to_entity(r) for r in rows]

    def delete_by_survey(self, survey_id: str) -> None:
        self._store = [r for r in self._store if r.get("survey_id") != survey_id]

    def _to_entity(self, row: dict) -> SurveyQuestionResponse:
        return SurveyQuestionResponse(
            id=row["id"],
            survey_id=row["survey_id"],
            agent_id=row["agent_id"],
            question_id=row["question_id"],
            answer=row["answer"],
            confidence=row.get("confidence", 0.5),
            short_reason=row.get("short_reason"),
            raw_llm_output=row.get("raw_llm_output"),
            is_fallback=row.get("is_fallback", False),
        )


# ── Fixtures ─────────────────────────────────────────────


@pytest.fixture
def fake_survey_repo():
    return FakeSurveyRepository()


@pytest.fixture
def fake_agent_repo():
    return FakeAgentRepository()


@pytest.fixture
def fake_response_repo():
    return FakeResponseRepository()


@pytest.fixture
def fake_aggregate_repo():
    return FakeSurveyAggregateRepository()


@pytest.fixture
def fake_question_repo():
    return FakeSurveyQuestionRepository()


@pytest.fixture
def fake_question_response_repo():
    return FakeSurveyQuestionResponseRepository()


@pytest.fixture
def client(
    fake_survey_repo,
    fake_agent_repo,
    fake_response_repo,
    fake_aggregate_repo,
    fake_question_repo,
    fake_question_response_repo,
) -> TestClient:
    app.dependency_overrides[get_survey_repo] = lambda: fake_survey_repo
    app.dependency_overrides[get_agent_repo] = lambda: fake_agent_repo
    app.dependency_overrides[get_response_repo] = lambda: fake_response_repo
    app.dependency_overrides[get_survey_aggregate_repo] = lambda: fake_aggregate_repo
    app.dependency_overrides[get_survey_question_repo] = lambda: fake_question_repo
    app.dependency_overrides[get_survey_question_response_repo] = lambda: (
        fake_question_response_repo
    )

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
