#!/usr/bin/env python3
"""
Prediction Tracker
Bridges StrategyAnalyzer's per-horizon predictions with the ticker_predictions
table: on every ticker run it resolves any previously-made predictions whose
target date has passed (scoring them against realized prices) and stores the
new 1-week/1-month/3-month/6-month/1-year predictions for future scoring.
"""

import os
import sys
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from database.models import DatabaseManager, TickerPrediction


class PredictionTracker:
    """Persists and scores forward-looking ticker predictions across runs."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        self.model = TickerPrediction(self.db)

    def _find_actual_price(self, ticker: str, target_date: str) -> Optional[float]:
        """Find the earliest recorded close price on/after the target date."""
        for row in self.db.get_ticker_prices(ticker):
            if row['price_date'] >= target_date and row.get('close') is not None:
                return float(row['close'])
        return None

    def resolve_due_predictions(self, ticker: str) -> List[Dict[str, Any]]:
        """Resolve predictions whose target date passed and for which we have price data."""
        resolved = []
        for due in self.model.get_due_predictions(ticker):
            actual_price = self._find_actual_price(ticker, due['target_date'])
            if actual_price is None:
                continue  # No market data yet on/after the target date
            outcome = self.model.resolve_prediction(
                prediction_id=due['id'],
                actual_price=actual_price,
                entry_price=due['entry_price'],
                predicted_trend=due['predicted_trend'],
                horizon=due['horizon'],
            )
            outcome.update({
                'horizon': due['horizon'],
                'target_date': due['target_date'],
                'predicted_price': due['predicted_price'],
                'predicted_trend': due['predicted_trend'],
            })
            resolved.append(outcome)
        return resolved

    def record_predictions(self, ticker: str, entry_price: float, predictions: Dict[str, Any],
                          run_id: Optional[str] = None) -> List[str]:
        """Persist the tracked horizons (1_week/1_month/3_month/6_month/1_year) from a run."""
        normalized: Dict[str, Dict[str, Any]] = {}
        for horizon in TickerPrediction.HORIZONS:
            pred = predictions.get(horizon)
            if pred is None:
                continue
            normalized[horizon] = asdict(pred) if is_dataclass(pred) else pred
        if not normalized:
            return []
        return self.model.save_predictions(ticker, entry_price, normalized, run_id=run_id)

    def process_run(self, ticker: str, entry_price: float, predictions: Dict[str, Any],
                    run_id: Optional[str] = None) -> Dict[str, Any]:
        """Resolve due predictions, record this run's new predictions, return a summary."""
        resolved = self.resolve_due_predictions(ticker)
        new_ids = self.record_predictions(ticker, entry_price, predictions, run_id=run_id)
        confidence = self.model.get_confidence_summary(ticker)
        return {
            "resolved": resolved,
            "new_prediction_ids": new_ids,
            "confidence": confidence,
        }
