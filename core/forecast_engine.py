"""Small, auditable forecasting engine with walk-forward evaluation.

Models forecast close-to-close log returns. Prices are reconstructed only at the
boundary, avoiding the usual non-stationary raw-price target problem.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

try:
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class Forecast:
    model: str
    horizon: int
    predicted_return_pct: float
    predicted_price: float
    direction_probability: float | None
    interval_low_pct: float
    interval_high_pct: float
    training_observations: int


def _features(close: pd.Series) -> pd.DataFrame:
    returns = np.log(close / close.shift(1))
    frame = pd.DataFrame(index=close.index)
    for window in (1, 5, 10, 20):
        frame[f"return_{window}"] = returns.rolling(window).sum()
    frame["volatility_20"] = returns.rolling(20).std()
    frame["trend_20"] = close / close.rolling(20).mean() - 1
    return frame


def _walk_forward_metrics(returns: pd.Series, horizon: int, model: str) -> dict[str, float | int | None]:
    """Evaluate only matured, forward observations with a simple expanding window."""
    values = returns.dropna().to_numpy()
    minimum = max(40, horizon * 4)
    predictions: list[float] = []
    actuals: list[float] = []
    for end in range(minimum, len(values) - horizon + 1, horizon):
        train = values[:end]
        actual = float(values[end:end + horizon].sum())
        if model == "drift":
            prediction = float(train[-min(20, len(train)):].mean() * horizon)
        elif model == "moving_average":
            prediction = float(np.median(train[-min(20, len(train)):]) * horizon)
        else:
            prediction = 0.0
        predictions.append(prediction)
        actuals.append(actual)
    if not actuals:
        return {"observations": 0, "mae_pct": None, "directional_accuracy": None}
    pred = np.asarray(predictions)
    actual = np.asarray(actuals)
    return {
        "observations": len(actual),
        "mae_pct": float(np.mean(np.abs(pred - actual)) * 100),
        "directional_accuracy": float(np.mean(np.sign(pred) == np.sign(actual))),
    }


def forecast_prices(data: pd.DataFrame, ticker: str, horizons: tuple[int, ...] = (5, 20, 60)) -> dict[str, Any]:
    if "Close" not in data or len(data) < 40:
        raise ValueError("At least 40 close observations are required")
    close = pd.to_numeric(data["Close"], errors="coerce").dropna()
    if len(close) < 40:
        raise ValueError("At least 40 valid close observations are required")
    returns = np.log(close / close.shift(1)).dropna()
    features = _features(close)
    latest_price = float(close.iloc[-1])
    forecasts: dict[str, Any] = {}
    for horizon in horizons:
        recent = returns.tail(min(20, len(returns)))
        estimates: dict[str, float] = {
            "random_walk": 0.0,
            "drift": float(recent.mean() * horizon),
            "moving_average": float(recent.median() * horizon),
        }
        if SKLEARN_AVAILABLE and len(features.dropna()) > 50:
            # Train only on rows whose future label is available; latest row remains inference-only.
            clean = features.iloc[:-horizon].dropna()
            # Label row t with the next h trading-session returns, never the past.
            target = sum(returns.shift(-offset) for offset in range(1, horizon + 1))
            target = target.reindex(clean.index)
            valid = target.notna()
            if valid.sum() > 30:
                ridge = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
                ridge.fit(clean.loc[valid], target.loc[valid])
                estimates["ridge"] = float(ridge.predict(features.iloc[[-1]].fillna(0))[0])
                labels = (target.loc[valid] > 0).astype(int)
                if labels.nunique() > 1:
                    classifier = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500))
                    classifier.fit(clean.loc[valid], labels)
                    probability = float(classifier.predict_proba(features.iloc[[-1]].fillna(0))[0, 1])
                else:
                    probability = float(labels.iloc[0])
            else:
                probability = None
        else:
            probability = None
        volatility = float(returns.tail(min(60, len(returns))).std() * np.sqrt(horizon))
        model_scores = {name: _walk_forward_metrics(returns, horizon, name) for name in ("drift", "moving_average")}
        # Conservative ensemble: validated simple models first, with Ridge only when available.
        selected = [estimates["drift"], estimates["moving_average"]]
        if "ridge" in estimates:
            selected.append(estimates["ridge"])
        predicted = float(np.median(selected))
        forecasts[str(horizon)] = {
            "horizon_trading_days": horizon,
            "predicted_return_pct": predicted * 100,
            "predicted_price": latest_price * np.exp(predicted),
            "direction_probability": probability,
            "interval_low_pct": (predicted - 1.96 * volatility) * 100,
            "interval_high_pct": (predicted + 1.96 * volatility) * 100,
            "models": estimates,
            "walk_forward": model_scores,
        }
    return {
        "ticker": ticker.upper(),
        "as_of": close.index[-1],
        "current_price": latest_price,
        "target": "close_to_close_log_return",
        "frequency": "trading_day",
        "forecasts": forecasts,
        "methodology": ["random_walk", "rolling_drift", "rolling_median", "ridge_return", "logistic_direction"],
        "disclaimer": "Forecasts are experimental estimates, not financial advice.",
    }
