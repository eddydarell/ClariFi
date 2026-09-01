from types import SimpleNamespace

import pandas as pd

from core.recommendation_validation import validate_forecast_evidence, validate_market_data


def make_strategy(action="BUY", timeframe="1 week"):
    return SimpleNamespace(
        action=action,
        timeframe=timeframe,
        decision_status="ACTIONABLE",
        gate_reasons=[],
        rationale=[],
    )


def make_forecast(directional_accuracy=0.60, observations=5):
    return {
        "forecasts": {
            "5": {
                "walk_forward": {
                    "drift": {
                        "directional_accuracy": directional_accuracy,
                        "observations": observations,
                    },
                    "moving_average": {
                        "directional_accuracy": directional_accuracy,
                        "observations": observations,
                    },
                }
            }
        }
    }


def test_passing_walk_forward_evidence_preserves_actionable_strategy():
    strategy = make_strategy()

    validation = validate_forecast_evidence(strategy, make_forecast())

    assert validation["status"] == "PASSED"
    assert strategy.action == "BUY"
    assert strategy.decision_status == "ACTIONABLE"


def test_failed_walk_forward_evidence_suppresses_strategy():
    strategy = make_strategy()
    strategy.optimal_moment = object()

    validation = validate_forecast_evidence(strategy, make_forecast(directional_accuracy=0.40))

    assert validation["status"] == "FAILED"
    assert strategy.action == "HOLD"
    assert strategy.decision_status == "SUPPRESSED"
    assert strategy.optimal_moment is None
    assert strategy.gate_reasons


def test_underpowered_walk_forward_evidence_suppresses_strategy():
    strategy = make_strategy()

    validation = validate_forecast_evidence(strategy, make_forecast(observations=2))

    assert validation["status"] == "INSUFFICIENT_EVIDENCE"
    assert strategy.action == "HOLD"


def make_market_data(index=None):
    if index is None:
        index = pd.date_range(end=pd.Timestamp.now(tz="UTC"), periods=2, freq="B")
    return pd.DataFrame({
        "Open": [100.0, 101.0], "High": [102.0, 103.0], "Low": [99.0, 100.0],
        "Close": [101.0, 102.0], "Volume": [1_000_000, 1_100_000],
    }, index=index)


def test_market_data_validation_accepts_complete_recent_ohlcv():
    validation = validate_market_data(make_market_data())

    assert validation["valid"] is True
    assert validation["status"] == "PASSED"


def test_market_data_validation_rejects_missing_or_invalid_prices():
    data = make_market_data().drop(columns=["Volume"])
    data.loc[data.index[0], "Close"] = 0

    validation = validate_market_data(data)

    assert validation["valid"] is False
    assert "Missing required OHLCV columns: Volume" in validation["reasons"]


def test_market_data_validation_rejects_stale_or_duplicate_bars():
    data = make_market_data(index=pd.DatetimeIndex(["2020-01-01", "2020-01-01"]))

    validation = validate_market_data(data)

    assert validation["valid"] is False
    assert "Market data contains duplicate timestamps" in validation["reasons"]