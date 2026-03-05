import time
from typing import Dict, List, Optional, Tuple

from .base import MarketProvider, MarketData

_NOT_SET = object()


class CachedProvider(MarketProvider):
    """
    Wraps any MarketProvider with a simple in-memory TTL cache.
    Default TTL is 30 seconds; adjust per-instance with `ttl`.
    Falls back to the inner provider on miss or expiry.
    Falls back to stale cache data if the inner provider raises.
    """

    def __init__(self, inner: MarketProvider, ttl: int = 30):
        self._inner = inner
        self._ttl = ttl
        self._markets_cache: Tuple[float, List[MarketData]] = (0.0, [])
        self._prices_cache: Dict[str, Tuple[float, Optional[MarketData]]] = {}
        self._timestamp: str = ""

    def _markets_stale(self) -> bool:
        cached_at, _ = self._markets_cache
        return time.monotonic() - cached_at > self._ttl

    def _prices_stale(self, event_id: str) -> bool:
        entry = self._prices_cache.get(event_id)
        if entry is None:
            return True
        cached_at, _ = entry
        return time.monotonic() - cached_at > self._ttl

    def get_markets(self, limit: int = 20) -> List[MarketData]:
        if not self._markets_stale():
            _, cached = self._markets_cache
            return cached[:limit]
        try:
            fresh = self._inner.get_markets(limit)
            self._markets_cache = (time.monotonic(), fresh)
            self._timestamp = self._inner.get_timestamp()
            return fresh
        except Exception:
            _, stale = self._markets_cache
            if stale:
                return stale[:limit]
            raise

    def get_prices(self, event_id: str) -> Optional[MarketData]:
        if not self._prices_stale(event_id):
            _, cached = self._prices_cache[event_id]
            return cached
        try:
            fresh = self._inner.get_prices(event_id)
            self._prices_cache[event_id] = (time.monotonic(), fresh)
            self._timestamp = self._inner.get_timestamp()
            return fresh
        except Exception:
            entry = self._prices_cache.get(event_id)
            if entry:
                _, stale = entry
                return stale
            raise

    def get_timestamp(self) -> str:
        return self._timestamp or self._inner.get_timestamp()

    def invalidate(self):
        self._markets_cache = (0.0, [])
        self._prices_cache = {}
