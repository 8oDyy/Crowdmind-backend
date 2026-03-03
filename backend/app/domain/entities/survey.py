from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Survey:
    id: str
    title: str
    mode: str
    input_text: str | None = None
    status: str = "pending"
    model: str = "llama-3.3-70b-versatile"
    n_agents: int = 100
    seed: int = 42
    parameters: dict[str, Any] | None = None
    created_by: str | None = None
    elapsed_seconds: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
