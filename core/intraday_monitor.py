#!/usr/bin/env python3
"""
Intraday Loop Monitor
Multi-stock continuous live monitoring loop that tracks intraday strategies in real time,
evaluates entries, stops, profit targets, and renders an interactive terminal dashboard.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Terminal styling
try:
    from colorama import Fore, Back, Style, init

    init(autoreset=True)
except ImportError:

    class Fore:
        GREEN = ""
        RED = ""
        YELLOW = ""
        CYAN = ""
        MAGENTA = ""
        BLUE = ""
        WHITE = ""

    class Back:
        GREEN = ""
        RED = ""
        YELLOW = ""
        BLUE = ""

    class Style:
        BRIGHT = ""
        DIM = ""
        NORMAL = ""
        RESET_ALL = ""


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from market_quote_provider import MarketQuoteProvider
from intraday_screener import IntradayScreener, IntradayCandidate
from intraday_strategy import (
    IntradayStrategyGenerator,
    DualIntradayReport,
    IntradayTradePlan,
)
from intraday_simulator import IntradaySimulator, SimulatedIntradayTrade
from intraday_agent import AutonomousIntradayAgent, IntradayAgentContext, AgentDecision
from event_emitter import (
    EventBus,
    EVENT_TRADE_OPENED,
    EVENT_TRADE_CLOSED,
    EVENT_TRADE_STOP_TIGHTENED,
    EVENT_BUDGET_UPDATED,
    EVENT_DECISION_MADE,
    EVENT_SESSION_ENDED,
)
from decision_logger import DecisionLogger


@dataclass
class MonitoredStockState:
    """State of an actively monitored stock and its intraday strategy."""

    ticker: str
    report: DualIntradayReport
    active_profile: str  # 'HIGH_RISK', 'LOW_RISK', or 'BOTH'
    current_price: float
    previous_price: float = 0.0
    state: str = (
        "WATCHING"  # 'WATCHING', 'ENTERED', 'TARGET_HIT', 'STOP_HIT', 'EOD_CLOSED'
    )
    entry_price: float = 0.0
    highest_price: float = 0.0
    lowest_price: float = 0.0
    active_plan: Optional[IntradayTradePlan] = None
    shadow_trade: Optional[SimulatedIntradayTrade] = None
    latest_decision: Optional[AgentDecision] = None
    messages: List[str] = field(default_factory=list)


class IntradayLoopMonitor:
    """
    Continuous multi-stock intraday monitor and strategy execution tracker.
    """

    def __init__(
        self,
        quote_provider: Optional[MarketQuoteProvider] = None,
        simulator: Optional[IntradaySimulator] = None,
        screener: Optional[IntradayScreener] = None,
        strategy_gen: Optional[IntradayStrategyGenerator] = None,
        agent: Optional[AutonomousIntradayAgent] = None,
        poll_interval_seconds: int = 10,
        enable_shadow_trading: bool = True,
        event_bus: Optional[EventBus] = None,
        decision_logger: Optional[DecisionLogger] = None,
    ):
        self.quote_provider = quote_provider or MarketQuoteProvider()
        self.screener = screener or IntradayScreener(self.quote_provider)
        self.strategy_gen = strategy_gen or IntradayStrategyGenerator(self.screener)
        self.simulator = simulator or IntradaySimulator()
        self.agent = agent or AutonomousIntradayAgent()
        self.poll_interval = poll_interval_seconds
        self.enable_shadow = enable_shadow_trading
        self.event_bus = event_bus or EventBus.get_instance()
        self.decision_logger = decision_logger
        self.monitored_stocks: Dict[str, MonitoredStockState] = {}
        self.running = False
        self.tick_count = 0

    def _emit(self, event_name: str, data: Dict[str, Any]):
        """Emit an event and augment with budget info if shadow trading."""
        if self.enable_shadow:
            try:
                data["budget"] = self.simulator.get_budget_summary()
                data["budget_remaining"] = data["budget"]["available_cash"]
            except Exception:
                pass
        self.event_bus.emit(event_name, data)

    def _log_decision(self, decision: AgentDecision, ctx: IntradayAgentContext):
        """Persist a decision to the decision logger."""
        if self.decision_logger:
            budget_info = None
            if self.enable_shadow:
                try:
                    budget_info = self.simulator.get_budget_summary()
                except Exception:
                    pass
            self.decision_logger.log(decision, ctx, budget_info)

    def add_stocks(self, tickers: List[str], profile: str = "BOTH"):
        """Adds a list of tickers to the continuous monitoring loop."""
        for t in tickers:
            ticker = t.strip().upper()
            report = self.strategy_gen.generate_for_ticker(ticker)
            if not report:
                print(
                    f"{Fore.YELLOW}⚠️  Could not generate intraday strategy for {ticker}{Style.RESET_ALL}"
                )
                continue

            # Pick active trade plan based on profile preference
            plan = (
                report.high_risk_strategy
                if profile == "HIGH_RISK"
                else report.low_risk_strategy
            )

            state = MonitoredStockState(
                ticker=ticker,
                report=report,
                active_profile=profile,
                current_price=report.current_price,
                previous_price=report.current_price,
                highest_price=report.current_price,
                lowest_price=report.current_price,
                active_plan=plan,
            )

            # Auto-open shadow trade if enabled and initially triggered
            if self.enable_shadow and plan:
                state.shadow_trade = self.simulator.open_paper_trade(plan)
                if state.shadow_trade:
                    state.state = "ENTERED"
                    state.entry_price = report.current_price
                    self._emit(
                        EVENT_TRADE_OPENED,
                        {
                            "ticker": ticker,
                            "price": report.current_price,
                            "risk_profile": plan.risk_profile,
                            "confidence": 1.0,
                            "shares": state.shadow_trade.shares,
                            "cost_basis": state.shadow_trade.cost_basis,
                            "plan": plan.to_dict(),
                        },
                    )

            self.monitored_stocks[ticker] = state
            print(
                f"{Fore.GREEN}✓ Added {ticker} ({profile}) to Intraday Monitor [Odds Score: {report.intraday_odds_score}/100]{Style.RESET_ALL}"
            )

    def poll_once(self) -> List[Dict[str, Any]]:
        """
        Executes a single polling iteration across all monitored stocks.
        Invokes the AI Intraday Agent to evaluate entries, stops, and targets.
        """
        self.tick_count += 1
        now_dt = datetime.now()
        now_str = now_dt.strftime("%H:%M:%S")
        events = []

        # Calculate minutes to 15:55 EST (16:00 close - 5 mins)
        target_eod_min = 15 * 60 + 55
        current_day_min = now_dt.hour * 60 + now_dt.minute
        minutes_to_close = max(0, target_eod_min - current_day_min)

        for ticker, state in self.monitored_stocks.items():
            quote = self.quote_provider.get_quote(ticker)
            price = quote.get("price")
            if price is None:
                continue

            price = float(price)
            state.previous_price = state.current_price
            state.current_price = price
            state.highest_price = max(state.highest_price, price)
            state.lowest_price = min(state.lowest_price, price)

            # Running P&L
            unrealized_pnl = 0.0
            if state.entry_price > 0:
                unrealized_pnl = ((price - state.entry_price) / state.entry_price) * 100

            cand = state.report.candidate_summary
            vwap = cand.get("vwap", price)
            vwap_dist = ((price - vwap) / vwap) * 100 if vwap > 0 else 0.0

            # 1. Build Agent Context
            ctx = IntradayAgentContext(
                ticker=ticker,
                current_price=price,
                previous_price=state.previous_price,
                high_price=state.highest_price,
                low_price=state.lowest_price,
                vwap=vwap,
                vwap_distance_pct=vwap_dist,
                rvol=cand.get("rvol", 1.0),
                atr=cand.get("atr", price * 0.02),
                atr_pct=cand.get("atr_pct", 2.0),
                gap_pct=cand.get("gap_pct", 0.0),
                odds_score=state.report.intraday_odds_score,
                position_status=state.state,
                entry_price=state.entry_price,
                unrealized_pnl_pct=round(unrealized_pnl, 2),
                active_plan=state.active_plan,
                current_time_str=now_str,
                minutes_to_eod_close=minutes_to_close,
            )

            # 2. Invoke Autonomous AI Agent
            if self.agent.on_decision is None:
                self.agent.on_decision = self._log_decision
            decision = self.agent.evaluate_tick(ctx)
            state.latest_decision = decision

            # 3. Handle Agent Actions
            if (
                decision.action == "BUY"
                and state.state == "WATCHING"
                and state.active_plan
            ):
                state.state = "ENTERED"
                state.entry_price = price
                if self.enable_shadow:
                    shadow_trade = self.simulator.open_paper_trade(
                        state.active_plan, fill_price=price
                    )
                    if shadow_trade:
                        state.shadow_trade = shadow_trade
                        self._emit(
                            EVENT_TRADE_OPENED,
                            {
                                "ticker": ticker,
                                "price": price,
                                "risk_profile": decision.risk_profile,
                                "confidence": decision.confidence,
                                "shares": shadow_trade.shares,
                                "cost_basis": shadow_trade.cost_basis,
                                "plan": state.active_plan.to_dict(),
                            },
                        )
                msg = f"[{now_str}] 🤖 AGENT BUY: Entered {ticker} at ${price:.2f} ({decision.reasoning[0] if decision.reasoning else ''})"
                state.messages.append(msg)
                events.append(
                    {
                        "ticker": ticker,
                        "action": "AGENT_BUY",
                        "price": price,
                        "decision": decision.to_dict(),
                    }
                )

            elif (
                decision.action == "TIGHTEN_STOP"
                and decision.new_stop_price
                and state.active_plan
            ):
                old_stop = state.active_plan.stop_loss_price
                state.active_plan.stop_loss_price = decision.new_stop_price
                if (
                    state.shadow_trade
                    and state.shadow_trade.id in self.simulator.active_trades
                ):
                    self.simulator.active_trades[
                        state.shadow_trade.id
                    ].stop_loss_price = decision.new_stop_price
                msg = f"[{now_str}] 🤖 AGENT TIGHTEN STOP: ${old_stop:.2f} ➔ ${decision.new_stop_price:.2f}"
                state.messages.append(msg)
                events.append(
                    {
                        "ticker": ticker,
                        "action": "AGENT_TIGHTEN_STOP",
                        "new_stop": decision.new_stop_price,
                    }
                )
                self._emit(
                    EVENT_TRADE_STOP_TIGHTENED,
                    {
                        "ticker": ticker,
                        "old_stop": old_stop,
                        "new_stop": decision.new_stop_price,
                        "price": price,
                    },
                )

            elif (
                decision.action in ("TAKE_PROFIT", "STOP_LOSS_EXIT", "FORCE_EOD_EXIT")
                and state.state == "ENTERED"
            ):
                state.state = (
                    "TARGET_HIT"
                    if decision.action == "TAKE_PROFIT"
                    else (
                        "STOP_HIT"
                        if decision.action == "STOP_LOSS_EXIT"
                        else "EOD_CLOSED"
                    )
                )
                msg = f"[{now_str}] 🤖 AGENT {decision.action}: ${price:.2f} (P&L: {unrealized_pnl:+.2f}%)"
                state.messages.append(msg)
                events.append(
                    {
                        "ticker": ticker,
                        "action": decision.action,
                        "price": price,
                        "pnl_pct": unrealized_pnl,
                    }
                )
                # Commit the shadow trade to the simulator immediately so
                # the budget is settled on the same tick.
                if (
                    self.enable_shadow
                    and state.shadow_trade
                    and state.shadow_trade.id in self.simulator.active_trades
                ):
                    self.simulator.force_exit_trade(
                        state.shadow_trade.id, price, decision.action, now_str
                    )
                self._emit(
                    EVENT_TRADE_CLOSED,
                    {
                        "ticker": ticker,
                        "price": price,
                        "action": decision.action,
                        "pnl_pct": round(unrealized_pnl, 2),
                        "reason": decision.reasoning[0] if decision.reasoning else "",
                    },
                )

            # Check paper trade / threshold logic
            if self.enable_shadow and self.simulator and state.state == "ENTERED":
                tick_events = self.simulator.update_with_tick(ticker, price, now_str)
                for ev in tick_events:
                    events.append(ev)
                    msg = f"[{now_str}] {ticker}: {ev['event']} at ${price:.2f} (P&L: {ev['pnl_pct']:+.2f}%)"
                    state.messages.append(msg)
                    self._emit(
                        EVENT_TRADE_CLOSED,
                        {
                            "ticker": ticker,
                            "price": price,
                            "action": ev["event"],
                            "pnl_pct": round(ev["pnl_pct"], 2),
                            "reason": f"Simulator {ev['event']} on tick",
                        },
                    )
                    if "STOP" in ev["event"]:
                        state.state = "STOP_HIT"
                    elif "TARGET" in ev["event"]:
                        state.state = "TARGET_HIT"

        return events

    def render_dashboard(self):
        """Renders a colorized live terminal dashboard with AI Agent telemetry."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        os.system("cls" if os.name == "nt" else "clear")

        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 88}")
        print(
            f" 🤖 ClariFi Autonomous Intraday AI Agent & Live Monitor | Tick #{self.tick_count} | {now_str}"
        )
        print(f"{'=' * 88}{Style.RESET_ALL}\n")

        print(
            f"{'Ticker':<7} {'Price':<10} {'Change':<10} {'Strategy':<11} {'Status':<12} {'Stop Loss':<10} {'Target 1':<10} {'P&L %':<8} {'Agent Action'}"
        )
        print(f"{'-' * 88}")

        for ticker, state in self.monitored_stocks.items():
            diff = state.current_price - state.previous_price
            diff_pct = (
                (diff / state.previous_price * 100) if state.previous_price > 0 else 0.0
            )

            if diff > 0:
                p_color = Fore.GREEN
                arrow = "▲"
            elif diff < 0:
                p_color = Fore.RED
                arrow = "▼"
            else:
                p_color = Fore.WHITE
                arrow = "●"

            plan = state.active_plan
            stop_str = f"${plan.stop_loss_price:.2f}" if plan else "N/A"
            target_str = f"${plan.target_1_price:.2f}" if plan else "N/A"

            # Compute running P&L
            if state.entry_price > 0:
                pnl = (
                    (state.current_price - state.entry_price) / state.entry_price
                ) * 100
                pnl_str = f"{pnl:+.2f}%"
                pnl_color = Fore.GREEN if pnl >= 0 else Fore.RED
            else:
                pnl_str = "0.00%"
                pnl_color = Fore.WHITE

            status_color = (
                Fore.YELLOW
                if state.state == "WATCHING"
                else (Fore.GREEN if state.state == "ENTERED" else Fore.MAGENTA)
            )

            dec = state.latest_decision
            agent_action_str = (
                f"{dec.action} ({dec.confidence * 100:.0f}%)" if dec else "INITIALIZING"
            )
            agent_color = (
                Fore.GREEN
                if dec and dec.action in ("BUY", "TAKE_PROFIT")
                else (Fore.RED if dec and "STOP" in dec.action else Fore.CYAN)
            )

            print(
                f"{Fore.WHITE}{Style.BRIGHT}{ticker:<7}{Style.RESET_ALL} "
                f"{p_color}{arrow} ${state.current_price:<7.2f}{Style.RESET_ALL} "
                f"{p_color}{diff_pct:>+5.2f}%{Style.RESET_ALL}   "
                f"{Fore.CYAN}{state.active_profile:<11}{Style.RESET_ALL} "
                f"{status_color}{state.state:<12}{Style.RESET_ALL} "
                f"{Fore.RED}{stop_str:<10}{Style.RESET_ALL} "
                f"{Fore.GREEN}{target_str:<10}{Style.RESET_ALL} "
                f"{pnl_color}{pnl_str:<8}{Style.RESET_ALL} "
                f"{agent_color}{agent_action_str}{Style.RESET_ALL}"
            )

        # Print recent agent decision rationales
        print(f"\n{Fore.CYAN}--- AI Agent Decision Log ---{Style.RESET_ALL}")
        for ticker, state in self.monitored_stocks.items():
            if state.latest_decision and state.latest_decision.reasoning:
                latest_reason = state.latest_decision.reasoning[0]
                print(
                    f"  • {Fore.YELLOW}{ticker}{Style.RESET_ALL}: [{state.latest_decision.action}] {latest_reason}"
                )

        # Print simulator stats
        if self.enable_shadow:
            perf = self.simulator.get_performance_summary()
            print(
                f"\n{Fore.BLUE}--- Intraday Paper Trading Summary ---{Style.RESET_ALL}"
            )
            print(
                f"Closed Trades: {perf['total_trades']} | Open Trades: {perf['open_trades']} | Win Rate: {perf['win_rate_pct']}% | Total Realized P&L: {perf['total_realized_pnl_pct']:+.2f}%"
            )
            try:
                budget = self.simulator.get_budget_summary()
                print(
                    f"Budget: {Fore.GREEN}${budget['available_cash']:,.2f}{Style.RESET_ALL} cash "
                    f"(init ${budget['initial_budget']:,.2f}) | "
                    f"Invested: {Fore.YELLOW}${budget['invested_amount']:,.2f}{Style.RESET_ALL} | "
                    f"Realized: {Fore.CYAN}{budget['total_realized_pnl']:+,.2f}${Style.RESET_ALL} "
                    f"(Trades: {budget['trades_count']})"
                )
            except Exception:
                pass

        print(
            f"\n{Fore.YELLOW}Press Ctrl+C to stop monitoring and liquidate positions.{Style.RESET_ALL}"
        )

    async def run_loop_async(self, max_ticks: Optional[int] = None):
        """Runs the asynchronous continuous monitoring loop."""
        self.running = True
        try:
            while self.running:
                self.poll_once()
                self.render_dashboard()
                if max_ticks and self.tick_count >= max_ticks:
                    break
                await asyncio.sleep(self.poll_interval)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print(
                f"\n{Fore.YELLOW}Stopping monitor and executing EOD liquidation...{Style.RESET_ALL}"
            )
        finally:
            self.running = False
            # Force EOD liquidation
            prices = {t: s.current_price for t, s in self.monitored_stocks.items()}
            self.simulator.force_eod_exit(prices)
            perf = self.simulator.get_performance_summary()
            print(
                f"{Fore.GREEN}Session Finalized. Performance: Win Rate {perf['win_rate_pct']}%, Realized P&L: {perf['total_realized_pnl_pct']:+.2f}%{Style.RESET_ALL}"
            )

            # Export decision log to CSV
            if self.decision_logger:
                try:
                    csv_path = self.decision_logger.export_csv()
                    print(
                        f"{Fore.CYAN}Decision log exported to: {csv_path}{Style.RESET_ALL}"
                    )
                    summary = self.decision_logger.summary()
                    print(
                        f"Session {summary['session_id']}: {summary['total_decisions']} decisions across {len(summary['tickers_monitored'])} tickers"
                    )
                except Exception as exc:
                    print(
                        f"{Fore.YELLOW}Could not export decision log CSV: {exc}{Style.RESET_ALL}"
                    )

            # Emit session ended
            self._emit(
                EVENT_SESSION_ENDED,
                {
                    "session_id": getattr(self.decision_logger, "session_id", None),
                    "performance": perf,
                },
            )

    def run_loop(self, max_ticks: Optional[int] = None):
        """Synchronous wrapper for running the monitoring loop."""
        asyncio.run(self.run_loop_async(max_ticks))
