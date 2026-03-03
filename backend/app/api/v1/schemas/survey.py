from datetime import datetime
from typing import Any

from pydantic import Field

from app.api.v1.schemas.common import BaseSchema


class QuestionCreate(BaseSchema):
    question_id: str = Field(..., min_length=1, max_length=50)
    type: str = Field(..., pattern="^(stance|likert|mcq)$")
    text: str = Field(..., min_length=1)
    choices: list[str] | None = None
    scale: list[int] | None = None


class SurveyCreate(BaseSchema):
    title: str = Field(..., min_length=1, max_length=255)
    mode: str = Field(..., pattern="^(text|questionnaire)$")
    input_text: str | None = None
    model: str = Field(default="llama-3.3-70b-versatile", max_length=100)
    n_agents: int = Field(default=100, ge=1, le=1000)
    seed: int = Field(default=42)
    parameters: dict[str, Any] | None = None
    questions: list[QuestionCreate] | None = None


class SurveyResponse(BaseSchema):
    id: str
    title: str
    mode: str
    input_text: str | None = None
    status: str
    model: str
    n_agents: int
    seed: int
    parameters: dict[str, Any] | None = None
    created_by: str | None = None
    elapsed_seconds: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class SurveyListResponse(BaseSchema):
    surveys: list[SurveyResponse]
    count: int


class SurveyQuestionResponse(BaseSchema):
    id: str
    survey_id: str
    question_index: int
    question_id: str
    type: str
    text: str
    choices: list[str] | None = None
    scale: list[int] | None = None
