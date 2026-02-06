from typing import Any


class RedisClient:
    """Stub Redis client for future caching implementation."""

    def __init__(self, url: str | None = None):
        self._url = url
        self._client: Any = None

    def get(self, key: str) -> Any | None:
        return None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        pass

    def delete(self, key: str) -> None:
        pass


_redis_client: RedisClient | None = None


def get_redis_client() -> RedisClient:
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
