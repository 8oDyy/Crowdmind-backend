from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Model:
    id: str
    name: str
    version: str
    target_device: str | None = None
    labels: list[str] | None = None
    storage_path: str | None = None
    checksum: str | None = None
    size: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
