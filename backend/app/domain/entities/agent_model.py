from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentModel:
    id: str
    agent_id: str
    model_version_id: str
    assigned_at: datetime = field(default_factory=datetime.utcnow)
