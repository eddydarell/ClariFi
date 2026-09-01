#!/usr/bin/env python3
"""Ticker suggestion engine using free Finnhub endpoints and yfinance trend checks."""

from __future__ import annotations

import json
import math
import os
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
import yfinance as yf

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # pragma: no cover - optional dependency
    pass


@dataclass
class TickerSuggestion:
    symbol: str
    score: float
    expected_7d_return: float
    momentum: float
    volume_signal: float
    analyst_bias: float
    risk_flag: str
    reason: str


class FinnhubAdapter:
    """Lightweight adapter using free-tier endpoints only."""

    def __init__(self, api_key: Optional[str] = None, session: Optional[requests.Session] = None):
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        self.session = session or requests.Session()
        self._rate_limit = deque(maxlen=60)
        self._base = "https://finnhub.io/api/v1"

    def _wait_for_slot(self) -> None:
        now = time.time()
        while self._rate_limit and now - self._rate_limit[0] < 1.0:
            time.sleep(0.05)
            now = time.time()
        self._rate_limit.append(now)

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {}

        self._wait_for_slot()
        url = f"{self._base}{path}"
        payload = {"token": self.api_key}
        if params:
            payload.update(params)

        response = self.session.get(url, params=payload, timeout=(3.05, 10))
        response.raise_for_status()
        return response.json() or {}

    def quote(self, symbol: str) -> Dict[str, Any]:
        try:
            data = self._get("/quote", {"symbol": symbol})
            if not data or "c" not in data:
                return {}
            return {
                "price": float(data.get("c", 0.0)),
                "change": float(data.get("d", 0.0)),
                "change_pct": float(data.get("dp", 0.0)),
                "prev_close": float(data.get("pc", 0.0)),
            }
        except Exception:
            return {}

    def recommendation_trends(self, symbol: str) -> Dict[str, Any]:
        try:
            rows = self._get("/stock/recommendation", {"symbol": symbol})
            if not rows:
                return {}
            latest = rows[0]
            buy = float(latest.get("buy", 0) or 0)
            hold = float(latest.get("hold", 0) or 0)
            sell = float(latest.get("sell", 0) or 0)
            strong_buy = float(latest.get("strongBuy", 0) or 0)
            strong_sell = float(latest.get("strongSell", 0) or 0)

            total = max(buy + hold + sell + strong_buy + strong_sell, 1.0)
            bias = ((strong_buy * 2.5) + (buy * 1.2) + (hold * 0.2) - (sell * 1.5) - (strong_sell * 2.8)) / total
            return {
                "bias": bias,
                "buy": buy,
                "hold": hold,
                "sell": sell,
                "strong_buy": strong_buy,
                "strong_sell": strong_sell,
            }
        except Exception:
            return {}

    def company_profile(self, symbol: str) -> Dict[str, Any]:
        try:
            profile = self._get("/stock/profile2", {"symbol": symbol})
            if not profile:
                return {}
            return {
                "name": profile.get("name"),
                "currency": profile.get("currency"),
                "exchange": profile.get("exchange"),
                "market_cap": float(profile.get("marketCapitalization", 0) or 0),
                "country": profile.get("country"),
            }
        except Exception:
            return {}


class TickerSuggestionEngine:
    """Custom short-term growth screener for actionable ticker suggestions."""

    DEFAULT_UNIVERSE = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD", "AVGO",
        "CRM", "ADBE", "NFLX", "PLTR", "ORCL", "INTC", "QCOM", "CSCO", "IBM",
        "SHOP", "UBER", "SPY", "QQQ", "XOM", "CVX", "COP", "SLB", "EOG", "MPC",
        "V", "MA", "PYPL", "SQ", "NKE", "COST", "HD", "WMT", "PFE", "LLY",
        "UNH", "JPM", "BAC", "GS", "MS", "C", "SCHW", "AXP", "TFC", "USB",
        "DIS", "CMCSA", "NEM", "FCX", "CAT", "DE", "HON", "UPS", "LOW", "KHC",
        "SNOW", "HOOD", "COIN", "RIVN", "LCID", "U", "GME", "AMC", "BB", "RIOT",
    ]

    def __init__(self, finnhub: Optional[FinnhubAdapter] = None, min_score: float = 55.0):
        self.finnhub = finnhub or FinnhubAdapter()
        self.min_score = min_score

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _calculate_momentum(self, history: Any) -> float:
        if history is None or getattr(history, "empty", True):
            return 0.0
        closes = history["Close"].dropna()
        if len(closes) < 5:
            return 0.0
        day1 = closes.iloc[-1]
        day5 = closes.iloc[-5]
        day10 = closes.iloc[-10] if len(closes) >= 10 else closes.iloc[0]
        short = ((day1 - day5) / day5) * 100.0 if day5 else 0.0
        mid = ((day1 - day10) / day10) * 100.0 if day10 else 0.0
        return max(short, mid)

    def _calculate_volume_signal(self, history: Any) -> float:
        if history is None or getattr(history, "empty", True):
            return 0.0
        vol = history["Volume"].dropna()
        if len(vol) < 10:
            return 0.0
        recent = vol.iloc[-5:].mean()
        baseline = vol.iloc[:-5].mean() if len(vol) > 5 else vol.mean()
        if baseline <= 0:
            return 0.0
        return ((recent - baseline) / baseline) * 100.0

    def _calculate_risk_flag(self, history: Any, price: float) -> str:
        if price <= 0:
            return "HIGH"
        if history is None or getattr(history, "empty", True):
            return "MEDIUM"

        closes = history["Close"].dropna()
        if len(closes) < 10:
            return "MEDIUM"

        recent = closes.iloc[-5:]
        std = recent.std()
        mean = recent.mean()
        if mean <= 0:
            return "MEDIUM"
        volatility_pct = (std / mean) * 100.0

        if volatility_pct > 8.0:
            return "HIGH"
        if volatility_pct > 4.0:
            return "MEDIUM"
        return "LOW"

    def _score_ticker(self, symbol: str, history: Any) -> Optional[TickerSuggestion]:
        if history is None or getattr(history, "empty", True):
            return None

        close = history["Close"].dropna()
        if len(close) < 10:
            return None

        price = float(close.iloc[-1])
        if price < 4.0:
            return None

        momentum = self._calculate_momentum(history)
        volume_signal = self._calculate_volume_signal(history)
        risk_flag = self._calculate_risk_flag(history, price)

        quote = self.finnhub.quote(symbol)
        quote_price = float(quote.get("price", price) or price)
        analyst = self.finnhub.recommendation_trends(symbol)
        analyst_bias = float(analyst.get("bias", 0.0) or 0.0)
        self.finnhub.company_profile(symbol)

        analyst_score = 50.0 + (analyst_bias * 20.0)
        analyst_score = max(0.0, min(100.0, analyst_score))

        score = (
            0.45 * _normalize(momentum, min_val=-20, max_val=20, midpoint=0)
            + 0.25 * _normalize(volume_signal, min_val=-30, max_val=60, midpoint=0)
            + 0.20 * analyst_score
            + 0.10 * _normalize(quote_price / max(price, 1.0), min_val=0.8, max_val=1.2, midpoint=1.0)
        )

        expected_7d_return = momentum * 0.7 + analyst_bias * 5.0 + volume_signal * 0.08
        reason_parts: List[str] = []
        if momentum > 4:
            reason_parts.append(f"7d momentum {momentum:.2f}%")
        if volume_signal > 25:
            reason_parts.append(f"volume surge +{volume_signal:.1f}%")
        if analyst_bias > 0.3:
            reason_parts.append("analyst sentiment tilting positive")

        if score < self.min_score:
            return None

        return TickerSuggestion(
            symbol=symbol,
            score=float(score),
            expected_7d_return=float(expected_7d_return),
            momentum=float(momentum),
            volume_signal=float(volume_signal),
            analyst_bias=float(analyst_bias),
            risk_flag=risk_flag,
            reason="; ".join(reason_parts) if reason_parts else "short-term trend and flow improvement",
        )

    def discover_suggestions(self, universe: Optional[List[str]] = None, limit: int = 10) -> List[TickerSuggestion]:
        universe = universe or self.DEFAULT_UNIVERSE
        results: List[TickerSuggestion] = []

        for symbol in universe:
            normalized_symbol = str(symbol).upper()
            try:
                history = yf.Ticker(normalized_symbol).history(period="1mo", interval="1d")
                suggestion = self._score_ticker(normalized_symbol, history)
                if suggestion is not None:
                    results.append(suggestion)
            except Exception:
                continue

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:limit]


def _normalize(value: float, min_val: float, max_val: float, midpoint: float = 0.0) -> float:
    if math.isnan(value):
        return 0.0
    capped = max(min_val, min(max_val, value))
    if midpoint == 0.0:
        return ((capped - min_val) / (max_val - min_val)) * 100.0
    if value >= midpoint:
        return ((value - midpoint) / (max_val - midpoint)) * 100.0 if max_val > midpoint else 100.0
    return ((value - min_val) / (midpoint - min_val)) * 100.0 if midpoint > min_val else 0.0


def run_suggestion_cycle() -> None:
    engine = TickerSuggestionEngine()
    suggestions = engine.discover_suggestions(limit=10)

    for item in suggestions:
        print(json.dumps({
            "symbol": item.symbol,
            "score": round(item.score, 2),
            "expected_7d_return": round(item.expected_7d_return, 2),
            "momentum": round(item.momentum, 2),
            "volume_signal": round(item.volume_signal, 2),
            "analyst_bias": round(item.analyst_bias, 2),
            "risk_flag": item.risk_flag,
            "reason": item.reason,
        }, separators=(",", ":")))


if __name__ == "__main__":
    run_suggestion_cycle()
