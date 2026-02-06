from typing import Any

from app.core.config import get_settings
from app.core.errors import RepoError


class SupabaseClient:
    def __init__(self, url: str, key: str, schema: str = "public"):
        self._url = url
        self._key = key
        self._schema = schema
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            if not self._url or not self._key:
                raise RepoError("Supabase URL and KEY must be configured")
            try:
                from supabase import create_client
                self._client = create_client(self._url, self._key)
            except ImportError:
                raise RepoError("supabase package not installed")
        return self._client

    def table(self, name: str) -> Any:
        return self._get_client().table(name)

    def select(
        self,
        table: str,
        columns: str = "*",
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        order_desc: bool = False,
    ) -> list[dict[str, Any]]:
        try:
            query = self.table(table).select(columns)
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            if order_by:
                query = query.order(order_by, desc=order_desc)
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
            response = query.execute()
            return response.data or []
        except Exception as e:
            raise RepoError(f"Select failed on {table}: {e}")

    def select_one(
        self,
        table: str,
        columns: str = "*",
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        results = self.select(table, columns, filters, limit=1)
        return results[0] if results else None

    def insert(
        self,
        table: str,
        data: dict[str, Any] | list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        try:
            response = self.table(table).insert(data).execute()
            return response.data or []
        except Exception as e:
            raise RepoError(f"Insert failed on {table}: {e}")

    def update(
        self,
        table: str,
        data: dict[str, Any],
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        try:
            query = self.table(table).update(data)
            for key, value in filters.items():
                query = query.eq(key, value)
            response = query.execute()
            return response.data or []
        except Exception as e:
            raise RepoError(f"Update failed on {table}: {e}")

    def delete(
        self,
        table: str,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        try:
            query = self.table(table).delete()
            for key, value in filters.items():
                query = query.eq(key, value)
            response = query.execute()
            return response.data or []
        except Exception as e:
            raise RepoError(f"Delete failed on {table}: {e}")


_supabase_client: SupabaseClient | None = None


def get_supabase_client() -> SupabaseClient:
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = SupabaseClient(
            url=settings.SUPABASE_URL,
            key=settings.SUPABASE_SERVICE_ROLE_KEY,
            schema=settings.SUPABASE_SCHEMA,
        )
    return _supabase_client


def reset_supabase_client() -> None:
    global _supabase_client
    _supabase_client = None
