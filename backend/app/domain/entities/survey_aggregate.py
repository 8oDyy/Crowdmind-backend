from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SurveyAggregate:
    id: str
    survey_id: str
    question_id: str | None = None
    aggregation: dict[str, Any] = field(default_factory=dict)
    computed_at: datetime = field(default_factory=datetime.utcnow)
