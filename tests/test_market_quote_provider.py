import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from market_quote_provider import MarketQuoteProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        return FakeResponse(self.payload)


def test_get_quote_normalizes_twelve_data_response_and_uses_cache():
    session = FakeSession({
        "symbol": "AAPL",
        "close": "211.24",
        "previous_close": "209.50",
        "currency": "USD",
        "exchange": "NASDAQ",
        "market_state": "open",
        "datetime": "2026-08-30 14:30:00",
    })
    provider = MarketQuoteProvider(api_key="test-key", cache_ttl_seconds=300, session=session)

    first_quote = provider.get_quote("aapl")
    second_quote = provider.get_quote("AAPL")

    assert first_quote["price"] == 211.24
    assert first_quote["provider"] == "twelve_data"
    assert first_quote["freshness"] == "real_time"
    assert second_quote["cached"] is True
    assert session.calls == 1


def test_get_quote_uses_labeled_yfinance_fallback_when_primary_unavailable(monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame(
                {"Close": [100.0, 101.5]}, index=pd.to_datetime(["2026-08-28", "2026-08-29"])
            )

    monkeypatch.setattr("market_quote_provider.yf.Ticker", lambda symbol: FakeTicker())
    provider = MarketQuoteProvider()

    quote = provider.get_quote("VOD.L")

    assert quote["price"] == 101.5
    assert quote["provider"] == "yfinance"
    assert quote["freshness"] == "delayed_or_end_of_day"