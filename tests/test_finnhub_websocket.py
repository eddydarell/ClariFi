import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from finnhub_websocket import FinnhubWebsocketClient


def _trade_frame(price, symbol="AAPL", ts_ms=1600000000000, volume=100):
    return '{"type":"trade","data":[{"p":%s,"s":"%s","t":%s,"v":%d}]}' % (
        price,
        symbol,
        ts_ms,
        volume,
    )


def test_subscribe_tracks_symbols_and_pending():
    client = FinnhubWebsocketClient(api_key="test-key")
    client.subscribe(["aapl", "MSFT"])
    assert client.subscribed_symbols == ["AAPL", "MSFT"]
    assert client.subscribed_symbols  # snapshot sorted
    assert len(client._pending) == 2  # noqa: SLF001


def test_handle_trade_message_updates_price_cache():
    client = FinnhubWebsocketClient(api_key="test-key")
    client._handle_message(_trade_frame(261.74))
    quote = client.get_quote("AAPL")
    assert quote["price"] == 261.74
    assert quote["provider"] == "finnhub_ws"
    assert quote["freshness"] == "real_time"
    assert quote["volume"] == 100


def test_handle_message_ignores_malformed_frames():
    client = FinnhubWebsocketClient(api_key="test-key")
    client._handle_message("not json")
    client._handle_message('{"type":"ping"}')
    assert client.get_quote("AAPL") is None


def test_get_quote_none_when_no_trade():
    client = FinnhubWebsocketClient(api_key="test-key")
    assert client.get_quote("AAPL") is None
    assert client.get_price("AAPL") is None


def test_get_quote_none_when_stale():
    client = FinnhubWebsocketClient(api_key="test-key")
    client._handle_message(_trade_frame(261.74))
    client._prices["AAPL"]["_ts_seconds"] = time.time() - 1000
    assert client.get_quote("AAPL", max_age_seconds=60) is None
    assert client.get_quote("AAPL", max_age_seconds=None)["price"] == 261.74


def test_unsubscribe_drops_symbol():
    client = FinnhubWebsocketClient(api_key="test-key")
    client.subscribe(["AAPL"])
    client._handle_message(_trade_frame(261.74))
    client.unsubscribe(["AAPL"])
    assert "AAPL" not in client.subscribed_symbols
    assert client.get_quote("AAPL") is None


def test_close_without_start_is_safe():
    client = FinnhubWebsocketClient(api_key="test-key")
    assert client.running is False
    assert client.connected is False
    client.close()
    assert client.running is False
