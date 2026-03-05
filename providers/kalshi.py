import os
from datetime import datetime, timezone
from typing import List, Optional

import requests

from .base import MarketProvider, MarketData, Outcome

KALSHI_BASE = os.environ.get("KALSHI_API_BASE", "https://trading-api.kalshi.com/trade-api/v2")
_TIMEOUT = 8
_MAX_RETRIES = 2


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/json", "User-Agent": "ProbEdge/1.0"})
    api_key = os.environ.get("KALSHI_API_KEY", "")
    if api_key:
        s.headers["Authorization"] = f"Bearer {api_key}"
    return s


def _normalize(raw: dict) -> Optional[MarketData]:
    try:
        yes_price = raw.get("yes_ask", raw.get("last_price", 50)) / 100
        no_price  = round(1 - yes_price, 4)
        outcomes  = [
            Outcome(name="Yes", price=yes_price, implied_prob=yes_price),
            Outcome(name="No",  price=no_price,  implied_prob=no_price),
        ]
        volume_raw = raw.get("volume", raw.get("volume_24h", 0))
        return MarketData(
            event_id=raw["ticker"],
            title=raw.get("title", raw.get("subtitle", "Untitled")),
            outcomes=outcomes,
            price=yes_price,
            implied_prob=yes_price,
            source="kalshi",
            updated_at=datetime.now(timezone.utc).isoformat(),
            volume=float(volume_raw) if volume_raw else None,
            end_date=raw.get("close_time"),
        )
    except (KeyError, TypeError, ValueError):
        return None


class KalshiProvider(MarketProvider):
    def __init__(self):
        self._last_fetched: str = ""
        self._session = _session()

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{KALSHI_BASE}{path}"
        last_err = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = self._session.get(url, params=params, timeout=_TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"Kalshi API unavailable after {_MAX_RETRIES + 1} attempts: {last_err}")

    def get_markets(self, limit: int = 20) -> List[MarketData]:
        try:
            data = self._get("/markets", params={"limit": min(limit, 100), "status": "open"})
            raw_list = data.get("markets", [])
        except RuntimeError:
            return []

        results = []
        for raw in raw_list:
            market = _normalize(raw)
            if market:
                results.append(market)
            if len(results) >= limit:
                break

        self._last_fetched = datetime.now(timezone.utc).isoformat()
        return results

    def get_prices(self, event_id: str) -> Optional[MarketData]:
        try:
            raw = self._get(f"/markets/{event_id}")
            market_raw = raw.get("market", raw)
            self._last_fetched = datetime.now(timezone.utc).isoformat()
            return _normalize(market_raw)
        except RuntimeError:
            return None

    def get_timestamp(self) -> str:
        return self._last_fetched or datetime.now(timezone.utc).isoformat()
