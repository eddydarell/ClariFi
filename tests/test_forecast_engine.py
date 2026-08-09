import numpy as np
import pandas as pd

from core.forecast_engine import forecast_prices
from core.result_schema import envelope, strict_json


def test_forecast_keeps_latest_row_for_inference_and_returns_intervals():
    close = pd.Series(np.linspace(100, 120, 140), index=pd.date_range("2020-01-01", periods=140, freq="B"))
    result = forecast_prices(pd.DataFrame({"Close": close}), "TEST", (5, 20))

    assert result["current_price"] == 120
    assert set(result["forecasts"]) == {"5", "20"}
    assert result["forecasts"]["5"]["interval_low_pct"] <= result["forecasts"]["5"]["predicted_return_pct"]


def test_envelope_is_strict_json_and_normalizes_non_finite_values():
    result = envelope("test", {"value": float("nan")})
    assert result["data"]["value"] is None
    strict_json(result)
