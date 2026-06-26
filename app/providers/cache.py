import time
from typing import Any, Hashable


class TtlCache:
    """A simple in-memory cache with Time-To-Live (TTL) expiration."""

    def __init__(self, ttl_seconds: float):
        self._ttl = ttl_seconds
        self._cache: dict[Hashable, tuple[Any, float]] = {}

    def get(self, key: Hashable) -> Any | None:
        """Retrieves a value from the cache. Returns None if key is missing or expired."""
        if key not in self._cache:
            return None
        value, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return None
        return value

    def set(self, key: Hashable, value: Any) -> None:
        """Stores a value in the cache with the configured TTL."""
        self._cache[key] = (value, time.time() + self._ttl)

    def clear(self) -> None:
        """Clears all cached entries."""
        self._cache.clear()
