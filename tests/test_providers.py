import time
import pytest
from unittest.mock import patch, MagicMock

from providers.base import MarketData, Outcome
from providers.mock import MockProvider
from providers.polymarket import _normalize as poly_normalize
from providers.kalshi import _normalize as kalshi_normalize
from providers.cache import CachedProvider


# ---------------------------------------------------------------------------
# Schema mapping tests
# ---------------------------------------------------------------------------

class TestPolymarketNormalize:
    def test_binary_market(self):
        raw = {
            "condition_id": "0xABC",
            "question": "Will it rain?",
            "active": True,
            "closed": False,
            "end_date_iso": "2026-06-01T00:00:00Z",
            "tokens": [
                {"outcome": "Yes", "price": 0.62, "winner": False},
                {"outcome": "No",  "price": 0.38, "winner": False},
            ],
        }
        m = poly_normalize(raw)
        assert m is not None
        assert m.event_id == "0xABC"
        assert m.title == "Will it rain?"
        assert m.source == "polymarket"
        assert abs(m.price - 0.62) < 1e-9
        assert abs(m.implied_prob - 0.62) < 1e-9
        assert len(m.outcomes) == 2
        assert m.outcomes[0].name == "Yes"
        assert m.end_date == "2026-06-01T00:00:00Z"

    def test_missing_tokens_returns_none(self):
        raw = {"condition_id": "0xDEF", "question": "Empty", "tokens": []}
        assert poly_normalize(raw) is None

    def test_categorical_market_first_token_as_price(self):
        raw = {
            "condition_id": "0x111",
            "question": "Who wins?",
            "tokens": [
                {"outcome": "Team A", "price": 0.45},
                {"outcome": "Team B", "price": 0.55},
            ],
        }
        m = poly_normalize(raw)
        assert m is not None
        assert len(m.outcomes) == 2
        assert m.outcomes[0].name == "Team A"


class TestKalshiNormalize:
    def test_binary_market(self):
        raw = {
            "ticker": "FED-25MAY-T4.75",
            "title": "Fed rate above 4.75%?",
            "yes_ask": 35,
            "volume": 500000,
            "close_time": "2025-05-07T18:00:00Z",
        }
        m = kalshi_normalize(raw)
        assert m is not None
        assert m.event_id == "FED-25MAY-T4.75"
        assert m.source == "kalshi"
        assert abs(m.price - 0.35) < 1e-9
        assert abs(m.implied_prob - 0.35) < 1e-9
        assert len(m.outcomes) == 2
        assert m.outcomes[1].name == "No"
        assert abs(m.outcomes[1].price - 0.65) < 1e-4

    def test_missing_ticker_returns_none(self):
        raw = {"title": "No ticker here", "yes_ask": 50}
        assert kalshi_normalize(raw) is None


# ---------------------------------------------------------------------------
# MockProvider
# ---------------------------------------------------------------------------

class TestMockProvider:
    def test_get_markets_returns_list(self):
        p = MockProvider()
        markets = p.get_markets()
        assert isinstance(markets, list)
        assert len(markets) > 0

    def test_market_schema_fields(self):
        p = MockProvider()
        m = p.get_markets(limit=1)[0]
        assert m.event_id
        assert m.title
        assert m.source == "mock"
        assert 0 <= m.price <= 1
        assert 0 <= m.implied_prob <= 1
        assert len(m.outcomes) >= 2

    def test_get_prices_found(self):
        p = MockProvider()
        markets = p.get_markets()
        first_id = markets[0].event_id
        result = p.get_prices(first_id)
        assert result is not None
        assert result.event_id == first_id

    def test_get_prices_not_found(self):
        p = MockProvider()
        assert p.get_prices("nonexistent-id-xyz") is None

    def test_limit(self):
        p = MockProvider()
        assert len(p.get_markets(limit=2)) == 2

    def test_get_timestamp_is_string(self):
        p = MockProvider()
        p.get_markets()
        ts = p.get_timestamp()
        assert isinstance(ts, str)
        assert len(ts) > 0


# ---------------------------------------------------------------------------
# API failure fallback-to-mock
# ---------------------------------------------------------------------------

class TestApiFailureFallback:
    def test_polymarket_falls_back_to_mock_on_error(self):
        from providers.polymarket import PolymarketProvider
        provider = PolymarketProvider()

        with patch.object(provider._session, "get", side_effect=Exception("network error")):
            with pytest.raises(RuntimeError, match="Polymarket API unavailable"):
                provider.get_markets()

        mock = MockProvider()
        markets = mock.get_markets()
        assert len(markets) > 0

    def test_kalshi_returns_empty_on_error(self):
        from providers.kalshi import KalshiProvider
        provider = KalshiProvider()

        with patch.object(provider._session, "get", side_effect=Exception("network error")):
            result = provider.get_markets()
        assert result == []


# ---------------------------------------------------------------------------
# Cache: stale-data handling
# ---------------------------------------------------------------------------

class TestCachedProvider:
    def _make_mock_data(self, source="mock") -> list:
        return [
            MarketData(
                event_id="test-1",
                title="Test Market",
                outcomes=[Outcome("Yes", 0.5, 0.5), Outcome("No", 0.5, 0.5)],
                price=0.5,
                implied_prob=0.5,
                source=source,
                updated_at="2026-03-05T00:00:00Z",
            )
        ]

    def test_cache_hit_does_not_call_inner_again(self):
        inner = MockProvider()
        cached = CachedProvider(inner, ttl=60)

        with patch.object(inner, "get_markets", wraps=inner.get_markets) as spy:
            cached.get_markets()
            cached.get_markets()
            assert spy.call_count == 1

    def test_cache_miss_after_ttl(self):
        inner = MockProvider()
        cached = CachedProvider(inner, ttl=0)

        with patch.object(inner, "get_markets", wraps=inner.get_markets) as spy:
            cached.get_markets()
            time.sleep(0.01)
            cached.get_markets()
            assert spy.call_count == 2

    def test_stale_data_returned_on_provider_error(self):
        inner = MockProvider()
        cached = CachedProvider(inner, ttl=0)

        cached.get_markets()

        with patch.object(inner, "get_markets", side_effect=RuntimeError("API down")):
            result = cached.get_markets()
        assert len(result) > 0

    def test_invalidate_clears_cache(self):
        inner = MockProvider()
        cached = CachedProvider(inner, ttl=9999)

        with patch.object(inner, "get_markets", wraps=inner.get_markets) as spy:
            cached.get_markets()
            cached.invalidate()
            cached.get_markets()
            assert spy.call_count == 2
