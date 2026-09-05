#!/usr/bin/env python3
"""
Unit tests for Autonomous AI Intraday Trading Agent.
"""

import os
import sys
import pytest
from datetime import datetime

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../core')))

from core.intraday_agent import AutonomousIntradayAgent, IntradayAgentContext, AgentDecision
from core.intraday_strategy import IntradayTradePlan


@pytest.fixture
def sample_trade_plan():
    return IntradayTradePlan(
        risk_profile="HIGH_RISK",
        ticker="AAPL",
        action="BUY",
        entry_price=100.0,
        entry_window="09:30 - 10:45 EST",
        entry_condition="Breakout above $100.00 with volume",
        stop_loss_price=97.0,
        stop_loss_pct=3.0,
        target_1_price=105.0,
        target_1_pct=5.0,
        target_2_price=108.0,
        target_2_pct=8.0,
        trailing_stop_activation_price=103.0,
        evening_exit_time="15:55 EST",
        risk_per_share=3.0,
        reward_per_share=5.0,
        risk_reward_ratio=1.67,
        position_sizing_pct=5.0
    )


class TestAutonomousIntradayAgent:
    """Tests evaluating autonomous decision making across intraday states."""

    def test_buy_entry_decision(self, sample_trade_plan):
        agent = AutonomousIntradayAgent()
        ctx = IntradayAgentContext(
            ticker="AAPL",
            current_price=100.5,
            previous_price=99.8,
            high_price=100.8,
            low_price=99.5,
            vwap=100.0,
            vwap_distance_pct=0.5,
            rvol=1.8,
            atr=2.5,
            atr_pct=2.5,
            gap_pct=1.2,
            odds_score=75.0,
            position_status="WATCHING",
            entry_price=0.0,
            unrealized_pnl_pct=0.0,
            active_plan=sample_trade_plan,
            current_time_str="10:05:00",
            minutes_to_eod_close=350
        )

        decision = agent.evaluate_tick(ctx)
        assert isinstance(decision, AgentDecision)
        assert decision.action == "BUY"
        assert decision.ticker == "AAPL"
        assert decision.risk_profile == "HIGH_RISK"
        assert decision.confidence >= 0.70
        assert len(decision.reasoning) > 0

    def test_stop_loss_exit_decision(self, sample_trade_plan):
        agent = AutonomousIntradayAgent()
        ctx = IntradayAgentContext(
            ticker="AAPL",
            current_price=96.5,  # Below stop_loss_price of 97.0
            previous_price=97.2,
            high_price=101.0,
            low_price=96.5,
            vwap=99.0,
            vwap_distance_pct=-2.5,
            rvol=1.2,
            atr=2.5,
            atr_pct=2.5,
            gap_pct=1.2,
            odds_score=60.0,
            position_status="ENTERED",
            entry_price=100.0,
            unrealized_pnl_pct=-3.5,
            active_plan=sample_trade_plan,
            current_time_str="11:30:00",
            minutes_to_eod_close=265
        )

        decision = agent.evaluate_tick(ctx)
        assert decision.action == "STOP_LOSS_EXIT"
        assert decision.confidence >= 0.95
        assert "stop-loss" in decision.reasoning[0].lower()

    def test_tighten_stop_to_breakeven(self, sample_trade_plan):
        agent = AutonomousIntradayAgent()
        # Price is at 103.5 (gain is 3.5, which is 70% of distance to target 1 of 105.0)
        ctx = IntradayAgentContext(
            ticker="AAPL",
            current_price=103.5,
            previous_price=103.0,
            high_price=103.8,
            low_price=99.8,
            vwap=101.5,
            vwap_distance_pct=2.0,
            rvol=1.5,
            atr=2.5,
            atr_pct=2.5,
            gap_pct=1.2,
            odds_score=75.0,
            position_status="ENTERED",
            entry_price=100.0,
            unrealized_pnl_pct=3.5,
            active_plan=sample_trade_plan,
            current_time_str="13:15:00",
            minutes_to_eod_close=160
        )

        decision = agent.evaluate_tick(ctx)
        assert decision.action == "TIGHTEN_STOP"
        assert decision.new_stop_price is not None
        assert decision.new_stop_price > sample_trade_plan.stop_loss_price
        assert decision.new_stop_price >= sample_trade_plan.entry_price

    def test_take_profit_target_reached(self, sample_trade_plan):
        agent = AutonomousIntradayAgent()
        # Price hits target 1 at 105.2
        ctx = IntradayAgentContext(
            ticker="AAPL",
            current_price=105.2,
            previous_price=104.8,
            high_price=105.5,
            low_price=99.8,
            vwap=102.0,
            vwap_distance_pct=3.1,
            rvol=1.5,
            atr=2.5,
            atr_pct=2.5,
            gap_pct=1.2,
            odds_score=75.0,
            position_status="ENTERED",
            entry_price=100.0,
            unrealized_pnl_pct=5.2,
            active_plan=sample_trade_plan,
            current_time_str="14:00:00",
            minutes_to_eod_close=115
        )

        decision = agent.evaluate_tick(ctx)
        assert decision.action == "TAKE_PROFIT"
        assert decision.confidence >= 0.90
        assert "Target 1" in decision.reasoning[0]

    def test_force_eod_exit_near_close(self, sample_trade_plan):
        agent = AutonomousIntradayAgent()
        ctx = IntradayAgentContext(
            ticker="AAPL",
            current_price=102.0,
            previous_price=102.0,
            high_price=103.0,
            low_price=99.5,
            vwap=101.5,
            vwap_distance_pct=0.5,
            rvol=1.1,
            atr=2.5,
            atr_pct=2.5,
            gap_pct=1.2,
            odds_score=60.0,
            position_status="ENTERED",
            entry_price=100.0,
            unrealized_pnl_pct=2.0,
            active_plan=sample_trade_plan,
            current_time_str="15:53:00",
            minutes_to_eod_close=2  # 2 minutes to 15:55 close
        )

        decision = agent.evaluate_tick(ctx)
        assert decision.action == "FORCE_EOD_EXIT"
        assert decision.confidence >= 0.98
        assert "EOD flat" in decision.reasoning[0]
