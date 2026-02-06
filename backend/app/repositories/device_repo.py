from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import NotFoundError, RepoError
from app.domain.entities.device import Device, DeviceDeployment
from app.infrastructure.db.supabase_client import SupabaseClient


class DeviceRepository:
    TABLE = "devices"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_device(
        self,
        serial_number: str,
        status: str = "offline",
    ) -> Device:
        data = {
            "id": str(uuid4()),
            "serial_number": serial_number,
            "status": status,
            "last_seen": None,
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create device")
        return self._to_device(result[0])

    def get_device(self, device_id: str) -> Device:
        row = self._db.select_one(self.TABLE, filters={"id": device_id})
        if not row:
            raise NotFoundError(f"Device {device_id} not found")
        return self._to_device(row)

    def get_device_by_serial(self, serial_number: str) -> Device | None:
        row = self._db.select_one(self.TABLE, filters={"serial_number": serial_number})
        return self._to_device(row) if row else None

    def update_status(
        self,
        device_id: str,
        status: str,
        last_seen: datetime | None = None,
    ) -> Device:
        data: dict[str, Any] = {"status": status}
        if last_seen:
            data["last_seen"] = last_seen.isoformat()
        
        result = self._db.update(
            self.TABLE,
            data=data,
            filters={"id": device_id},
        )
        if not result:
            raise NotFoundError(f"Device {device_id} not found")
        return self._to_device(result[0])

    def list_devices(self, limit: int = 100, offset: int = 0) -> list[Device]:
        rows = self._db.select(
            self.TABLE,
            limit=limit,
            offset=offset,
        )
        return [self._to_device(r) for r in rows]

    def _to_device(self, row: dict[str, Any]) -> Device:
        return Device(
            id=row["id"],
            serial_number=row["serial_number"],
            status=row["status"],
            last_seen=self._parse_datetime_opt(row.get("last_seen")),
        )

    def _parse_datetime_opt(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return None


class DeviceDeploymentRepository:
    TABLE = "device_deployments"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_deployment(
        self,
        device_id: str,
        agent_id: str,
        model_version_id: str,
    ) -> DeviceDeployment:
        data = {
            "device_id": device_id,
            "deployed_at": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "model_version_id": model_version_id,
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create device deployment")
        return self._to_deployment(result[0])

    def list_deployments(
        self,
        device_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DeviceDeployment]:
        rows = self._db.select(
            self.TABLE,
            filters={"device_id": device_id},
            limit=limit,
            offset=offset,
            order_by="deployed_at",
            order_desc=True,
        )
        return [self._to_deployment(r) for r in rows]

    def get_current_deployment(self, device_id: str) -> DeviceDeployment | None:
        rows = self._db.select(
            self.TABLE,
            filters={"device_id": device_id},
            limit=1,
            order_by="deployed_at",
            order_desc=True,
        )
        return self._to_deployment(rows[0]) if rows else None

    def _to_deployment(self, row: dict[str, Any]) -> DeviceDeployment:
        return DeviceDeployment(
            device_id=row["device_id"],
            deployed_at=self._parse_datetime(row["deployed_at"]),
            agent_id=row["agent_id"],
            model_version_id=row["model_version_id"],
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()
