from dataclasses import dataclass
from datetime import datetime


@dataclass
class Device:
    id: str
    serial_number: str
    status: str
    last_seen: datetime | None = None


@dataclass
class DeviceDeployment:
    device_id: str
    deployed_at: datetime
    agent_id: str
    model_version_id: str
