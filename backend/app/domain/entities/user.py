from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class User:
    id: str
    email: str
    role: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
