from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Experiment:
    id: str
    title: str
    message: str
    mode: str
    created_by: str
    description: str | None = None
    parameters: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
