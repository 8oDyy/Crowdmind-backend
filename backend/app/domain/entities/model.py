from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Model:
    id: str
    name: str
    framework: str
    description: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ModelVersion:
    id: str
    model_id: str
    version: str
    file_path: str
    checksum: str
    size_kb: int
    created_at: datetime = field(default_factory=datetime.utcnow)
