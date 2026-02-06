from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.errors import NotFoundError, RepoError
from app.domain.entities.user import User
from app.infrastructure.db.supabase_client import SupabaseClient


class UserRepository:
    TABLE = "users"

    def __init__(self, db: SupabaseClient):
        self._db = db

    def create_user(
        self,
        email: str,
        role: str,
    ) -> User:
        data = {
            "id": str(uuid4()),
            "email": email,
            "role": role,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self._db.insert(self.TABLE, data)
        if not result:
            raise RepoError("Failed to create user")
        return self._to_user(result[0])

    def get_user(self, user_id: str) -> User:
        row = self._db.select_one(self.TABLE, filters={"id": user_id})
        if not row:
            raise NotFoundError(f"User {user_id} not found")
        return self._to_user(row)

    def get_user_by_email(self, email: str) -> User | None:
        row = self._db.select_one(self.TABLE, filters={"email": email})
        return self._to_user(row) if row else None

    def list_users(self, limit: int = 100, offset: int = 0) -> list[User]:
        rows = self._db.select(
            self.TABLE,
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_desc=True,
        )
        return [self._to_user(r) for r in rows]

    def _to_user(self, row: dict[str, Any]) -> User:
        return User(
            id=row["id"],
            email=row["email"],
            role=row["role"],
            created_at=self._parse_datetime(row.get("created_at")),
        )

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.utcnow()
