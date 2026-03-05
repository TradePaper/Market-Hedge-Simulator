from datetime import datetime, timezone
from typing import List, Optional

from .base import MarketProvider, MarketData, Outcome

_MOCK_MARKETS: List[MarketData] = [
    MarketData(
        event_id="mock-001",
        title="Will the Fed raise rates at the next FOMC meeting?",
        outcomes=[
            Outcome(name="Yes", price=0.28, implied_prob=0.28),
            Outcome(name="No",  price=0.72, implied_prob=0.72),
        ],
        price=0.28,
        implied_prob=0.28,
        source="mock",
        updated_at="2026-03-05T12:00:00Z",
        volume=1_240_000,
        end_date="2026-05-07",
    ),
    MarketData(
        event_id="mock-002",
        title="Super Bowl LX Winner — Kansas City Chiefs",
        outcomes=[
            Outcome(name="Yes", price=0.34, implied_prob=0.34),
            Outcome(name="No",  price=0.66, implied_prob=0.66),
        ],
        price=0.34,
        implied_prob=0.34,
        source="mock",
        updated_at="2026-03-05T12:00:00Z",
        volume=8_900_000,
        end_date="2027-02-07",
    ),
    MarketData(
        event_id="mock-003",
        title="US Unemployment Below 4% at Year-End 2026?",
        outcomes=[
            Outcome(name="Yes", price=0.61, implied_prob=0.61),
            Outcome(name="No",  price=0.39, implied_prob=0.39),
        ],
        price=0.61,
        implied_prob=0.61,
        source="mock",
        updated_at="2026-03-05T12:00:00Z",
        volume=540_000,
        end_date="2026-12-31",
    ),
    MarketData(
        event_id="mock-004",
        title="Bitcoin Above $150k Before End of 2026?",
        outcomes=[
            Outcome(name="Yes", price=0.43, implied_prob=0.43),
            Outcome(name="No",  price=0.57, implied_prob=0.57),
        ],
        price=0.43,
        implied_prob=0.43,
        source="mock",
        updated_at="2026-03-05T12:00:00Z",
        volume=3_200_000,
        end_date="2026-12-31",
    ),
    MarketData(
        event_id="mock-005",
        title="Republican Wins 2026 Senate Majority?",
        outcomes=[
            Outcome(name="Yes", price=0.55, implied_prob=0.55),
            Outcome(name="No",  price=0.45, implied_prob=0.45),
        ],
        price=0.55,
        implied_prob=0.55,
        source="mock",
        updated_at="2026-03-05T12:00:00Z",
        volume=2_100_000,
        end_date="2026-11-03",
    ),
]

_INDEX = {m.event_id: m for m in _MOCK_MARKETS}


class MockProvider(MarketProvider):
    _fetched_at: str = ""

    def get_markets(self, limit: int = 20) -> List[MarketData]:
        self._fetched_at = datetime.now(timezone.utc).isoformat()
        return _MOCK_MARKETS[:limit]

    def get_prices(self, event_id: str) -> Optional[MarketData]:
        self._fetched_at = datetime.now(timezone.utc).isoformat()
        return _INDEX.get(event_id)

    def get_timestamp(self) -> str:
        return self._fetched_at or datetime.now(timezone.utc).isoformat()
