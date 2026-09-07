#!/usr/bin/env python3
"""
Autonomous AI Intraday Trading Agent
Evaluates live stock ticks, technical metrics, stop-loss / take-profit indicators,
and time-to-close to autonomously make BUY, SELL, TIGHTEN_STOP, or EOD_EXIT decisions.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, time as dtime
from typing import Any, Callable, Dict, List, Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from intraday_strategy import IntradayTradePlan, DualIntradayReport
from event_emitter import EventBus, EVENT_DECISION_MADE


@dataclass
class IntradayAgentContext:
    """Rich market and position context supplied to the AI Agent on every tick."""

    ticker: str
    current_price: float
    previous_price: float
    high_price: float
    low_price: float
    vwap: float
    vwap_distance_pct: float
    rvol: float
    atr: float
    atr_pct: float
    gap_pct: float
    odds_score: float
    position_status: (
        str  # 'WATCHING', 'ENTERED', 'TARGET_HIT', 'STOP_HIT', 'EOD_CLOSED'
    )
    entry_price: float
    unrealized_pnl_pct: float
    active_plan: Optional[IntradayTradePlan]
    current_time_str: str
    minutes_to_eod_close: int  # Minutes until 15:55 EST mandatory exit

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.active_plan:
            data["active_plan"] = self.active_plan.to_dict()
        return data


@dataclass
class AgentDecision:
    """Autonomous decision output produced by the AI Agent."""

    action: str  # 'BUY', 'HOLD', 'TAKE_PROFIT', 'STOP_LOSS_EXIT', 'TIGHTEN_STOP', 'FORCE_EOD_EXIT'
    ticker: str
    risk_profile: str  # 'HIGH_RISK', 'LOW_RISK', 'NONE'
    confidence: float  # 0.0 to 1.0
    suggested_price: float
    new_stop_price: Optional[float] = None
    reasoning: List[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AutonomousIntradayAgent:
    """
    Intelligent intraday trading agent that evaluates real-time market data
    and executes disciplined trading decisions based on predefined risk rules
    and indicator dynamics.
    """

    def __init__(
        self,
        name: str = "ClariFi-Intraday-Agent-v1",
        preferred_profile: str = "BOTH",
        llm_hook: Optional[Callable[[IntradayAgentContext], AgentDecision]] = None,
        on_decision: Optional[
            Callable[[AgentDecision, IntradayAgentContext], None]
        ] = None,
    ):
        self.name = name
        self.preferred_profile = preferred_profile
        self.llm_hook = llm_hook  # Optional pluggable LLM decision provider
        self.on_decision = on_decision  # Optional callback fired on every decision
        self.decision_history: List[AgentDecision] = []

    def _dispatch_decision(
        self, decision: AgentDecision, ctx: IntradayAgentContext
    ) -> AgentDecision:
        """Fire the on_decision callback and emit a decision.made event on the EventBus."""
        self.decision_history.append(decision)
        if self.on_decision is not None:
            try:
                self.on_decision(decision, ctx)
            except Exception:
                pass
        try:
            EventBus.get_instance().emit(
                EVENT_DECISION_MADE,
                {
                    **decision.to_dict(),
                    "reasoning_list": decision.reasoning,
                    "context": ctx.to_dict(),
                },
            )
        except Exception:
            pass
        return decision

    def evaluate_tick(self, ctx: IntradayAgentContext) -> AgentDecision:
        """
        Main decision-making logic evaluated on each tick or price alert.
        """
        # If an external LLM hook is attached, invoke it first
        if self.llm_hook is not None:
            try:
                llm_decision = self.llm_hook(ctx)
                if llm_decision:
                    return self._dispatch_decision(llm_decision, ctx)
            except Exception:
                pass  # Fall back to algorithmic autonomous rules

        decision = self._rule_based_evaluate(ctx)
        return self._dispatch_decision(decision, ctx)

    def _rule_based_evaluate(self, ctx: IntradayAgentContext) -> AgentDecision:
        now = datetime.now()
        plan = ctx.active_plan
        price = ctx.current_price

        # 1. Mandatory End-of-Day Exit Rule (15:55 EST or <= 5 mins to close)
        if ctx.minutes_to_eod_close <= 5 and ctx.position_status == "ENTERED":
            return AgentDecision(
                action="FORCE_EOD_EXIT",
                ticker=ctx.ticker,
                risk_profile=plan.risk_profile if plan else "NONE",
                confidence=0.99,
                suggested_price=price,
                reasoning=[
                    f"Mandatory EOD flat rule reached ({ctx.minutes_to_eod_close} mins to close)",
                    f"Closing position at ${price:.2f} with {ctx.unrealized_pnl_pct:+.2f}% realized P&L",
                    "Eliminates overnight gap and earnings risk",
                ],
            )

        # 2. Position is in WATCHING state: Evaluate Morning Entry Criteria
        if ctx.position_status == "WATCHING" and plan:
            # Check if within morning entry window
            profile_to_use = plan.risk_profile

            # Entry Trigger Checks
            can_enter = False
            reasons = []

            if profile_to_use == "HIGH_RISK":
                # Breakout trigger: price holding above entry condition level & strong volume
                if price >= plan.entry_price and ctx.rvol >= 1.2:
                    can_enter = True
                    reasons = [
                        f"Morning breakout confirmed: ${price:.2f} >= ${plan.entry_price:.2f}",
                        f"Relative Volume confirmation (RVOL: {ctx.rvol:.2f}x)",
                        f"Favorable Risk/Reward ratio: {plan.risk_reward_ratio:.2f}x",
                    ]
            else:
                # Low risk trigger: VWAP bounce / EMA hold with positive posture
                if ctx.vwap_distance_pct >= -0.5 and price >= plan.stop_loss_price:
                    can_enter = True
                    reasons = [
                        f"Support holding above VWAP pivot (${ctx.vwap:.2f})",
                        f"Disciplined low-risk stop set at ${plan.stop_loss_price:.2f} (-{plan.stop_loss_pct:.2f}%)",
                        f"Initial profit target: ${plan.target_1_price:.2f} (+{plan.target_1_pct:.2f}%)",
                    ]

            if can_enter and ctx.odds_score >= 50.0:
                return AgentDecision(
                    action="BUY",
                    ticker=ctx.ticker,
                    risk_profile=profile_to_use,
                    confidence=round(ctx.odds_score / 100.0, 2),
                    suggested_price=price,
                    new_stop_price=plan.stop_loss_price,
                    reasoning=reasons,
                )

        # 3. Position is in ENTERED state: Manage Stops, Trailing Exits & Targets
        if ctx.position_status == "ENTERED" and plan:
            # A. Stop Loss Breach Check
            if price <= plan.stop_loss_price:
                return AgentDecision(
                    action="STOP_LOSS_EXIT",
                    ticker=ctx.ticker,
                    risk_profile=plan.risk_profile,
                    confidence=0.98,
                    suggested_price=plan.stop_loss_price,
                    reasoning=[
                        f"Price breached hard stop-loss of ${plan.stop_loss_price:.2f}",
                        f"Executing disciplined cut-loss to protect capital (P&L: {ctx.unrealized_pnl_pct:+.2f}%)",
                    ],
                )

            # B. Target 2 Achievement (Final Take Profit)
            if plan.target_2_price and price >= plan.target_2_price:
                return AgentDecision(
                    action="TAKE_PROFIT",
                    ticker=ctx.ticker,
                    risk_profile=plan.risk_profile,
                    confidence=0.95,
                    suggested_price=price,
                    reasoning=[
                        f"Profit Target 2 (${plan.target_2_price:.2f}) reached at ${price:.2f}",
                        f"Securing +{ctx.unrealized_pnl_pct:.2f}% gain at maximum profit expansion",
                    ],
                )

            # C. Target 1 Achievement
            if price >= plan.target_1_price:
                return AgentDecision(
                    action="TAKE_PROFIT",
                    ticker=ctx.ticker,
                    risk_profile=plan.risk_profile,
                    confidence=0.90,
                    suggested_price=price,
                    reasoning=[
                        f"Profit Target 1 (${plan.target_1_price:.2f}) reached (+{plan.target_1_pct:.2f}%)",
                        f"Locking in gains at ${price:.2f} (P&L: {ctx.unrealized_pnl_pct:+.2f}%)",
                    ],
                )

            # D. Dynamic Trailing Stop Tightening
            # If price reached >= 60% of the distance to Target 1, raise stop to Breakeven
            distance_to_target = plan.target_1_price - plan.entry_price
            current_gain = price - plan.entry_price
            if distance_to_target > 0 and (current_gain / distance_to_target) >= 0.60:
                breakeven_stop = round(
                    plan.entry_price + (plan.entry_price * 0.002), 2
                )  # Entry + 0.2% buffer
                if breakeven_stop > plan.stop_loss_price:
                    return AgentDecision(
                        action="TIGHTEN_STOP",
                        ticker=ctx.ticker,
                        risk_profile=plan.risk_profile,
                        confidence=0.85,
                        suggested_price=price,
                        new_stop_price=breakeven_stop,
                        reasoning=[
                            f"Price reached 60%+ of Target 1 (${price:.2f})",
                            f"Tightening stop-loss from ${plan.stop_loss_price:.2f} up to Breakeven+ (${breakeven_stop:.2f})",
                            "Position is now risk-free",
                        ],
                    )

        # 4. Default: Maintain active posture
        return AgentDecision(
            action="HOLD",
            ticker=ctx.ticker,
            risk_profile=plan.risk_profile if plan else "NONE",
            confidence=0.50,
            suggested_price=price,
            reasoning=[
                f"Price (${price:.2f}) trading within normal intraday volatility channel",
                f"P&L: {ctx.unrealized_pnl_pct:+.2f}% | VWAP distance: {ctx.vwap_distance_pct:+.2f}%",
                "Maintaining position and monitoring triggers",
            ],
        )
