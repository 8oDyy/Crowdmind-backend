from datetime import datetime

from app.api.v1.schemas.common import BaseSchema


class AgentResponse(BaseSchema):
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
    created_at: datetime


class AgentListResponse(BaseSchema):
    agents: list[AgentResponse]
    count: int
