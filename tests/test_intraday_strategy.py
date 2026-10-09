#!/usr/bin/env python3
"""
Unit tests for Intraday Screening, Dual Strategy Generation, Simulator, and Live Monitor.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../core")))

from core.intraday_screener import IntradayScreener, IntradayCandidate
from core.intraday_strategy import (
    IntradayStrategyGenerator,
    DualIntradayReport,
    IntradayTradePlan,
)
from core.intraday_simulator import IntradaySimulator, SimulatedIntradayTrade
from core.intraday_monitor import IntradayLoopMonitor, MonitoredStockState
from core.engine import ClariFiEngine
from database.models import DatabaseManager


def make_synthetic_daily_data(
    start_price: float = 100.0, num_days: int = 30
) -> pd.DataFrame:
    """Generates synthetic OHLCV daily data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=num_days, freq="D")
    np.random.seed(42)

    closes = [start_price]
    for _ in range(num_days - 1):
        change = np.random.normal(0.002, 0.02)
        closes.append(closes[-1] * (1 + change))

    closes = np.array(closes)
    highs = closes * (1 + np.abs(np.random.normal(0.01, 0.005, num_days)))
    lows = closes * (1 - np.abs(np.random.normal(0.01, 0.005, num_days)))
    opens = (highs + lows) / 2
    volumes = np.random.randint(1_000_000, 5_000_000, size=num_days)

    df = pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": volumes,
            "Ticker": "TEST",
        },
        index=dates,
    )

    return df


class TestIntradayScreener:
    """Tests for Intraday candidate metrics and ranking."""

    def test_compute_intraday_metrics(self):
        screener = IntradayScreener()
        df = make_synthetic_daily_data(start_price=150.0, num_days=30)

        candidate = screener.compute_intraday_metrics(
            ticker="TEST",
            df_daily=df,
            realtime_quote={
                "price": 152.0,
                "provider": "mock",
                "freshness": "real_time",
            },
        )

        assert candidate is not None
        assert candidate.ticker == "TEST"
        assert candidate.current_price == 152.0
        assert candidate.atr > 0
        assert candidate.atr_pct > 0
        assert candidate.rvol > 0
        assert 0 <= candidate.intraday_odds_score <= 100
        assert len(candidate.suitable_profiles) > 0
        assert len(candidate.reasons) > 0

    def test_insufficient_data_returns_none(self):
        screener = IntradayScreener()
        df_small = make_synthetic_daily_data(start_price=100.0, num_days=5)

        candidate = screener.compute_intraday_metrics(ticker="TEST", df_daily=df_small)
        assert candidate is None


class TestIntradayStrategyGenerator:
    """Tests for Dual Strategy generation: High-Risk vs Low-Risk."""

    def test_dual_strategy_generation(self):
        screener = IntradayScreener()
        generator = IntradayStrategyGenerator(screener)
        df = make_synthetic_daily_data(start_price=200.0, num_days=30)

        candidate = screener.compute_intraday_metrics(
            ticker="NVDA", df_daily=df, realtime_quote={"price": 200.0}
        )
        assert candidate is not None

        report = generator.generate_strategies_for_candidate(candidate)

        assert isinstance(report, DualIntradayReport)
        assert report.ticker == "NVDA"
        assert report.current_price == 200.0

        # Validate High-Risk Strategy
        hr = report.high_risk_strategy
        assert isinstance(hr, IntradayTradePlan)
        assert hr.risk_profile == "HIGH_RISK"
        assert hr.action == "BUY"
        assert hr.entry_price == 200.0

        assert hr.stop_loss_price < 200.0
        assert hr.target_1_price > 200.0
        assert hr.risk_reward_ratio >= 1.8
        assert "15:55" in hr.evening_exit_time
        assert "09:30" in hr.entry_window

        # Validate Low-Risk Strategy
        lr = report.low_risk_strategy
        assert isinstance(lr, IntradayTradePlan)
        assert lr.risk_profile == "LOW_RISK"
        assert lr.action == "BUY"
        assert lr.entry_price == 200.0
        assert lr.stop_loss_price < 200.0
        assert lr.target_1_price > 200.0
        assert lr.stop_loss_pct < hr.stop_loss_pct  # Safer stop loss
        assert hr.target_1_pct > lr.target_1_pct  # Higher rewards for high risk
        assert "15:55" in lr.evening_exit_time

    def test_bearish_candidate_gets_short_plans(self):
        generator = IntradayStrategyGenerator()
        candidate = IntradayCandidate(
            ticker="TEST",
            current_price=100.0,
            previous_close=102.0,
            open_price=98.0,
            gap_pct=-1.96,
            rvol=1.8,
            atr=2.0,
            atr_pct=2.0,
            volume=2_000_000,
            avg_volume=1_000_000,
            vwap=101.0,
            vwap_distance_pct=-0.99,
            intraday_odds_score=70.0,
            suitable_profiles=["HIGH_RISK"],
        )
        report = generator.generate_strategies_for_candidate(candidate)
        assert report.high_risk_strategy.action == "SELL"
        assert report.high_risk_strategy.direction == "SHORT"
        assert report.high_risk_strategy.stop_loss_price > candidate.current_price
        assert report.high_risk_strategy.target_1_price < candidate.current_price


class TestIntradaySimulator:
    """Tests for simulated paper trade lifecycle and P&L tracking."""

    def test_paper_trade_lifecycle(self, tmp_path):
        db_file = str(tmp_path / "test_sim.db")
        db_mgr = DatabaseManager(db_file)
        sim = IntradaySimulator(db_mgr)

        plan = IntradayTradePlan(
            risk_profile="HIGH_RISK",
            ticker="AAPL",
            action="BUY",
            entry_price=100.0,
            entry_window="09:30 - 10:30",
            entry_condition="Breakout",
            stop_loss_price=97.0,
            stop_loss_pct=3.0,
            target_1_price=106.0,
            target_1_pct=6.0,
            target_2_price=110.0,
            target_2_pct=10.0,
            trailing_stop_activation_price=104.0,
            evening_exit_time="15:55 EST",
            risk_per_share=3.0,
            reward_per_share=6.0,
            risk_reward_ratio=2.0,
            position_sizing_pct=5.0,
        )

        # 1. Open Trade
        trade = sim.open_paper_trade(plan)
        assert trade.id in sim.active_trades
        assert trade.status == "OPEN"
        assert trade.ticker == "AAPL"

        # 2. Tick below Stop Loss triggers exit
        events = sim.update_with_tick("AAPL", 96.5)
        assert len(events) == 1
        assert events[0]["event"] == "STOP_LOSS_TRIGGERED"
        assert trade.id not in sim.active_trades
        assert len(sim.closed_trades) == 1
        assert sim.closed_trades[0].status == "STOP_HIT"
        assert sim.closed_trades[0].net_pnl_pct < 0

    def test_target_hit_simulation(self, tmp_path):
        db_file = str(tmp_path / "test_sim_target.db")
        db_mgr = DatabaseManager(db_file)
        sim = IntradaySimulator(db_mgr)

        plan = IntradayTradePlan(
            risk_profile="LOW_RISK",
            ticker="MSFT",
            action="BUY",
            entry_price=400.0,
            entry_window="09:30 - 10:30",
            entry_condition="VWAP bounce",
            stop_loss_price=395.0,
            stop_loss_pct=1.25,
            target_1_price=410.0,
            target_1_pct=2.5,
            target_2_price=415.0,
            target_2_pct=3.75,
            trailing_stop_activation_price=405.0,
            evening_exit_time="15:55 EST",
            risk_per_share=5.0,
            reward_per_share=10.0,
            risk_reward_ratio=2.0,
            position_sizing_pct=10.0,
        )

        trade = sim.open_paper_trade(plan)
        events = sim.update_with_tick("MSFT", 411.0)

        assert len(events) == 1
        assert events[0]["event"] == "TARGET_1_TRIGGERED"
        assert len(sim.closed_trades) == 1
        assert sim.closed_trades[0].status == "TARGET_HIT"
        assert sim.closed_trades[0].net_pnl_pct > 0

        # Performance summary
        perf = sim.get_performance_summary()
        assert perf["total_trades"] == 1
        assert perf["winning_trades"] == 1
        assert perf["win_rate_pct"] == 100.0
        assert perf["total_realized_pnl_pct"] > 0


class TestClariFiEngineIntegration:
    """Tests for ClariFiEngine intraday methods."""

    def test_engine_intraday_methods(self, tmp_path):
        db_file = str(tmp_path / "engine_test.db")
        engine = ClariFiEngine(db_file)

        assert hasattr(engine, "intraday_scout")
        assert hasattr(engine, "generate_intraday_strategies")
        assert hasattr(engine, "create_intraday_monitor")

        # Test strategy generation method
        res = engine.generate_intraday_strategies(["AAPL"])
        assert res["success"] is True
        assert "reports" in res
