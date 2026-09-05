#!/usr/bin/env python3
"""
Intraday Stock Screener and Scout Engine
Scouts stocks with the best intraday odds using Relative Volume (RVOL),
Morning Gap %, ATR Volatility, VWAP distance, and opening momentum metrics.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, time as dtime
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import yfinance as yf

# Cross-platform color support
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = ""
        RED = ""
        YELLOW = ""
        CYAN = ""
        MAGENTA = ""
        BLUE = ""
        WHITE = ""
    class Style:
        RESET_ALL = ""

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from market_quote_provider import MarketQuoteProvider


@dataclass
class IntradayCandidate:
    """Scouted stock candidate for intraday trading with calculated metrics."""
    ticker: str
    current_price: float
    previous_close: float
    open_price: float
    gap_pct: float
    rvol: float  # Relative Volume (>1.5 indicates high institutional interest)
    atr: float  # 14-period Average True Range ($)
    atr_pct: float  # ATR as % of current price
    volume: int
    avg_volume: int
    vwap: float
    vwap_distance_pct: float  # (price - VWAP) / VWAP * 100
    intraday_odds_score: float  # 0 to 100 composite intraday score
    suitable_profiles: List[str]  # e.g., ['HIGH_RISK', 'LOW_RISK']
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IntradayScreener:
    """
    Intraday Screener that evaluates candidate stocks and ranks them based on
    daytrading potential (liquidity, volatility, momentum, and catalyst volume).
    """

    DEFAULT_UNIVERSE = [
        # Mega caps & highly liquid tech
        'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX',
        # High-beta growth / momentum
        'PLTR', 'COIN', 'SOFI', 'MARA', 'RIOT', 'ROKU', 'SQ', 'SHOP', 'HOOD',
        # Semis & Hardware
        'SMCI', 'ARM', 'AVGO', 'INTC', 'MU', 'QCOM',
        # Financials / Energy / Volatile Industrials
        'JPM', 'BAC', 'XOM', 'CVX', 'OXY', 'CAT', 'BA',
        # High volatility / retail focus
        'DKNG', 'RIVN', 'LCID', 'UBER', 'SNAP'
    ]

    def __init__(self, quote_provider: Optional[MarketQuoteProvider] = None):
        self.quote_provider = quote_provider or MarketQuoteProvider()

    def compute_intraday_metrics(
        self,
        ticker: str,
        df_daily: Optional[pd.DataFrame] = None,
        df_intraday: Optional[pd.DataFrame] = None,
        realtime_quote: Optional[Dict[str, Any]] = None,
    ) -> Optional[IntradayCandidate]:
        """
        Calculates intraday trading parameters for a given ticker.
        """
        ticker = ticker.strip().upper()

        # 1. Fetch Daily Data if not provided (for ATR, 20-day avg volume, previous close)
        if df_daily is None or df_daily.empty:
            try:
                stock = yf.Ticker(ticker)
                df_daily = stock.history(period="30d", interval="1d")
                if isinstance(df_daily.columns, pd.MultiIndex):
                    df_daily.columns = df_daily.columns.get_level_values(0)
            except Exception:
                return None

        if df_daily is None or len(df_daily) < 15:
            return None

        # Clean daily headers
        cols = {c.lower(): c for c in df_daily.columns}
        high_col = cols.get('high', 'High')
        low_col = cols.get('low', 'Low')
        close_col = cols.get('close', 'Close')
        open_col = cols.get('open', 'Open')
        vol_col = cols.get('volume', 'Volume')

        # Compute ATR (14 period)
        highs = df_daily[high_col].values
        lows = df_daily[low_col].values
        closes = df_daily[close_col].values
        volumes = df_daily[vol_col].values

        tr_list = []
        for i in range(1, len(df_daily)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
            tr_list.append(tr)

        atr = float(np.mean(tr_list[-14:])) if len(tr_list) >= 14 else float(np.mean(tr_list))
        avg_volume = int(np.mean(volumes[-20:])) if len(volumes) >= 20 else int(np.mean(volumes))
        prev_close = float(closes[-2]) if len(closes) >= 2 else float(closes[-1])

        # Current Price & Open
        if realtime_quote and realtime_quote.get("price") is not None:
            current_price = float(realtime_quote["price"])
        else:
            quote = self.quote_provider.get_quote(ticker)
            current_price = float(quote.get("price") or closes[-1])

        # Fallback open price
        open_price = float(df_daily[open_col].iloc[-1]) if open_col in df_daily.columns else prev_close
        current_volume = int(volumes[-1]) if len(volumes) > 0 else avg_volume

        # RVOL calculation (Current volume relative to expected proportion or full daily)
        rvol = (current_volume / avg_volume) if avg_volume > 0 else 1.0

        # Gap calculation
        gap_pct = ((open_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0.0

        # Intraday VWAP estimation
        vwap = (highs[-1] + lows[-1] + closes[-1]) / 3 if len(highs) > 0 else current_price
        if df_intraday is not None and not df_intraday.empty:
            try:
                i_high = df_intraday[cols.get('high', 'High')]
                i_low = df_intraday[cols.get('low', 'Low')]
                i_close = df_intraday[cols.get('close', 'Close')]
                i_vol = df_intraday[cols.get('volume', 'Volume')]
                typical_price = (i_high + i_low + i_close) / 3
                cum_vol = i_vol.cumsum()
                cum_pv = (typical_price * i_vol).cumsum()
                if cum_vol.iloc[-1] > 0:
                    vwap = float(cum_pv.iloc[-1] / cum_vol.iloc[-1])
            except Exception:
                pass

        vwap_distance_pct = ((current_price - vwap) / vwap) * 100 if vwap > 0 else 0.0
        atr_pct = (atr / current_price) * 100 if current_price > 0 else 0.0

        # 2. Composite Intraday Odds Scoring (0 - 100)
        # Components:
        # - Liquidity & Volume Surge (RVOL): 30 pts
        # - Daily Range & Volatility (ATR%): 25 pts
        # - Price Action / Gap Momentum: 25 pts
        # - VWAP Trend Alignment: 20 pts
        score = 0.0
        reasons = []

        # RVOL scoring
        if rvol >= 2.0:
            score += 30
            reasons.append(f"Exceptional relative volume (RVOL: {rvol:.2f}x)")
        elif rvol >= 1.3:
            score += 22
            reasons.append(f"Strong relative volume (RVOL: {rvol:.2f}x)")
        elif rvol >= 0.8:
            score += 15
        else:
            score += 5
            reasons.append(f"Subdued volume (RVOL: {rvol:.2f}x)")

        # ATR% scoring
        if 2.0 <= atr_pct <= 6.0:
            score += 25
            reasons.append(f"Ideal daytrading range (ATR: ${atr:.2f}, {atr_pct:.1f}%)")
        elif atr_pct > 6.0:
            score += 20
            reasons.append(f"Very high intraday volatility (ATR: ${atr:.2f}, {atr_pct:.1f}%)")
        elif atr_pct >= 1.0:
            score += 15
            reasons.append(f"Moderate range suitable for conservative scalps (ATR%: {atr_pct:.1f}%)")
        else:
            score += 5
            reasons.append(f"Low volatility range (ATR%: {atr_pct:.1f}%)")

        # Gap % scoring
        abs_gap = abs(gap_pct)
        if 1.0 <= abs_gap <= 5.0:
            score += 25
            direction = "Up" if gap_pct > 0 else "Down"
            reasons.append(f"Morning Catalyst Gap {direction} ({gap_pct:+.2f}%)")
        elif abs_gap > 5.0:
            score += 18
            reasons.append(f"Large gap subject to mean-reversion risk ({gap_pct:+.2f}%)")
        else:
            score += 10

        # VWAP Alignment scoring
        if 0.1 <= vwap_distance_pct <= 2.0:
            score += 20
            reasons.append(f"Holding clean bullish posture above VWAP (+{vwap_distance_pct:.2f}%)")
        elif -1.5 <= vwap_distance_pct < 0.1:
            score += 15
            reasons.append(f"Near VWAP pivot support/resistance ({vwap_distance_pct:+.2f}%)")
        else:
            score += 8

        intraday_score = round(min(100.0, max(0.0, score)), 1)

        # 3. Strategy Profile Eligibility
        profiles = []
        if atr_pct >= 2.5 and rvol >= 1.2:
            profiles.append("HIGH_RISK")
        if avg_volume >= 1_000_000 and 1.0 <= atr_pct <= 4.0:
            profiles.append("LOW_RISK")
        if not profiles:
            profiles.append("LOW_RISK" if atr_pct < 2.5 else "HIGH_RISK")

        return IntradayCandidate(
            ticker=ticker,
            current_price=round(current_price, 2),
            previous_close=round(prev_close, 2),
            open_price=round(open_price, 2),
            gap_pct=round(gap_pct, 2),
            rvol=round(rvol, 2),
            atr=round(atr, 2),
            atr_pct=round(atr_pct, 2),
            volume=current_volume,
            avg_volume=avg_volume,
            vwap=round(vwap, 2),
            vwap_distance_pct=round(vwap_distance_pct, 2),
            intraday_odds_score=intraday_score,
            suitable_profiles=profiles,
            reasons=reasons
        )

    def scout_market(
        self,
        tickers: Optional[List[str]] = None,
        top_n: int = 10,
        min_score: float = 40.0
    ) -> List[IntradayCandidate]:
        """
        Scouts and ranks the best intraday stocks from the target watchlist/universe.
        """
        universe = [t.upper() for t in (tickers or self.DEFAULT_UNIVERSE)]
        candidates: List[IntradayCandidate] = []

        print(f"{Fore.CYAN}🔎 Scouting {len(universe)} stocks for intraday opportunities...{Style.RESET_ALL}")

        for ticker in universe:
            try:
                candidate = self.compute_intraday_metrics(ticker)
                if candidate and candidate.intraday_odds_score >= min_score:
                    candidates.append(candidate)
            except Exception as e:
                continue

        # Sort descending by intraday odds score
        candidates.sort(key=lambda c: c.intraday_odds_score, reverse=True)
        return candidates[:top_n]
