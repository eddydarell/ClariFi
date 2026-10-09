"""Point-in-time quantitative momentum research and portfolio construction.

This module deliberately does not download data. Keeping data acquisition out of
the strategy makes look-ahead tests deterministic and makes provider provenance
the caller's responsibility.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import sqrt
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MomentumConfig:
    lookbacks: Tuple[int, ...] = (63, 126, 252)
    lookback_weights: Tuple[float, ...] = (0.20, 0.30, 0.50)
    skip_sessions: int = 21
    volatility_lookback: int = 63
    minimum_annualized_volatility: float = 0.10
    entry_percentile: float = 0.90
    retention_percentile: float = 0.70
    maximum_positions: int = 20
    maximum_position_weight: float = 0.10
    target_portfolio_volatility: float = 0.12
    minimum_price: float = 5.0
    minimum_dollar_volume: float = 10_000_000.0
    one_way_cost_bps: float = 10.0
    benchmark: str = "SPY"

    def __post_init__(self) -> None:
        if len(self.lookbacks) != len(self.lookback_weights):
            raise ValueError("lookbacks and lookback_weights must have equal length")
        if any(lookback <= 0 for lookback in self.lookbacks):
            raise ValueError("lookbacks must be positive")
        if self.skip_sessions < 0 or self.volatility_lookback < 2:
            raise ValueError(
                "skip_sessions must be non-negative and volatility_lookback >= 2"
            )
        if not 0 < self.retention_percentile <= self.entry_percentile <= 1:
            raise ValueError(
                "percentile thresholds must satisfy 0 < retention <= entry <= 1"
            )
        if self.maximum_positions < 1 or not 0 < self.maximum_position_weight <= 1:
            raise ValueError("position limits are invalid")
        if self.one_way_cost_bps < 0:
            raise ValueError("one_way_cost_bps must be non-negative")


@dataclass
class MomentumSignal:
    ticker: str
    as_of: str
    eligible: bool = False
    exclusion_reasons: List[str] = field(default_factory=list)
    returns: Dict[str, float] = field(default_factory=dict)
    volatility: Optional[float] = None
    raw_score: Optional[float] = None
    risk_adjusted_score: Optional[float] = None
    percentile_rank: Optional[float] = None
    above_sma_200: Optional[bool] = None
    confidence_score: float = 0.0
    confidence: str = "LOW"


@dataclass
class MomentumBacktestResult:
    strategy_id: str
    period_start: Optional[str]
    period_end: Optional[str]
    gross_return_pct: float
    net_return_pct: float
    benchmark_return_pct: float
    cagr_pct: Optional[float]
    volatility_pct: Optional[float]
    sharpe: Optional[float]
    sortino: Optional[float]
    max_drawdown_pct: float
    alpha_pct: Optional[float]
    beta: Optional[float]
    tracking_error_pct: Optional[float]
    information_ratio: Optional[float]
    monthly_hit_rate_pct: Optional[float]
    average_turnover_pct: float
    rebalances: int
    trades: int
    warnings: List[str] = field(default_factory=list)


def _series(frame: pd.DataFrame) -> pd.Series:
    column = "Adj Close" if "Adj Close" in frame.columns else "Close"
    if column not in frame.columns:
        raise ValueError("price frame requires Close or Adj Close")
    result = pd.to_numeric(frame[column], errors="coerce")
    result.index = pd.to_datetime(result.index)
    return result.sort_index().loc[~result.index.duplicated(keep="last")]


def _as_of_frame(frame: pd.DataFrame, as_of: Optional[pd.Timestamp]) -> pd.DataFrame:
    result = frame.copy()
    result.index = pd.to_datetime(result.index)
    result = result.sort_index().loc[~result.index.duplicated(keep="last")]
    if as_of is not None:
        result = result.loc[result.index <= as_of]
    return result


def _zscore(values: Mapping[str, float]) -> Dict[str, float]:
    if not values:
        return {}
    series = pd.Series(values, dtype=float)
    lower, upper = series.quantile(0.05), series.quantile(0.95)
    clipped = series.clip(lower=lower, upper=upper)
    std = float(clipped.std(ddof=0))
    if not np.isfinite(std) or std == 0:
        return {key: 0.0 for key in values}
    mean = float(clipped.mean())
    return {key: float((value - mean) / std) for key, value in clipped.items()}


def _signal_date(
    frame: pd.DataFrame, as_of: Optional[pd.Timestamp]
) -> Optional[pd.Timestamp]:
    prices = _as_of_frame(frame, as_of)
    return prices.index[-1] if not prices.empty else None


def _eligible_signal(
    ticker: str,
    frame: pd.DataFrame,
    as_of: Optional[pd.Timestamp],
    config: MomentumConfig,
) -> MomentumSignal:
    frame = _as_of_frame(frame, as_of)
    date = (
        frame.index[-1]
        if not frame.empty
        else pd.Timestamp(as_of or pd.Timestamp.utcnow())
    )
    signal = MomentumSignal(ticker=ticker, as_of=date.isoformat())
    prices = _series(frame)
    required = max(config.lookbacks) + config.skip_sessions + 1
    if len(prices.dropna()) < required:
        signal.exclusion_reasons.append(f"insufficient_history:{required}")
        return signal
    if prices.isna().tail(required).any():
        signal.exclusion_reasons.append("missing_price_history")
        return signal
    current = float(prices.iloc[-1])
    if not np.isfinite(current) or current < config.minimum_price:
        signal.exclusion_reasons.append("price_below_minimum")
    volume = pd.to_numeric(
        frame.get("Volume", pd.Series(index=frame.index)), errors="coerce"
    )
    dollar_volume = (prices * volume).tail(20).median()
    if not np.isfinite(dollar_volume) or dollar_volume < config.minimum_dollar_volume:
        signal.exclusion_reasons.append("dollar_volume_below_minimum")
    if signal.exclusion_reasons:
        return signal

    skipped = len(prices) - 1 - config.skip_sessions
    for lookback in config.lookbacks:
        numerator = float(prices.iloc[skipped])
        denominator = float(prices.iloc[skipped - lookback])
        signal.returns[f"{lookback}_1"] = numerator / denominator - 1.0
    returns = prices.pct_change().dropna().tail(config.volatility_lookback)
    signal.volatility = float(returns.std(ddof=1) * sqrt(252))
    signal.volatility = max(signal.volatility, config.minimum_annualized_volatility)
    sma_index = skipped
    signal.above_sma_200 = bool(
        prices.iloc[sma_index]
        > prices.iloc[max(0, sma_index - 199) : sma_index + 1].mean()
    )
    signal.eligible = True
    return signal


def compute_signals(
    price_frames: Mapping[str, pd.DataFrame],
    as_of: Optional[str | pd.Timestamp] = None,
    config: MomentumConfig = MomentumConfig(),
) -> List[MomentumSignal]:
    """Compute cross-sectional momentum signals using only data up to ``as_of``."""
    cutoff = pd.Timestamp(as_of) if as_of is not None else None
    signals = [
        _eligible_signal(str(ticker).upper(), frame, cutoff, config)
        for ticker, frame in price_frames.items()
    ]
    eligible = [signal for signal in signals if signal.eligible]
    horizon_zscores: Dict[str, Dict[str, float]] = {}
    for key in (f"{lookback}_1" for lookback in config.lookbacks):
        horizon_zscores[key] = _zscore(
            {signal.ticker: signal.returns[key] for signal in eligible}
        )
    raw = {
        signal.ticker: sum(
            weight * horizon_zscores[f"{lookback}_1"][signal.ticker]
            for lookback, weight in zip(config.lookbacks, config.lookback_weights)
        )
        for signal in eligible
    }
    adjusted = {
        signal.ticker: raw[signal.ticker]
        / max(signal.volatility or 0.0, config.minimum_annualized_volatility)
        for signal in eligible
    }
    adjusted_z = _zscore(adjusted)
    ranks = (
        pd.Series(adjusted_z, dtype=float).rank(pct=True, method="first")
        if adjusted_z
        else pd.Series(dtype=float)
    )
    for signal in eligible:
        signal.raw_score = float(raw[signal.ticker])
        signal.risk_adjusted_score = float(adjusted_z[signal.ticker])
        signal.percentile_rank = float(ranks[signal.ticker])
        signal.confidence_score = float(
            100
            * (
                0.60 * signal.percentile_rank
                + 0.40 * (1.0 if signal.above_sma_200 else 0.0)
            )
        )
        signal.confidence = (
            "HIGH"
            if signal.confidence_score >= 75
            else "MEDIUM"
            if signal.confidence_score >= 55
            else "LOW"
        )
    return sorted(
        signals,
        key=lambda signal: (signal.percentile_rank or 0.0, signal.ticker),
        reverse=True,
    )


def market_regime(benchmark_frame: pd.DataFrame) -> str:
    prices = _series(benchmark_frame).dropna()
    if len(prices) < 200:
        return "UNKNOWN"
    sma_50 = float(prices.iloc[-50:].mean())
    sma_200 = float(prices.iloc[-200:].mean())
    above_200 = float(prices.iloc[-1]) > sma_200
    fast_above_slow = sma_50 > sma_200
    if above_200 and fast_above_slow:
        return "RISK_ON"
    if above_200 or fast_above_slow:
        return "NEUTRAL"
    return "RISK_OFF"


def build_target_portfolio(
    signals: Sequence[MomentumSignal],
    benchmark_frame: pd.DataFrame,
    previous_weights: Optional[Mapping[str, float]] = None,
    config: MomentumConfig = MomentumConfig(),
) -> Dict[str, Any]:
    """Build a long-only target; shorting remains a separate, explicit strategy."""
    previous = dict(previous_weights or {})
    regime = market_regime(benchmark_frame)
    gross_limit = {"RISK_ON": 1.0, "NEUTRAL": 0.5, "RISK_OFF": 0.0}.get(regime, 0.0)
    eligible = {signal.ticker: signal for signal in signals if signal.eligible}
    selected = [
        signal
        for signal in signals
        if signal.eligible
        and (
            (signal.percentile_rank or 0.0) >= config.entry_percentile
            or (
                signal.ticker in previous
                and (signal.percentile_rank or 0.0) >= config.retention_percentile
            )
        )
        and signal.above_sma_200
    ]
    selected = selected[: config.maximum_positions]
    weights: Dict[str, float] = {}
    if gross_limit and selected:
        inverse_vol = {
            signal.ticker: 1.0
            / max(signal.volatility or 0.0, config.minimum_annualized_volatility)
            for signal in selected
        }
        total = sum(inverse_vol.values())
        weights = {
            ticker: gross_limit * value / total for ticker, value in inverse_vol.items()
        }
        for _ in range(10):
            excess = sum(
                max(weight - config.maximum_position_weight, 0.0)
                for weight in weights.values()
            )
            capped = {
                ticker: min(weight, config.maximum_position_weight)
                for ticker, weight in weights.items()
            }
            uncapped = [
                ticker
                for ticker, weight in weights.items()
                if weight < config.maximum_position_weight
            ]
            if excess <= 1e-12 or not uncapped:
                weights = capped
                break
            share = excess / len(uncapped)
            weights = {
                ticker: capped[ticker] + (share if ticker in uncapped else 0.0)
                for ticker in weights
            }
    turnover = sum(
        abs(weights.get(ticker, 0.0) - previous.get(ticker, 0.0))
        for ticker in set(weights) | set(previous)
    )
    actions = [
        {
            "ticker": ticker,
            "target_weight": round(weight, 8),
            "action": "BUY" if weight > previous.get(ticker, 0) else "SELL",
        }
        for ticker, weight in sorted(weights.items())
    ]
    return {
        "regime": regime,
        "gross_exposure": float(sum(weights.values())),
        "cash_weight": float(max(0.0, 1.0 - sum(weights.values()))),
        "turnover": float(turnover),
        "estimated_cost_pct": float(turnover * config.one_way_cost_bps / 10000.0),
        "positions": actions,
        "excluded": [
            {"ticker": signal.ticker, "reasons": signal.exclusion_reasons}
            for signal in signals
            if not signal.eligible
        ],
    }


def _metrics(
    strategy_returns: pd.Series, benchmark_returns: pd.Series
) -> Dict[str, Optional[float]]:
    strategy_returns = strategy_returns.dropna()
    benchmark_returns = benchmark_returns.reindex(strategy_returns.index).fillna(0.0)
    if strategy_returns.empty:
        return {
            key: None
            for key in (
                "cagr_pct",
                "volatility_pct",
                "sharpe",
                "sortino",
                "alpha_pct",
                "beta",
                "tracking_error_pct",
                "information_ratio",
                "monthly_hit_rate_pct",
            )
        }
    years = max(len(strategy_returns) / 12.0, 1 / 12)
    cumulative = float((1 + strategy_returns).prod())
    excess = strategy_returns - benchmark_returns
    variance = (
        float(benchmark_returns.var(ddof=1)) if len(benchmark_returns) > 1 else 0.0
    )
    beta = (
        float(strategy_returns.cov(benchmark_returns) / variance)
        if variance > 0
        else None
    )
    alpha = float(
        (strategy_returns.mean() - (beta or 0.0) * benchmark_returns.mean()) * 12 * 100
    )
    tracking = float(excess.std(ddof=1) * sqrt(12)) if len(excess) > 1 else 0.0
    return {
        "cagr_pct": (cumulative ** (1 / years) - 1) * 100,
        "volatility_pct": float(strategy_returns.std(ddof=1) * sqrt(12) * 100)
        if len(strategy_returns) > 1
        else 0.0,
        "sharpe": float(
            strategy_returns.mean() / strategy_returns.std(ddof=1) * sqrt(12)
        )
        if len(strategy_returns) > 1 and strategy_returns.std(ddof=1)
        else None,
        "sortino": float(
            strategy_returns.mean()
            / strategy_returns[strategy_returns < 0].std(ddof=1)
            * sqrt(12)
        )
        if len(strategy_returns[strategy_returns < 0]) > 1
        and strategy_returns[strategy_returns < 0].std(ddof=1)
        else None,
        "alpha_pct": alpha,
        "beta": beta,
        "tracking_error_pct": tracking * 100,
        "information_ratio": float(excess.mean() / excess.std(ddof=1) * sqrt(12))
        if len(excess) > 1 and excess.std(ddof=1)
        else None,
        "monthly_hit_rate_pct": float((strategy_returns > 0).mean() * 100),
    }


def backtest(
    price_frames: Mapping[str, pd.DataFrame],
    benchmark_frame: pd.DataFrame,
    config: MomentumConfig = MomentumConfig(),
) -> MomentumBacktestResult:
    """Run a monthly next-open walk-forward backtest with explicit costs."""
    benchmark_prices = _series(benchmark_frame).dropna()
    dates = (
        benchmark_prices.groupby(benchmark_prices.index.to_period("M")).tail(1).index
    )
    portfolio_returns: List[float] = []
    gross_returns: List[float] = []
    benchmark_returns: List[float] = []
    turnover_values: List[float] = []
    previous: Dict[str, float] = {}
    trades = 0
    warnings: List[str] = []
    for signal_date in dates[:-1]:
        next_dates = benchmark_prices.index[benchmark_prices.index > signal_date]
        if len(next_dates) == 0:
            continue
        execution_date = next_dates[0]
        future_dates = benchmark_prices.index[benchmark_prices.index >= execution_date]
        next_rebalance = dates[dates > signal_date]
        end_date = next_rebalance[0] if len(next_rebalance) else future_dates[-1]
        signals = compute_signals(price_frames, as_of=signal_date, config=config)
        target = build_target_portfolio(
            signals, benchmark_frame.loc[:signal_date], previous, config
        )
        weights = {
            position["ticker"]: position["target_weight"]
            for position in target["positions"]
        }
        turnover_values.append(float(target["turnover"]))
        trades += sum(
            1
            for ticker in set(weights) | set(previous)
            if abs(weights.get(ticker, 0) - previous.get(ticker, 0)) > 1e-10
        )
        period_returns = []
        for ticker, weight in weights.items():
            frame = _as_of_frame(price_frames[ticker], end_date)
            prices = _series(frame)
            start = prices[prices.index >= execution_date]
            finish = prices[prices.index <= end_date]
            if not start.empty and not finish.empty and float(start.iloc[0]) > 0:
                period_returns.append(
                    weight * (float(finish.iloc[-1]) / float(start.iloc[0]) - 1.0)
                )
        gross = sum(period_returns)
        net = gross - target["estimated_cost_pct"]
        gross_returns.append(gross)
        portfolio_returns.append(net)
        bench_start = benchmark_prices[benchmark_prices.index >= execution_date]
        bench_end = benchmark_prices[benchmark_prices.index <= end_date]
        if not bench_start.empty and not bench_end.empty:
            benchmark_returns.append(
                float(bench_end.iloc[-1]) / float(bench_start.iloc[0]) - 1.0
            )
        else:
            benchmark_returns.append(0.0)
        previous = weights
    strategy_series = pd.Series(portfolio_returns, dtype=float)
    benchmark_series = pd.Series(benchmark_returns, dtype=float)
    metrics = _metrics(strategy_series, benchmark_series)
    curve = (
        (1 + strategy_series).cumprod()
        if not strategy_series.empty
        else pd.Series(dtype=float)
    )
    drawdown = curve / curve.cummax() - 1 if not curve.empty else pd.Series([0.0])
    gross_return = (
        float((1 + pd.Series(gross_returns, dtype=float)).prod() - 1)
        if gross_returns
        else 0.0
    )
    benchmark_return = (
        float((1 + benchmark_series).prod() - 1) if not benchmark_series.empty else 0.0
    )
    return MomentumBacktestResult(
        strategy_id="cross_sectional_momentum_12_1_v1",
        period_start=str(dates[0].date()) if len(dates) else None,
        period_end=str(dates[-1].date()) if len(dates) else None,
        gross_return_pct=gross_return * 100,
        net_return_pct=float((1 + strategy_series).prod() - 1) * 100
        if not strategy_series.empty
        else 0.0,
        benchmark_return_pct=benchmark_return * 100,
        max_drawdown_pct=float(drawdown.min() * 100),
        average_turnover_pct=float(np.mean(turnover_values) * 100)
        if turnover_values
        else 0.0,
        rebalances=len(portfolio_returns),
        trades=trades,
        warnings=warnings,
        **metrics,
    )


def signal_dict(signal: MomentumSignal) -> Dict[str, Any]:
    return asdict(signal)


def result_dict(result: MomentumBacktestResult) -> Dict[str, Any]:
    return asdict(result)
