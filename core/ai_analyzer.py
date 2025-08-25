#!/usr/bin/env python3
"""AI Analyzer for ClariFi

Provides an "ai" target that summarizes quantitative metrics, performs a very
lightweight heuristic backtest, and then asks a local Ollama model (qwen3:latest)
to synthesize BUY / SELL / HOLD recommendations for each ticker or an entire
portfolio.

Design goals:
  * Zero external service calls beyond yfinance + local Ollama.
  * Graceful degradation if Ollama or model missing.
  * Deterministic quantitative pre-summary + LLM qualitative overlay.
  * Simple backtesting (SMA crossover) to include performance differentials.

NOTE: This is NOT financial advice. Output is heuristic + LLM text.
"""
from __future__ import annotations

import os
import re
import json
import math
import textwrap
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None  # type: ignore

try:  # Optional dependency
    import ollama  # type: ignore
except ImportError:  # pragma: no cover
    ollama = None  # type: ignore


@dataclass
class BacktestResult:
    strategy_return_pct: float
    buy_hold_return_pct: float
    excess_return_pct: float
    trades: int
    win_rate_pct: float

    def to_dict(self):
        return asdict(self)


@dataclass
class TickerAnalysis:
    ticker: str
    period: str
    last_price: float
    avg_daily_return_pct: float
    vol_annualized_pct: float
    max_drawdown_pct: float
    sma50_vs_200_pct: float
    rsi_14: float
    ytd_return_pct: Optional[float]
    backtest: Optional[BacktestResult]
    quantitative_trend: str

    def to_dict(self):
        d = asdict(self)
        if self.backtest:
            d["backtest"] = self.backtest.to_dict()
        return d


RECOMMENDATION_REGEX = re.compile(r"\b(BUY|SELL|HOLD)\b", re.IGNORECASE)

# Structured response schema for consistent AI output
RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["tickers", "overall"],
    "properties": {
        "tickers": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["ticker", "recommendation", "rationale", "confidence"],
                "properties": {
                    "ticker": {"type": "string", "pattern": "^[A-Z]{1,6}$"},
                    "recommendation": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
                    "rationale": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 3
                    },
                    "confidence": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]}
                }
            }
        },
        "overall": {
            "type": "object",
            "required": ["stance", "notes", "market_outlook"],
            "properties": {
                "stance": {"type": "string", "enum": ["BULLISH", "BEARISH", "NEUTRAL"]},
                "notes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 3
                },
                "market_outlook": {"type": "string", "enum": ["FAVORABLE", "CAUTIOUS", "UNFAVORABLE"]}
            }
        }
    }
}


class AIAnalyzer:
    def __init__(self, model: str = "qwen3:latest"):
        self.model = model

    # -------------------------- Data Acquisition -------------------------- #
    def fetch_history(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        if yf is None:
            raise RuntimeError("yfinance not installed. Install dependencies first.")
        data = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        if data.empty:
            raise ValueError(f"No data returned for {ticker}")
        return data

    # -------------------------- Metric Computation ------------------------ #
    def compute_metrics(self, ticker: str, data: pd.DataFrame, period: str) -> TickerAnalysis:
        closes = data['Close'].dropna().copy()
        if closes.empty:
            raise ValueError(f"No closing prices for {ticker}")

        # Basic returns
        daily_ret = closes.pct_change().dropna()
        avg_daily = daily_ret.mean()
        vol_annualized = daily_ret.std() * math.sqrt(252)

        # Max drawdown
        roll_max = closes.cummax()
        dd = (closes / roll_max - 1).min()

        # Moving averages
        sma50 = closes.rolling(50).mean()
        sma200 = closes.rolling(200).mean()
        sma50_vs_200_pct = ((sma50.iloc[-1] / sma200.iloc[-1]) - 1) * 100 if (not np.isnan(sma50.iloc[-1]) and not np.isnan(sma200.iloc[-1])) else float('nan')

        # RSI (14)
        rsi_14 = self._rsi(closes, 14)

        # YTD return (approx if data spans year boundary)
        ytd_return = None
        if len(closes) > 250:  # timeframe likely includes YTD
            year_start = closes[closes.index.year == closes.index[-1].year]
            if not year_start.empty:
                ytd_return = (year_start.iloc[-1] / year_start.iloc[0] - 1) * 100

        # Simple backtest
        backtest = None
        try:
            backtest = self._sma_crossover_backtest(closes)
        except Exception:  # pragma: no cover - don't fail entire analysis
            backtest = None

        # Qualitative trend label
        quantitative_trend = self._trend_label(closes)

        return TickerAnalysis(
            ticker=ticker.upper(),
            period=period,
            last_price=float(closes.iloc[-1]),
            avg_daily_return_pct=avg_daily * 100,
            vol_annualized_pct=vol_annualized * 100,
            max_drawdown_pct=dd * 100,
            sma50_vs_200_pct=sma50_vs_200_pct,
            rsi_14=rsi_14,
            ytd_return_pct=ytd_return,
            backtest=backtest,
            quantitative_trend=quantitative_trend,
        )

    def _rsi(self, series: pd.Series, period: int = 14) -> float:
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        ema_up = up.ewm(com=period - 1, adjust=False).mean()
        ema_down = down.ewm(com=period - 1, adjust=False).mean()
        rs = ema_up / (ema_down + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not rsi.empty else float('nan')

    def _sma_crossover_backtest(self, closes: pd.Series, fast: int = 20, slow: int = 50) -> BacktestResult:
        if len(closes) < slow + 5:
            raise ValueError("Not enough data for backtest")
        sma_fast = closes.rolling(fast).mean()
        sma_slow = closes.rolling(slow).mean()
        signal = (sma_fast > sma_slow).astype(int)
        # Trade when signal changes
        position = signal.shift(1).fillna(0)
        strat_ret = position * closes.pct_change()
        buy_hold_ret = closes.pct_change()
        # Performance
        strategy_cum = (1 + strat_ret.fillna(0)).prod() - 1
        buy_hold_cum = (1 + buy_hold_ret.fillna(0)).prod() - 1
        trades = int((signal.diff().abs() == 1).sum())
        wins = int((strat_ret > 0).sum())
        total_trading_days = int((~strat_ret.isna()).sum())
        win_rate = wins / total_trading_days * 100 if total_trading_days else 0
        return BacktestResult(
            strategy_return_pct=strategy_cum * 100,
            buy_hold_return_pct=buy_hold_cum * 100,
            excess_return_pct=(strategy_cum - buy_hold_cum) * 100,
            trades=trades,
            win_rate_pct=win_rate,
        )

    def _trend_label(self, closes: pd.Series) -> str:
        if len(closes) < 30:
            return "INSUFFICIENT"
        recent = closes.tail(30)
        x = np.arange(len(recent))
        slope = np.polyfit(x, recent.values, 1)[0]
        slope_pct = slope / recent.mean()
        if slope_pct > 0.002:
            return "UP"
        if slope_pct < -0.002:
            return "DOWN"
        return "FLAT"

    # -------------------------- Prompt & LLM ------------------------------ #
    def build_prompt(self, analyses: List[TickerAnalysis]) -> str:
        """Build enhanced, structured prompt for consistent AI responses across models."""

        # Define the exact JSON schema in the prompt
        schema_str = json.dumps(RESPONSE_SCHEMA, indent=2)

        lines = [
            "=== FINANCIAL ANALYSIS TASK ===",
            "You are a professional equity analyst. Analyze the provided quantitative metrics and issue precise investment recommendations.",
            "",
            "=== INSTRUCTIONS ===",
            "1. For each ticker, provide exactly ONE recommendation: BUY, SELL, or HOLD",
            "2. Base decisions ONLY on the quantitative metrics provided below",
            "3. Consider these factors in order of importance:",
            "   - Trend direction and momentum (SMA crossover, RSI)",
            "   - Risk-adjusted returns (Sharpe ratio from daily returns vs volatility)",
            "   - Downside protection (max drawdown analysis)",
            "   - Backtest performance vs buy-and-hold",
            "4. Provide exactly 1-3 bullet points of rationale per ticker",
            "5. Assign confidence level: HIGH (clear signals), MEDIUM (mixed signals), LOW (insufficient data)",
            "",
            "=== OUTPUT FORMAT ===",
            "Respond with ONLY valid JSON matching this exact schema:",
            schema_str,
            "",
            "=== DECISION CRITERIA ===",
            "BUY: Strong uptrend + low drawdown + positive backtest excess returns + RSI < 70",
            "SELL: Clear downtrend + high drawdown + negative excess returns + RSI > 30",
            "HOLD: Mixed signals, insufficient data, or neutral conditions",
            "",
            "Overall stance: BULLISH (majority BUY), BEARISH (majority SELL), NEUTRAL (majority HOLD)",
            "Market outlook: FAVORABLE (low volatility + positive trends), CAUTIOUS (mixed), UNFAVORABLE (high vol + negative)",
            "",
            "=== QUANTITATIVE METRICS ==="
        ]

        for a in analyses:
            b = a.backtest
            # Calculate implied Sharpe ratio from daily returns
            sharpe_approx = (a.avg_daily_return_pct / (a.vol_annualized_pct / math.sqrt(252))) if a.vol_annualized_pct > 0 else 0

            lines.append(
                f"TICKER: {a.ticker}"
            )
            lines.append(
                f"  Trend: {a.quantitative_trend} | Price: ${a.last_price:.2f}"
            )
            lines.append(
                f"  Returns: Daily {a.avg_daily_return_pct:.2f}% | YTD {(a.ytd_return_pct if a.ytd_return_pct is not None else float('nan')):.2f}%"
            )
            lines.append(
                f"  Risk: Vol {a.vol_annualized_pct:.2f}% | MaxDD {a.max_drawdown_pct:.2f}% | Sharpe ~{sharpe_approx:.2f}"
            )
            lines.append(
                f"  Momentum: SMA50vs200 {a.sma50_vs_200_pct:.2f}% | RSI14 {a.rsi_14:.1f}"
            )
            if b:
                lines.append(
                    f"  Backtest: Strategy {b.strategy_return_pct:.2f}% vs BuyHold {b.buy_hold_return_pct:.2f}% | Excess {b.excess_return_pct:.2f}% | {b.trades} trades | {b.win_rate_pct:.1f}% win rate"
                )
            else:
                lines.append(
                    f"  Backtest: INSUFFICIENT_DATA"
                )
            lines.append("")  # Blank line between tickers

        lines.extend([
            "=== RESPONSE REQUIREMENTS ===",
            "- Return ONLY the JSON object, no additional text",
            "- Ensure all required fields are present",
            "- Use exact enum values specified in schema",
            "- Keep rationale concise and factual"
        ])

        return "\n".join(lines)

    def call_llm(self, prompt: str) -> str:
        """Call Ollama with enhanced system prompt for structured output."""
        if ollama is None:
            raise RuntimeError(
                "ollama python client not installed. Run 'pip install ollama' and ensure Ollama is running.\n"
                "Install Ollama: https://ollama.ai/\n"
                "Pull model: ollama pull qwen3:latest"
            )
        try:
            resp = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a disciplined financial analyst that ALWAYS responds with valid JSON. "
                            "Never include explanatory text outside the JSON structure. "
                            "Follow the exact schema provided in the user prompt. "
                            "Be precise, factual, and consistent in your analysis."
                        )
                    },
                    {"role": "user", "content": prompt},
                ],
                options={
                    "temperature": 0.1,  # Lower temperature for more consistent responses
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                },
            )
            return resp.get("message", {}).get("content", "")
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"Ollama invocation failed: {e}")

    def parse_recommendations(self, llm_text: str) -> Dict[str, Any]:
        """Enhanced parsing with schema validation."""
        # Clean the response text
        cleaned = llm_text.strip()

        # Remove any markdown code block markers
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Try to extract JSON
        json_start = cleaned.find('{')
        json_end = cleaned.rfind('}') + 1

        parsed_json = None
        validation_errors = []

        if json_start != -1 and json_end > json_start:
            try:
                json_text = cleaned[json_start:json_end]
                parsed_json = json.loads(json_text)

                # Basic schema validation
                validation_errors = self._validate_response_schema(parsed_json)

            except json.JSONDecodeError as e:
                validation_errors.append(f"JSON parsing error: {e}")
        else:
            validation_errors.append("No valid JSON found in response")

        # Fallback: regex extraction if JSON parsing fails
        if not parsed_json or validation_errors:
            parsed_json = self._fallback_parse(cleaned)
            if validation_errors:
                validation_errors.append("Used fallback parsing due to schema issues")

        return {
            "raw": llm_text,
            "parsed": parsed_json,
            "validation_errors": validation_errors
        }

    def _validate_response_schema(self, data: Dict[str, Any]) -> List[str]:
        """Basic validation of response against expected schema."""
        errors = []

        # Check top-level structure
        if not isinstance(data, dict):
            errors.append("Response must be a JSON object")
            return errors

        if "tickers" not in data:
            errors.append("Missing 'tickers' field")
        if "overall" not in data:
            errors.append("Missing 'overall' field")

        # Validate tickers array
        if "tickers" in data:
            if not isinstance(data["tickers"], list):
                errors.append("'tickers' must be an array")
            else:
                for i, ticker_obj in enumerate(data["tickers"]):
                    if not isinstance(ticker_obj, dict):
                        errors.append(f"Ticker {i} must be an object")
                        continue

                    required_fields = ["ticker", "recommendation", "rationale", "confidence"]
                    for field in required_fields:
                        if field not in ticker_obj:
                            errors.append(f"Ticker {i} missing '{field}' field")

                    # Validate recommendation enum
                    if "recommendation" in ticker_obj:
                        if ticker_obj["recommendation"] not in ["BUY", "SELL", "HOLD"]:
                            errors.append(f"Ticker {i} invalid recommendation: {ticker_obj['recommendation']}")

                    # Validate confidence enum
                    if "confidence" in ticker_obj:
                        if ticker_obj["confidence"] not in ["HIGH", "MEDIUM", "LOW"]:
                            errors.append(f"Ticker {i} invalid confidence: {ticker_obj['confidence']}")

        # Validate overall object
        if "overall" in data:
            overall = data["overall"]
            if not isinstance(overall, dict):
                errors.append("'overall' must be an object")
            else:
                required_fields = ["stance", "notes", "market_outlook"]
                for field in required_fields:
                    if field not in overall:
                        errors.append(f"Overall missing '{field}' field")

                # Validate stance enum
                if "stance" in overall:
                    if overall["stance"] not in ["BULLISH", "BEARISH", "NEUTRAL"]:
                        errors.append(f"Invalid overall stance: {overall['stance']}")

                # Validate market_outlook enum
                if "market_outlook" in overall:
                    if overall["market_outlook"] not in ["FAVORABLE", "CAUTIOUS", "UNFAVORABLE"]:
                        errors.append(f"Invalid market outlook: {overall['market_outlook']}")

        return errors

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback regex parsing when JSON parsing fails."""
        recs = []
        for line in text.splitlines():
            m = RECOMMENDATION_REGEX.search(line)
            if m:
                ticker_match = re.search(r"([A-Z]{1,6})", line)
                if ticker_match:
                    recs.append({
                        "ticker": ticker_match.group(1),
                        "recommendation": m.group(1).upper(),
                        "rationale": [line.strip()],
                        "confidence": "MEDIUM"  # Default fallback
                    })

        return {
            "tickers": recs,
            "overall": {
                "stance": "NEUTRAL",
                "notes": ["Fallback parsing used due to response format issues"],
                "market_outlook": "CAUTIOUS"
            }
        }

    # -------------------------- Public API ------------------------------- #
    def analyze(self, tickers: List[str], period: str = "1y", call_model: bool = True) -> Dict[str, Any]:
        analyses: List[TickerAnalysis] = []
        errors: Dict[str, str] = {}
        for t in tickers:
            try:
                data = self.fetch_history(t, period=period)
                analyses.append(self.compute_metrics(t, data, period))
            except Exception as e:
                errors[t.upper()] = str(e)
        prompt = self.build_prompt(analyses)
        llm_text = None
        parsed = None
        if call_model and analyses:
            try:
                llm_text = self.call_llm(prompt)
                parsed = self.parse_recommendations(llm_text)
            except Exception as e:
                errors['__llm__'] = str(e)
        return {
            "success": len(analyses) > 0,
            "analyses": [a.to_dict() for a in analyses],
            "prompt": prompt,
            "llm_raw": llm_text,
            "llm": parsed,
            "errors": errors,
        }


def is_probable_portfolio_identifier(value: str) -> bool:
    """Very light heuristic to detect if a single argument might be a portfolio id (UUID-like)."""
    return bool(re.fullmatch(r"[0-9a-fA-F-]{8,50}", value))


__all__ = [
    "AIAnalyzer",
    "TickerAnalysis",
    "BacktestResult",
    "is_probable_portfolio_identifier",
]
