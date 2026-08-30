"""Current market quote retrieval with provider and freshness metadata."""

import os
import time
from typing import Any, Dict, Optional

import requests
import yfinance as yf

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class MarketQuoteProvider:
    """Fetch current quotes, preferring Twelve Data for supported symbols."""

    QUOTE_URL = "https://api.twelvedata.com/quote"

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_ttl_seconds: Optional[int] = None,
        session: Optional[requests.Session] = None,
    ):
        self.api_key = api_key or os.getenv("TWELVE_DATA_API_KEY")
        self.cache_ttl_seconds = cache_ttl_seconds or int(
            os.getenv("CLARIFI_QUOTE_CACHE_TTL_SECONDS", "300")
        )
        self.session = session or requests.Session()
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_quote(self, ticker: str) -> Dict[str, Any]:
        """Return a normalized quote; fallback quotes are explicitly non-real-time."""
        symbol = ticker.strip().upper()
        cached_quote = self._cache.get(symbol)
        if cached_quote and time.monotonic() - cached_quote["cached_at"] < self.cache_ttl_seconds:
            quote = dict(cached_quote["quote"])
            quote["cached"] = True
            return quote

        quote = self._get_twelve_data_quote(symbol) if self.api_key else None
        if quote:
            self._cache[symbol] = {"cached_at": time.monotonic(), "quote": quote}
            return quote
        return self._get_yfinance_fallback(symbol)

    def _get_twelve_data_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.get(
                self.QUOTE_URL,
                params={"symbol": symbol, "apikey": self.api_key},
                timeout=(3.05, 10),
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "error" or not data.get("close"):
                return None
            return {
                "symbol": data.get("symbol", symbol),
                "price": float(data["close"]),
                "previous_close": self._as_float(data.get("previous_close")),
                "currency": data.get("currency"),
                "exchange": data.get("exchange"),
                "market_state": data.get("market_state"),
                "timestamp": data.get("datetime"),
                "provider": "twelve_data",
                "freshness": "real_time",
                "cached": False,
            }
        except (requests.RequestException, ValueError, TypeError):
            return None

    def _get_yfinance_fallback(self, symbol: str) -> Dict[str, Any]:
        try:
            history = yf.Ticker(symbol).history(period="5d", interval="1d")
            if not history.empty:
                return {
                    "symbol": symbol,
                    "price": float(history["Close"].iloc[-1]),
                    "previous_close": self._as_float(history["Close"].iloc[-2]) if len(history) > 1 else None,
                    "currency": None,
                    "exchange": None,
                    "market_state": None,
                    "timestamp": history.index[-1].isoformat(),
                    "provider": "yfinance",
                    "freshness": "delayed_or_end_of_day",
                    "cached": False,
                }
        except (Exception,):
            pass
        return {
            "symbol": symbol,
            "price": None,
            "previous_close": None,
            "currency": None,
            "exchange": None,
            "market_state": None,
            "timestamp": None,
            "provider": "unavailable",
            "freshness": "unavailable",
            "cached": False,
        }

    @staticmethod
    def _as_float(value: Any) -> Optional[float]:
        return float(value) if value not in (None, "") else None