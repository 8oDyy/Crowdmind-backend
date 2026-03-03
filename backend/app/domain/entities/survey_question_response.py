from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SurveyQuestionResponse:
    id: str
    survey_id: str
    agent_id: str
    question_id: str
    answer: str
    confidence: float = 0.5
    short_reason: str | None = None
    raw_llm_output: str | None = None
    is_fallback: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
