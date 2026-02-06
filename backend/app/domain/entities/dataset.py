from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Dataset:
    id: str
    name: str
    dataset_type: str
    created_by: str
    description: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DatasetVersion:
    id: str
    dataset_id: str
    version: str
    file_path: str
    format: str
    checksum: str
    size_kb: int
    schema: dict[str, Any] | None = None
    stats: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TrainingRun:
    id: str
    dataset_version_id: str
    model_id: str
    status: str
    output_model_version_id: str | None = None
    parameters: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    logs_path: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
