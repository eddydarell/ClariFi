import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.ticker_suggestion_engine import TickerSuggestionEngine


class FakeFInnhubAdapter:
    def quote(self, symbol):
        return {"price": 101.0, "change": 1.5, "change_pct": 1.4, "prev_close": 100.0}

    def recommendation_trends(self, symbol):
        return {"bias": 0.8, "buy": 22, "hold": 10, "sell": 4, "strong_buy": 8, "strong_sell": 1}

    def company_profile(self, symbol):
        return {"name": "Example Inc", "currency": "USD", "exchange": "NASDAQ", "market_cap": 500000000.0, "country": "US"}


def make_history(start=90.0, growth=0.02):
    closes = [start * (1 + growth) ** i for i in range(30)]
    opens = [close * 0.998 for close in closes]
    highs = [close * 1.01 for close in closes]
    lows = [close * 0.99 for close in closes]
    volumes = [1_200_000 + i * 15000 for i in range(30)]
    dates = pd.date_range(end=pd.Timestamp.utcnow(), periods=30, freq='D')
    return pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volumes,
    }, index=dates)


def test_discover_suggestions_returns_ranked_results(monkeypatch):
    engine = TickerSuggestionEngine(finnhub=FakeFInnhubAdapter(), min_score=55.0)

    class FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, period, interval):
            return make_history()

    monkeypatch.setattr('core.ticker_suggestion_engine.yf.Ticker', FakeTicker)

    results = engine.discover_suggestions(universe=['TEST'], limit=5)

    assert len(results) == 1
    assert results[0].symbol == 'TEST'
    assert results[0].score >= 55.0
    assert results[0].reason
    assert results[0].risk_flag in {'LOW', 'MEDIUM', 'HIGH'}
