from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SurveyQuestion:
    id: str
    survey_id: str
    question_index: int
    question_id: str
    type: str
    text: str
    choices: list[str] | None = None
    scale: list[int] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
