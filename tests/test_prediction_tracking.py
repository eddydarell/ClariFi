import os
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.main import AdvancedStockAnalysis
from core.prediction_tracker import PredictionTracker
from core.strategy_analyzer import StrategyAnalyzer
from database.models import DatabaseManager


def make_price_data(start_price=100.0, daily_change_pct=5.0, num_days=120):
    import numpy as np
    from datetime import datetime

    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=num_days, freq='B')
    n = len(dates)
    trend = np.linspace(0, daily_change_pct * n / 100, n)
    noise = np.random.normal(0, 0.003, n)
    close = start_price * (1 + trend / 100 + noise)
    close = np.maximum(close, 1.0)
    return pd.DataFrame({
        'Open': close * (1 + np.random.uniform(-0.005, 0.005, n)),
        'High': close * (1 + np.abs(np.random.normal(0, 0.01, n))),
        'Low': close * (1 - np.abs(np.random.normal(0, 0.01, n))),
        'Close': close,
        'Volume': np.random.randint(1000000, 10000000, n),
    }, index=dates)


def test_analysis_persistence_helper_writes_prediction_rows(tmp_path):
    analysis = AdvancedStockAnalysis()
    data = make_price_data()
    strategy = StrategyAnalyzer().generate_strategy('TEST', data)
    db_path = tmp_path / 'test_predictions.db'
    db_manager = DatabaseManager(db_path=str(db_path))

    result = analysis._persist_prediction_tracking(
        ticker='TEST',
        entry_price=strategy.entry_price,
        predictions=strategy.predictions,
        db_manager=db_manager,
    )

    assert result['new_prediction_ids']
    assert len(result['new_prediction_ids']) == 5
    assert os.path.exists(db_path)

    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM ticker_predictions WHERE ticker = ?', ('TEST',))
        assert cursor.fetchone()[0] == 5


def test_tracker_persists_recommendation_provenance(tmp_path):
    data = make_price_data()
    strategy = StrategyAnalyzer().generate_strategy('TEST', data)
    db_manager = DatabaseManager(db_path=str(tmp_path / 'provenance.db'))
    tracker = PredictionTracker(db_manager)

    tracker.process_run(
        ticker='TEST', entry_price=strategy.entry_price, predictions=strategy.predictions,
        provenance={
            'decision_status': 'SUPPRESSED',
            'evidence_tags': ['trend_bullish', 'volatility_acceptable'],
            'data_quality': {'status': 'PASSED', 'valid': True},
            'empirical_validation': {'status': 'FAILED', 'actionable': False},
            'trade_plan_validation': {'status': 'NOT_APPLICABLE', 'actionable': False},
            'policy_version': 'swing-v1',
        },
    )

    with db_manager.get_connection() as conn:
        row = conn.execute('''
                 SELECT decision_status, evidence_tags, data_quality, empirical_validation,
                     trade_plan_validation, policy_version
            FROM ticker_predictions WHERE ticker = ? LIMIT 1
        ''', ('TEST',)).fetchone()

    assert row['decision_status'] == 'SUPPRESSED'
    assert row['policy_version'] == 'swing-v1'
    assert row['evidence_tags'] == '["trend_bullish", "volatility_acceptable"]'
    assert '"status": "PASSED"' in row['data_quality']
    assert '"status": "FAILED"' in row['empirical_validation']
    assert '"status": "NOT_APPLICABLE"' in row['trade_plan_validation']
