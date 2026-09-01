"""Empirical validation gates for actionable strategy recommendations."""

from __future__ import annotations

from statistics import median
from typing import Any, Dict

import numpy as np
import pandas as pd


SWING_HORIZONS = {
    "2 days": 5,
    "5 days": 5,
    "1 week": 5,
    "2 weeks": 20,
    "1 month": 20,
    "2 months": 60,
}

REQUIRED_OHLCV_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


def validate_market_data(data: pd.DataFrame, max_age_days: int = 7) -> Dict[str, Any]:
    """Validate the minimum point-in-time OHLCV contract for a strategy run."""
    reasons: list[str] = []
    if data is None or data.empty:
        return {"status": "FAILED", "valid": False, "reasons": ["No market data is available"]}

    missing_columns = [column for column in REQUIRED_OHLCV_COLUMNS if column not in data.columns]
    if missing_columns:
        reasons.append(f"Missing required OHLCV columns: {', '.join(missing_columns)}")
        return {"status": "FAILED", "valid": False, "reasons": reasons}

    index = pd.to_datetime(data.index, errors="coerce")
    if index.isna().any():
        reasons.append("Market data contains invalid timestamps")
    elif index.has_duplicates:
        reasons.append("Market data contains duplicate timestamps")
    elif not index.is_monotonic_increasing:
        reasons.append("Market data timestamps are not ordered")
    else:
        latest_date = index.max().date()
        age_days = (pd.Timestamp.now(tz="UTC").date() - latest_date).days
        if max_age_days and age_days > max_age_days:
            reasons.append(f"Latest market bar is stale ({age_days} days old; maximum {max_age_days})")

    prices = data.loc[:, ("Open", "High", "Low", "Close")].apply(pd.to_numeric, errors="coerce")
    if prices.isna().any().any() or not np.isfinite(prices.to_numpy()).all():
        reasons.append("Market data contains missing or non-finite prices")
    elif (prices <= 0).any().any():
        reasons.append("Market data contains zero or negative prices")
    elif (prices["High"] < prices["Low"]).any():
        reasons.append("Market data contains rows where High is below Low")

    volume = pd.to_numeric(data["Volume"], errors="coerce")
    if volume.isna().any() or not np.isfinite(volume.to_numpy()).all() or (volume < 0).any():
        reasons.append("Market data contains invalid volume")

    return {
        "status": "PASSED" if not reasons else "FAILED",
        "valid": not reasons,
        "data_as_of": index.max().strftime("%Y-%m-%d") if not index.isna().all() else None,
        "reasons": reasons,
    }


def validate_forecast_evidence(
    strategy: Any,
    forecast: Dict[str, Any],
    minimum_observations: int = 3,
    minimum_directional_accuracy: float = 0.55,
) -> Dict[str, Any]:
    """Suppress actionable calls without adequate walk-forward support."""
    if strategy.action not in {"BUY", "SELL"}:
        return {"status": "NOT_APPLICABLE", "actionable": False, "reasons": []}

    horizon = SWING_HORIZONS.get(strategy.timeframe, 5)
    forecast_for_horizon = forecast.get("forecasts", {}).get(str(horizon))
    if not forecast_for_horizon:
        return _suppress(strategy, horizon, ["No walk-forward forecast evidence is available"])

    metrics = forecast_for_horizon.get("walk_forward", {})
    observations = [metric.get("observations", 0) for metric in metrics.values()]
    accuracies = [
        metric["directional_accuracy"]
        for metric in metrics.values()
        if metric.get("directional_accuracy") is not None
    ]
    if not observations or min(observations) < minimum_observations:
        return _suppress(
            strategy,
            horizon,
            [f"Insufficient walk-forward observations (minimum {minimum_observations})"],
            metrics,
        )
    if not accuracies:
        return _suppress(strategy, horizon, ["Walk-forward directional accuracy is unavailable"], metrics)

    directional_accuracy = float(median(accuracies))
    validation = {
        "status": "PASSED" if directional_accuracy >= minimum_directional_accuracy else "FAILED",
        "actionable": directional_accuracy >= minimum_directional_accuracy,
        "horizon_trading_days": horizon,
        "minimum_observations": minimum_observations,
        "minimum_directional_accuracy": minimum_directional_accuracy,
        "directional_accuracy": directional_accuracy,
        "walk_forward": metrics,
        "reasons": [],
    }
    if validation["actionable"]:
        return validation

    validation["reasons"] = [
        "Walk-forward directional accuracy "
        f"({directional_accuracy:.0%}) is below the required {minimum_directional_accuracy:.0%}"
    ]
    return _suppress(strategy, horizon, validation["reasons"], metrics, validation)


def validate_trade_plan(strategy: Any) -> Dict[str, Any]:
    """Suppress actionable strategies without a valid bounded trade plan."""
    if strategy.action not in {"BUY", "SELL"}:
        return {"status": "NOT_APPLICABLE", "actionable": False, "reasons": []}
    plan = strategy.trade_plan
    if plan is None:
        return _suppress_trade_plan(strategy, ["No trade plan is available"])
    if plan.valid:
        return {
            "status": "PASSED",
            "actionable": True,
            "risk_reward_ratio": plan.risk_reward_ratio,
            "reasons": [],
        }
    return _suppress_trade_plan(strategy, plan.reasons)


def _suppress_trade_plan(strategy: Any, reasons: list[str]) -> Dict[str, Any]:
    strategy.action = "HOLD"
    strategy.decision_status = "SUPPRESSED"
    strategy.optimal_moment = None
    strategy.gate_reasons.extend(reasons)
    strategy.rationale.extend(reasons)
    return {"status": "FAILED", "actionable": False, "reasons": reasons}


def _suppress(
    strategy: Any,
    horizon: int,
    reasons: list[str],
    metrics: Dict[str, Any] | None = None,
    validation: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    validation = validation or {
        "status": "INSUFFICIENT_EVIDENCE",
        "actionable": False,
        "horizon_trading_days": horizon,
        "walk_forward": metrics or {},
        "reasons": reasons,
    }
    strategy.action = "HOLD"
    strategy.decision_status = "SUPPRESSED"
    strategy.optimal_moment = None
    strategy.gate_reasons.extend(reasons)
    strategy.rationale.extend(reasons)
    return validation