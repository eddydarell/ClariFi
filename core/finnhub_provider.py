"""Finnhub quote and market-status providers with normalized, cache-friendly outputs."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - optional dependency
    pass


class _FinnhubBase:
    """Shared rate-limited GET helper for Finnhub REST endpoints."""

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
        min_interval_seconds: float = 1.1,
    ):
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        self.session = session or requests.Session()
        self._min_interval = min_interval_seconds
        self._last_request = 0.0

    def _wait_for_slot(self) -> None:
        wait = self._min_interval - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        self._wait_for_slot()
        url = f"{self.BASE_URL}{path}"
        payload = {"token": self.api_key}
        if params:
            payload.update(params)
        try:
            response = self.session.get(url, params=payload, timeout=(3.05, 10))
            response.raise_for_status()
            return response.json() or {}
        except (requests.RequestException, ValueError, TypeError):
            return None


class FinnhubQuoteProvider(_FinnhubBase):
    """
    Real-time quote provider using the Finnhub Quote endpoint.

    Mirrors the ``MarketQuoteProvider.get_quote`` interface so it can be used
    anywhere a quote provider is expected.
    """

    QUOTE_PATH = "/quote"

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_ttl_seconds: int = 10,
        session: Optional[requests.Session] = None,
    ):
        super().__init__(api_key=api_key, session=session)
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_quote(self, ticker: str) -> Dict[str, Any]:
        """Return a normalized Finnhub quote or an explicit unavailable fallback."""
        symbol = ticker.strip().upper()
        cached = self._cache.get(symbol)
        if cached and time.monotonic() - cached["_fetched"] < self.cache_ttl_seconds:
            quote = dict(cached["quote"])
            quote["cached"] = True
            return quote

        data = self._get(self.QUOTE_PATH, params={"symbol": symbol})
        if data is None:
            return self._unavailable(symbol)

        current = data.get("c")
        if current is None:
            return self._unavailable(symbol)

        quote = {
            "symbol": str(data.get("symbol") or symbol),
            "price": float(current),
            "previous_close": self._as_float(data.get("pc")),
            "day_open": self._as_float(data.get("o")),
            "day_high": self._as_float(data.get("h")),
            "day_low": self._as_float(data.get("l")),
            "change": self._as_float(data.get("d")),
            "change_pct": self._as_float(data.get("dp")),
            "currency": None,
            "exchange": None,
            "market_state": None,
            "timestamp": self._iso_from_unix(data.get("t")),
            "provider": "finnhub",
            "freshness": "real_time",
            "cached": False,
        }
        self._cache[symbol] = {"_fetched": time.monotonic(), "quote": quote}
        return quote

    @staticmethod
    def _unavailable(symbol: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "price": None,
            "previous_close": None,
            "day_open": None,
            "day_high": None,
            "day_low": None,
            "change": None,
            "change_pct": None,
            "currency": None,
            "exchange": None,
            "market_state": None,
            "timestamp": None,
            "provider": "unavailable",
            "freshness": "unavailable",
            "cached": False,
        }

    @staticmethod
    def _iso_from_unix(unix_seconds: Any) -> Optional[str]:
        if unix_seconds in (None, ""):
            return None
        try:
            return datetime.fromtimestamp(float(unix_seconds), timezone.utc).isoformat()
        except (ValueError, OSError, TypeError, OverflowError):
            return None

    @staticmethod
    def _as_float(value: Any) -> Optional[float]:
        return float(value) if value not in (None, "") else None


class FinnhubMarketStatusProvider(_FinnhubBase):
    """
    Market-status provider using the Finnhub Market Status endpoint.

    The endpoint returns the exchange's own timestamp and timezone, so
    ``minutes_to_close`` is computed in the *market's* timezone rather than the
    server's local clock.
    """

    STATUS_PATH = "/stock/market-status"

    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
        ttl_seconds: int = 60,
        eod_time: str = "15:55",
        timezone_override: Optional[str] = None,
    ):
        super().__init__(api_key=api_key, session=session)
        self.ttl_seconds = ttl_seconds
        self.eod_hour, self.eod_minute = (int(x) for x in eod_time.split(":"))
        self.timezone_override = timezone_override
        self._cache: Optional[Dict[str, Any]] = None
        self._fetched_at = 0.0

    @property
    def eod_clock(self) -> str:
        return f"{self.eod_hour:02d}:{self.eod_minute:02d}"

    def get_status(self, exchange: str = "US") -> Optional[Dict[str, Any]]:
        """Return normalized market status; crashes/limit errors degrade to ``None``."""
        if self._cache and time.monotonic() - self._fetched_at < self.ttl_seconds:
            return dict(self._cache)

        data = self._get(self.STATUS_PATH, params={"exchange": exchange})
        if not data:
            return None

        timezone_name = (
            self.timezone_override or data.get("timezone") or "America/New_York"
        )
        status = {
            "exchange": data.get("exchange") or exchange,
            "is_open": bool(data.get("isOpen")),
            "session": data.get("session"),
            "holiday": data.get("holiday"),
            "timezone": timezone_name,
            "market_time": self._market_time(data.get("t"), timezone_name),
        }
        self._cache = status
        self._fetched_at = time.monotonic()
        return dict(status)

    def minutes_to_close(self, exchange: str = "US") -> Optional[int]:
        """
        Minutes until the EOD flat deadline (default 15:55) in the market's timezone.

        Returns ``None`` when the market is not in (or approaching) a trading
        session (weekend, holiday, after-hours) so callers can distinguish
        "market closed" from an imminent deadline. Otherwise returns a value
        >= 0, clamped at 0 (already past the deadline).
        """
        status = self.get_status(exchange)
        if status is None or status["market_time"] is None:
            return None
        if status["session"] not in ("pre-market", "regular"):
            return None
        market_time = status["market_time"]
        if not isinstance(market_time.tzinfo, ZoneInfo):
            return None
        deadline = market_time.replace(
            hour=self.eod_hour, minute=self.eod_minute, second=0, microsecond=0
        )
        minutes = int((deadline - market_time).total_seconds() // 60)
        return max(minutes, 0)

    def is_market_open(self, exchange: str = "US") -> Optional[bool]:
        status = self.get_status(exchange)
        return status["is_open"] if status else None

    def current_session(self, exchange: str = "US") -> Optional[str]:
        status = self.get_status(exchange)
        return status["session"] if status else None

    @staticmethod
    def _market_time(unix_seconds: Any, timezone_name: str) -> Optional[datetime]:
        try:
            unix_seconds = float(unix_seconds)
        except (TypeError, ValueError):
            unix_seconds = None
        if unix_seconds is None:
            try:
                return datetime.now(ZoneInfo(timezone_name))
            except (KeyError, ValueError):
                return None
        try:
            return datetime.fromtimestamp(unix_seconds, ZoneInfo(timezone_name))
        except (ValueError, OSError, TypeError, OverflowError):
            return None
