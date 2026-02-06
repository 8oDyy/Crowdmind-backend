from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Reaction:
    id: str
    experiment_id: str
    agent_id: str
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
