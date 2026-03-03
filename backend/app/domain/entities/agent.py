from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Agent:
    id: str
    survey_id: str
    agent_index: int
    eco: float
    open: float
    trust: float
    temperament: float
    age: int
    education: str
    urban_rural: str
    classe_sociale: str
    background: str
    created_at: datetime = field(default_factory=datetime.utcnow)
