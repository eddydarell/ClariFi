import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from finnhub_provider import FinnhubQuoteProvider, FinnhubMarketStatusProvider


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


def test_finnhub_quote_normalizes_and_caches():
    session = FakeSession(
        {
            "c": 261.74,
            "h": 263.31,
            "l": 260.68,
            "o": 261.07,
            "pc": 259.45,
            "t": 1700000000,
        }
    )
    provider = FinnhubQuoteProvider(
        api_key="test-key", cache_ttl_seconds=300, session=session
    )

    first = provider.get_quote("aapl")
    second = provider.get_quote("AAPL")

    assert first["price"] == 261.74
    assert first["previous_close"] == 259.45
    assert first["day_high"] == 263.31
    assert first["day_low"] == 260.68
    assert first["day_open"] == 261.07
    assert first["provider"] == "finnhub"
    assert first["freshness"] == "real_time"
    assert (
        first["timestamp"]
        == datetime.fromtimestamp(1700000000, timezone.utc).isoformat()
    )
    assert second["cached"] is True
    assert session.calls == 1


def test_finnhub_quote_unavailable_without_price():
    session = FakeSession({"c": None})
    provider = FinnhubQuoteProvider(
        api_key="test-key", cache_ttl_seconds=300, session=session
    )
    quote = provider.get_quote("XYZ")
    assert quote["price"] is None
    assert quote["provider"] == "unavailable"


def test_finnhub_quote_unavailable_without_api_key(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    provider = FinnhubQuoteProvider(api_key=None)
    quote = provider.get_quote("AAPL")
    assert quote["price"] is None
    assert quote["provider"] == "unavailable"


def _status_payload_for(
    iso_local, session="regular", is_open=True, tz="America/New_York"
):
    tzinfo = ZoneInfo(tz)
    dt = datetime.fromisoformat(iso_local).replace(tzinfo=tzinfo)
    return {
        "exchange": "US",
        "holiday": None,
        "isOpen": is_open,
        "session": session,
        "timezone": tz,
        "t": int(dt.timestamp()),
    }


def test_market_status_normalizes_response():
    payload = {
        "exchange": "US",
        "holiday": None,
        "isOpen": False,
        "session": "pre-market",
        "timezone": "America/New_York",
        "t": 1697018041,
    }
    provider = FinnhubMarketStatusProvider(
        api_key="test-key", session=FakeSession(payload)
    )
    status = provider.get_status()
    assert status["is_open"] is False
    assert status["session"] == "pre-market"
    assert status["timezone"] == "America/New_York"


def test_minutes_to_close_computed_in_market_timezone():
    payload = _status_payload_for("2026-09-07T15:30:00")
    provider = FinnhubMarketStatusProvider(
        api_key="test-key", session=FakeSession(payload), ttl_seconds=0
    )
    assert provider.minutes_to_close() == 25


def test_minutes_to_close_zero_when_past_deadline():
    payload = _status_payload_for(
        "2026-09-07T16:05:00", session="regular", is_open=True
    )
    provider = FinnhubMarketStatusProvider(
        api_key="test-key", session=FakeSession(payload), ttl_seconds=0
    )
    assert provider.minutes_to_close() == 0


def test_minutes_to_close_negative_clamped_to_zero():
    payload = _status_payload_for(
        "2026-09-07T16:00:00", session="regular", is_open=True
    )
    provider = FinnhubMarketStatusProvider(
        api_key="test-key", session=FakeSession(payload), ttl_seconds=0
    )
    assert provider.minutes_to_close() == 0


def test_minutes_to_close_none_when_market_closed():
    payload = _status_payload_for("2026-09-07T13:00:00", session=None, is_open=False)
    payload["holiday"] = "Labor Day"
    provider = FinnhubMarketStatusProvider(
        api_key="test-key", session=FakeSession(payload), ttl_seconds=0
    )
    assert provider.minutes_to_close() is None


def test_minutes_to_close_premarket_countdown():
    payload = _status_payload_for(
        "2026-09-07T08:30:00", session="pre-market", is_open=False
    )
    provider = FinnhubMarketStatusProvider(
        api_key="test-key", session=FakeSession(payload), ttl_seconds=0
    )
    assert provider.minutes_to_close() == 445


def test_market_status_returns_none_when_unavailable(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    provider = FinnhubMarketStatusProvider(api_key=None)
    assert provider.get_status() is None
    assert provider.minutes_to_close() is None


def test_market_status_cache_ttl():
    payload = _status_payload_for("2026-09-07T15:30:00")
    session = FakeSession(payload)
    provider = FinnhubMarketStatusProvider(
        api_key="test-key", session=session, ttl_seconds=300
    )
    provider.get_status()
    provider.get_status()
    assert session.calls == 1
