from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.enums.common import AgentType


@dataclass
class Agent:
    id: str
    name: str
    type: AgentType
    traits: dict[str, Any] | None = None
    current_model_id: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
