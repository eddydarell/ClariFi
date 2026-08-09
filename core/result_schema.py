"""Canonical result envelopes and strict JSON conversion for public boundaries."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from typing import Any, Iterable, Optional

import numpy as np
import pandas as pd

SCHEMA_VERSION = "clarifi.result.v1"


def to_jsonable(value: Any) -> Any:
    """Convert supported scientific Python values without hiding schema errors."""
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, (datetime, date, pd.Timestamp)):
        timestamp = pd.Timestamp(value)
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        return timestamp.isoformat().replace("+00:00", "Z")
    if isinstance(value, pd.DataFrame):
        return to_jsonable(value.to_dict(orient="records"))
    if isinstance(value, pd.Series):
        return to_jsonable(value.to_dict())
    if isinstance(value, np.ndarray):
        return to_jsonable(value.tolist())
    if isinstance(value, np.generic):
        return to_jsonable(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"Unsupported JSON value: {type(value).__name__}")


def error_item(message: str, code: str = "ERROR", component: Optional[str] = None,
               ticker: Optional[str] = None, retryable: bool = False) -> dict[str, Any]:
    item: dict[str, Any] = {"code": code, "message": message, "retryable": retryable}
    if component:
        item["component"] = component
    if ticker:
        item["ticker"] = ticker
    return item


def envelope(operation: str, data: Any = None, errors: Optional[Iterable[dict[str, Any]]] = None,
             warnings: Optional[Iterable[str]] = None, meta: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    errors_list = list(errors or [])
    result = {
        "schema_version": SCHEMA_VERSION,
        "operation": operation,
        "status": "error" if errors_list and data is None else "partial" if errors_list else "ok",
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat().replace("+00:00", "Z"),
        "data": to_jsonable(data),
        "errors": to_jsonable(errors_list),
        "meta": to_jsonable({**(meta or {}), "warnings": list(warnings or [])}),
    }
    strict_json(result)
    return result


def strict_json(value: Any) -> str:
    """Validate and return strict JSON; NaN/Infinity and unknown objects are rejected."""
    return json.dumps(to_jsonable(value), allow_nan=False, separators=(",", ":"))
