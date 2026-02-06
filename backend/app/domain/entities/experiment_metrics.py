from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ExperimentMetrics:
    experiment_id: str
    metrics: dict[str, Any]
    computed_at: datetime = field(default_factory=datetime.utcnow)
