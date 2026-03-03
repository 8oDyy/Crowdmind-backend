from datetime import datetime
from typing import Any

from pydantic import Field

from app.api.v1.schemas.common import BaseSchema


class ResponseCreate(BaseSchema):
    agent_id: str = Field(..., min_length=1)
    stance: str | None = Field(default=None, pattern="^(agree|disagree|mixed)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    short_reason: str | None = Field(default=None, max_length=180)
    raw_llm_output: str | None = None
    is_fallback: bool = False


class ResponseOut(BaseSchema):
    id: str
    survey_id: str
    agent_id: str
    stance: str | None = None
    confidence: float
    short_reason: str | None = None
    raw_llm_output: str | None = None
    is_fallback: bool
    created_at: datetime


class ResponseListResponse(BaseSchema):
    responses: list[ResponseOut]
    count: int


class QuestionResponseCreate(BaseSchema):
    agent_id: str = Field(..., min_length=1)
    question_id: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    short_reason: str | None = Field(default=None, max_length=180)
    raw_llm_output: str | None = None
    is_fallback: bool = False


class QuestionResponseOut(BaseSchema):
    id: str
    survey_id: str
    agent_id: str
    question_id: str
    answer: str
    confidence: float
    short_reason: str | None = None
    raw_llm_output: str | None = None
    is_fallback: bool
    created_at: datetime


class QuestionResponseListResponse(BaseSchema):
    responses: list[QuestionResponseOut]
    count: int


class AggregateOut(BaseSchema):
    id: str
    survey_id: str
    question_id: str | None = None
    aggregation: dict[str, Any]
    computed_at: datetime


class AggregateListResponse(BaseSchema):
    aggregates: list[AggregateOut]
    count: int
