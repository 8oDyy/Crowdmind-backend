from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Dataset:
    id: str
    name: str
    version: str
    schema_def: dict[str, Any] | None = None
    labels: list[str] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DatasetRow:
    id: str
    dataset_id: str
    input_data: dict[str, Any]
    label: str
    meta: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
