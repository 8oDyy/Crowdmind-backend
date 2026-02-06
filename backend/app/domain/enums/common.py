from enum import Enum


class AgentType(str, Enum):
    DIGITAL = "digital"
    PHYSICAL = "physical"


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    STOPPED = "stopped"


class ExportFormat(str, Enum):
    JSONL = "jsonl"
    CSV = "csv"
