from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.enums.common import ExperimentStatus


@dataclass
class Experiment:
    id: str
    name: str
    status: ExperimentStatus = ExperimentStatus.DRAFT
    scenario: dict[str, Any] | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
