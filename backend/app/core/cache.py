import time
import json
from typing import Optional, Any, Dict
from datetime import datetime, timezone
from backend.app.core.config import settings
from backend.app.core.logging import logger


class InMemoryTTLCache:
    """
    Lightweight in-memory asynchronous TTL cache with expiration and automatic pruning.
    Avoids duplicate external API requests during bursts.
    """

    def __init__(self, default_ttl: int = settings.WEATHER_CACHE_TTL_SECONDS):
        self._default_ttl = default_ttl
        self._store: Dict[str, Dict[str, Any]] = {}

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        return time.time() > entry["expires_at"]

    async def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if self._is_expired(entry):
            del self._store[key]
            return None
        return entry["value"]

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "cached_at": datetime.now(timezone.utc).isoformat()
        }
        # Prune expired keys if store exceeds 500 items
        if len(self._store) > 500:
            self._prune()

    def _prune(self):
        now = time.time()
        expired = [k for k, v in self._store.items() if now > v["expires_at"]]
        for k in expired:
            self._store.pop(k, None)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def clear(self) -> None:
        self._store.clear()


cache = InMemoryTTLCache()
