"""Realtime Finnhub trade-stream websocket client running on a background thread."""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from websockets.sync.client import connect as ws_connect

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - optional dependency
    pass


class FinnhubWebsocketClient:
    """
    Streams realtime trades via ``wss://ws.finnhub.io`` and keeps a lock-guarded
    cache of the latest price per subscribed symbol.

    The websocket runs on a daemon thread so synchronous callers (e.g. the
    intraday monitor's poll loop) can pull the freshest price on every tick.
    Connections are re-established with a fixed backoff, re-subscribing all
    tracked symbols on every reconnect.
    """

    WS_URL = "wss://ws.finnhub.io?token={token}"

    def __init__(
        self,
        api_key: Optional[str] = None,
        reconnect_seconds: float = 5.0,
        recv_timeout: float = 1.0,
    ):
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        self.reconnect_seconds = reconnect_seconds
        self.recv_timeout = recv_timeout

        self._prices: Dict[str, Dict[str, Any]] = {}
        self._subscribed: set = set()
        self._pending: List[tuple] = []
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._connected = False
        self._error: Optional[str] = None

    # ------------------------------------------------------------------ state

    @property
    def running(self) -> bool:
        return self._running

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def last_error(self) -> Optional[str]:
        return self._error

    @property
    def subscribed_symbols(self) -> List[str]:
        with self._lock:
            return sorted(self._subscribed)

    # ------------------------------------------------------------ lifecycle

    def start(self) -> None:
        """Start the background receive thread (idempotent)."""
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._error = None
        self._thread = threading.Thread(
            target=self._run, name="finnhub-ws", daemon=True
        )
        self._thread.start()

    def close(self) -> None:
        """Stop the background thread and drop cached prices."""
        self._running = False
        self._connected = False
        with self._lock:
            self._prices.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    stop = close

    # ----------------------------------------------------------- subscriptions

    def subscribe(self, symbols: List[str]) -> None:
        """Track and stream the given symbols (idempotent across reconnects)."""
        symbols = [s.strip().upper() for s in symbols if s and s.strip().upper()]
        if not symbols:
            return
        with self._lock:
            for symbol in symbols:
                if symbol not in self._subscribed:
                    self._subscribed.add(symbol)
                    self._pending.append(("subscribe", symbol))

    def unsubscribe(self, symbols: List[str]) -> None:
        symbols = [s.strip().upper() for s in symbols if s and s.strip().upper()]
        if not symbols:
            return
        with self._lock:
            for symbol in symbols:
                self._subscribed.discard(symbol)
                self._pending.append(("unsubscribe", symbol))
            for symbol in symbols:
                self._prices.pop(symbol, None)

    # ------------------------------------------------------------- read side

    def latest_trades(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {symbol: dict(entry) for symbol, entry in self._prices.items()}

    def get_quote(
        self, symbol: str, max_age_seconds: Optional[float] = 300.0
    ) -> Optional[Dict[str, Any]]:
        """
        Normalized realtime quote for ``symbol`` or ``None`` when no fresh trade
        has been received. ``max_age_seconds=None`` disables staleness checks.
        """
        symbol = symbol.strip().upper()
        with self._lock:
            entry = self._prices.get(symbol)
            if not entry:
                return None
            if max_age_seconds is not None:
                now = time.time()
                ts_seconds = entry.get("_ts_seconds", 0.0)
                if now - ts_seconds > max_age_seconds:
                    return None
        return self._normalize(symbol, entry)

    def get_price(
        self, symbol: str, max_age_seconds: Optional[float] = 300.0
    ) -> Optional[float]:
        quote = self.get_quote(symbol, max_age_seconds=max_age_seconds)
        return quote["price"] if quote else None

    # ------------------------------------------------------------------ internals

    def _normalize(self, symbol: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        ts_ms = entry.get("timestamp_ms")
        timestamp = None
        if ts_ms:
            try:
                timestamp = datetime.fromtimestamp(
                    ts_ms / 1000.0, timezone.utc
                ).isoformat()
            except (ValueError, OSError, TypeError, OverflowError):
                timestamp = None
        return {
            "symbol": symbol,
            "price": entry["price"],
            "previous_close": None,
            "currency": None,
            "exchange": None,
            "market_state": "open",
            "timestamp": timestamp,
            "volume": entry.get("volume"),
            "provider": "finnhub_ws",
            "freshness": "real_time",
            "cached": False,
        }

    def _run(self) -> None:
        while self._running:
            try:
                self._run_connection()
            except Exception as exc:  # noqa: BLE001 - reconnect on any transport failure
                self._error = repr(exc)
                self._connected = False
            if not self._running:
                break
            time.sleep(self.reconnect_seconds)

    def _run_connection(self) -> None:
        from websockets.exceptions import ConnectionClosed

        uri = self.WS_URL.format(token=self.api_key)
        with ws_connect(uri, open_timeout=10.0) as conn:
            self._connected = True
            self._error = None
            for symbol in self._subscribed_symbols_snapshot():
                conn.send(json.dumps({"type": "subscribe", "symbol": symbol}))
            while self._running:
                self._drain_pending(conn)
                try:
                    message = conn.recv(timeout=self.recv_timeout)
                except TimeoutError:
                    continue
                except ConnectionClosed:
                    raise
                self._handle_message(message)

    def _subscribed_symbols_snapshot(self) -> List[str]:
        with self._lock:
            return sorted(self._subscribed)

    def _drain_pending(self, conn) -> None:
        with self._lock:
            pending = self._pending
            self._pending = []
        for op, symbol in pending:
            try:
                conn.send(json.dumps({"type": op, "symbol": symbol}))
            except Exception:  # noqa: BLE001 - transport failure handled by caller
                self._error = repr(op)
                raise

    def _handle_message(self, raw: str) -> None:
        try:
            message = json.loads(raw)
        except (ValueError, TypeError):
            return
        if not isinstance(message, dict):
            return

        msg_type = message.get("type")
        data = message.get("data")

        if msg_type == "trade" and isinstance(data, list):
            now = time.time()
            with self._lock:
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    symbol = str(item.get("s") or "").strip().upper()
                    if not symbol:
                        continue
                    try:
                        price = float(item["p"])
                    except (KeyError, TypeError, ValueError):
                        continue
                    self._prices[symbol] = {
                        "price": price,
                        "timestamp_ms": item.get("t"),
                        "volume": item.get("v"),
                        "_ts_seconds": now,
                    }
        elif msg_type == "error":
            info = message.get("info") or message.get("data")
            self._error = f"finnhub ws error: {info}" if info else "finnhub ws error"
