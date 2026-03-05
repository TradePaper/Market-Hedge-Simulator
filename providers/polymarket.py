import os
from datetime import datetime, timezone
from typing import List, Optional

import requests

from .base import MarketProvider, MarketData, Outcome

CLOB_BASE = os.environ.get("POLYMARKET_API_BASE", "https://clob.polymarket.com")
_TIMEOUT = 8
_MAX_RETRIES = 2


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/json", "User-Agent": "ProbEdge/1.0"})
    return s


def _normalize(raw: dict) -> Optional[MarketData]:
    try:
        tokens = raw.get("tokens") or []
        if not tokens:
            return None

        outcomes = [
            Outcome(
                name=t["outcome"],
                price=float(t.get("price", 0)),
                implied_prob=float(t.get("price", 0)),
            )
            for t in tokens
        ]

        yes_token = next(
            (t for t in tokens if t.get("outcome", "").lower() == "yes"),
            tokens[0],
        )
        price = float(yes_token.get("price", 0))

        return MarketData(
            event_id=raw["condition_id"],
            title=raw.get("question", "Untitled"),
            outcomes=outcomes,
            price=price,
            implied_prob=price,
            source="polymarket",
            updated_at=datetime.now(timezone.utc).isoformat(),
            end_date=raw.get("end_date_iso"),
        )
    except (KeyError, TypeError, ValueError):
        return None


class PolymarketProvider(MarketProvider):
    def __init__(self):
        self._last_fetched: str = ""
        self._session = _session()

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{CLOB_BASE}{path}"
        last_err = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = self._session.get(url, params=params, timeout=_TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"Polymarket API unavailable after {_MAX_RETRIES + 1} attempts: {last_err}")

    def get_markets(self, limit: int = 20) -> List[MarketData]:
        data = self._get("/markets", params={"limit": min(limit, 100)})
        raw_list = data.get("data", data) if isinstance(data, dict) else data
        if not isinstance(raw_list, list):
            raw_list = []

        results = []
        for raw in raw_list:
            if raw.get("closed") or raw.get("archived"):
                continue
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
            self._last_fetched = datetime.now(timezone.utc).isoformat()
            return _normalize(raw)
        except RuntimeError:
            return None

    def get_timestamp(self) -> str:
        return self._last_fetched or datetime.now(timezone.utc).isoformat()
