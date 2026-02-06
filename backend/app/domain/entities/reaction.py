from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AgentReaction:
    id: str
    experiment_id: str
    agent_id: str
    reaction: str
    emotion: str
    score: float | None = None
    raw_data: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
