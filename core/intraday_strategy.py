#!/usr/bin/env python3
"""
Intraday Strategy Engine
Generates High Risk - High Reward and Safer Low Risk intraday trading strategies
with morning buy rules, evening exit conditions, stop loss, and gain targets.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field, asdict, replace
from datetime import datetime, time as dtime
from typing import Any, Dict, List, Optional
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from intraday_screener import IntradayCandidate, IntradayScreener


@dataclass
class IntradayTradePlan:
    """Intraday trade plan containing entry, target, stop loss, and exit timing."""

    risk_profile: str  # 'HIGH_RISK' or 'LOW_RISK'
    ticker: str
    action: str  # 'BUY' or 'HOLD'
    entry_price: float
    entry_window: str  # e.g., "09:30 - 10:30 EST (Morning Breakout / Dip)"
    entry_condition: str  # Technical trigger criteria
    stop_loss_price: float
    stop_loss_pct: float
    target_1_price: float
    target_1_pct: float
    target_2_price: Optional[float]
    target_2_pct: Optional[float]
    trailing_stop_activation_price: Optional[float]
    evening_exit_time: str  # "15:55 EST (Mandatory Flat EOD)"
    risk_per_share: float
    reward_per_share: float
    risk_reward_ratio: float
    position_sizing_pct: float  # Recommended portfolio allocation %
    reasons: List[str] = field(default_factory=list)
    valid: bool = True
    direction: str = "LONG"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DualIntradayReport:
    """Container holding both High-Risk and Low-Risk intraday strategies for a ticker."""

    ticker: str
    current_price: float
    intraday_odds_score: float
    timestamp: str
    high_risk_strategy: IntradayTradePlan
    low_risk_strategy: IntradayTradePlan
    candidate_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "current_price": self.current_price,
            "intraday_odds_score": self.intraday_odds_score,
            "timestamp": self.timestamp,
            "high_risk_strategy": self.high_risk_strategy.to_dict(),
            "low_risk_strategy": self.low_risk_strategy.to_dict(),
            "candidate_summary": self.candidate_summary,
        }


class IntradayStrategyGenerator:
    """
    Produces actionable intraday trading strategies tailored for daytraders:
    1. High Risk - High Reward: Targets maximum intraday momentum & expansion.
    2. Safer Low Risk: Targets high probability mean-reversion & trend continuation.
    """

    def __init__(self, screener: Optional[IntradayScreener] = None):
        self.screener = screener or IntradayScreener()

    def generate_strategies_for_candidate(
        self, candidate: IntradayCandidate
    ) -> DualIntradayReport:
        """
        Generates both High Risk and Low Risk trade plans for a screened candidate.
        """
        high_risk_plan = self._build_high_risk_strategy(candidate)
        low_risk_plan = self._build_low_risk_strategy(candidate)

        high_risk_plan = self._orient_plan(high_risk_plan, candidate)
        low_risk_plan = self._orient_plan(low_risk_plan, candidate)

        return DualIntradayReport(
            ticker=candidate.ticker,
            current_price=candidate.current_price,
            intraday_odds_score=candidate.intraday_odds_score,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            high_risk_strategy=high_risk_plan,
            low_risk_strategy=low_risk_plan,
            candidate_summary=candidate.to_dict(),
        )

    def _orient_plan(
        self, plan: IntradayTradePlan, candidate: IntradayCandidate
    ) -> IntradayTradePlan:
        """Use a short thesis only when both gap and VWAP posture are bearish."""
        if candidate.gap_pct >= -1.0 or candidate.vwap_distance_pct >= 0:
            return plan
        entry = plan.entry_price
        stop = round(entry + (entry - plan.stop_loss_price), 2)
        target_1 = round(entry - (plan.target_1_price - entry), 2)
        target_2 = (
            round(entry - (plan.target_2_price - entry), 2)
            if plan.target_2_price
            else None
        )
        trailing = (
            round(entry - (plan.trailing_stop_activation_price - entry), 2)
            if plan.trailing_stop_activation_price
            else None
        )
        return replace(
            plan,
            action="SELL",
            direction="SHORT",
            stop_loss_price=stop,
            target_1_price=target_1,
            target_2_price=target_2,
            trailing_stop_activation_price=trailing,
            entry_condition=plan.entry_condition.replace("above", "below").replace(
                "Support", "Resistance"
            ),
            reasons=[
                *plan.reasons,
                "Short direction confirmed by bearish gap and price below VWAP",
            ],
        )

    def generate_for_ticker(self, ticker: str) -> Optional[DualIntradayReport]:
        """
        Screens a single ticker and generates the dual intraday report.
        """
        candidate = self.screener.compute_intraday_metrics(ticker)
        if not candidate:
            return None
        return self.generate_strategies_for_candidate(candidate)

    def _build_high_risk_strategy(self, c: IntradayCandidate) -> IntradayTradePlan:
        """
        High Risk - High Reward:
        - Entry: Morning breakout above VWAP or 15-min Opening Range High.
        - Targets: 2.0x - 3.0x ATR ($+3% to +8%).
        - Stop Loss: 1.0x ATR or below morning swing low (R/R >= 2.0).
        - Trailing stop triggers once Target 1 is reached.
        """
        entry_price = c.current_price
        atr = max(c.atr, entry_price * 0.015)  # Minimum 1.5% buffer

        # Stop loss based on 1x ATR or 3% max
        stop_distance = min(atr * 1.0, entry_price * 0.035)
        stop_loss_price = round(max(0.01, entry_price - stop_distance), 2)
        stop_loss_pct = round(((entry_price - stop_loss_price) / entry_price) * 100, 2)

        # Target 1 (2.0x ATR) and Target 2 (3.0x ATR)
        target_1_price = round(entry_price + (atr * 2.0), 2)
        target_1_pct = round(((target_1_price - entry_price) / entry_price) * 100, 2)

        target_2_price = round(entry_price + (atr * 3.0), 2)
        target_2_pct = round(((target_2_price - entry_price) / entry_price) * 100, 2)

        trailing_activation = round(entry_price + (atr * 1.2), 2)

        risk_per_share = round(entry_price - stop_loss_price, 2)
        reward_per_share = round(target_1_price - entry_price, 2)
        rr_ratio = (
            round(reward_per_share / risk_per_share, 2) if risk_per_share > 0 else 2.0
        )

        reasons = [
            f"Momentum breakout play with high RVOL ({c.rvol:.2f}x)",
            f"Wide ATR profit expansion target (+{target_1_pct:.1f}% / +{target_2_pct:.1f}%)",
            f"Stop-loss placed 1x ATR (${stop_distance:.2f}) below entry",
            "Trailing stop engages once Target 1 or +1.2x ATR is printed",
        ]

        return IntradayTradePlan(
            risk_profile="HIGH_RISK",
            ticker=c.ticker,
            action="BUY",
            entry_price=entry_price,
            entry_window="09:30 - 10:45 EST (Morning Opening Range Breakout)",
            entry_condition=f"Cross and 5m candle close above ${entry_price:.2f} with volume confirmation",
            stop_loss_price=stop_loss_price,
            stop_loss_pct=stop_loss_pct,
            target_1_price=target_1_price,
            target_1_pct=target_1_pct,
            target_2_price=target_2_price,
            target_2_pct=target_2_pct,
            trailing_stop_activation_price=trailing_activation,
            evening_exit_time="15:55 EST (Hard Exit / No Overnight Hold)",
            risk_per_share=risk_per_share,
            reward_per_share=reward_per_share,
            risk_reward_ratio=rr_ratio,
            position_sizing_pct=5.0,  # 5% max risk allocation
            reasons=reasons,
            valid=True,
        )

    def _build_low_risk_strategy(self, c: IntradayCandidate) -> IntradayTradePlan:
        """
        Safer Low Risk:
        - Entry: Morning VWAP bounce / 20 EMA pullback test.
        - Targets: 1.0x to 1.5x ATR (+1.0% to +3.0%).
        - Stop Loss: 0.5x to 0.7x ATR or clean VWAP breach (R/R >= 1.5).
        - Evening exit: Strict 15:55 EST flat closure.
        """
        entry_price = c.current_price
        atr = max(c.atr, entry_price * 0.01)

        # Conservative stop loss: 0.6x ATR or 1.5% max
        stop_distance = min(atr * 0.6, entry_price * 0.015)
        stop_loss_price = round(max(0.01, entry_price - stop_distance), 2)
        stop_loss_pct = round(((entry_price - stop_loss_price) / entry_price) * 100, 2)

        # Target 1 (1.0x ATR) and Target 2 (1.5x ATR)
        target_1_price = round(entry_price + (atr * 1.0), 2)
        target_1_pct = round(((target_1_price - entry_price) / entry_price) * 100, 2)

        target_2_price = round(entry_price + (atr * 1.5), 2)
        target_2_pct = round(((target_2_price - entry_price) / entry_price) * 100, 2)

        trailing_activation = round(entry_price + (atr * 0.8), 2)

        risk_per_share = round(entry_price - stop_loss_price, 2)
        reward_per_share = round(target_1_price - entry_price, 2)
        rr_ratio = (
            round(reward_per_share / risk_per_share, 2) if risk_per_share > 0 else 1.6
        )

        reasons = [
            f"Mean reversion / trend continuation near VWAP (${c.vwap:.2f})",
            f"Controlled risk with tight stop at 0.6x ATR (-{stop_loss_pct:.1f}%)",
            f"High-probability conservative target (+{target_1_pct:.1f}%)",
            "Liquid profile ensuring minimal slippage",
        ]

        return IntradayTradePlan(
            risk_profile="LOW_RISK",
            ticker=c.ticker,
            action="BUY",
            entry_price=entry_price,
            entry_window="09:45 - 11:30 EST (Morning VWAP / EMA Pullback Confirmation)",
            entry_condition=f"Support hold at or above VWAP (${c.vwap:.2f}) with positive price posture",
            stop_loss_price=stop_loss_price,
            stop_loss_pct=stop_loss_pct,
            target_1_price=target_1_price,
            target_1_pct=target_1_pct,
            target_2_price=target_2_price,
            target_2_pct=target_2_pct,
            trailing_stop_activation_price=trailing_activation,
            evening_exit_time="15:55 EST (Hard Exit / No Overnight Hold)",
            risk_per_share=risk_per_share,
            reward_per_share=reward_per_share,
            risk_reward_ratio=rr_ratio,
            position_sizing_pct=10.0,  # 10% allocation for conservative profile
            reasons=reasons,
            valid=True,
        )
