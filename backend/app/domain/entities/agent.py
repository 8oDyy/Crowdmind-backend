from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Agent:
    id: str
    label: str
    demographics: dict[str, Any] | None = None
    traits: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
