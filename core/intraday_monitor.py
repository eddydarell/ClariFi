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
from intraday_strategy import IntradayStrategyGenerator, DualIntradayReport, IntradayTradePlan
from intraday_simulator import IntradaySimulator, SimulatedIntradayTrade


@dataclass
class MonitoredStockState:
    """State of an actively monitored stock and its intraday strategy."""
    ticker: str
    report: DualIntradayReport
    active_profile: str  # 'HIGH_RISK', 'LOW_RISK', or 'BOTH'
    current_price: float
    previous_price: float = 0.0
    state: str = "WATCHING"  # 'WATCHING', 'ENTERED', 'TARGET_HIT', 'STOP_HIT', 'EOD_CLOSED'
    entry_price: float = 0.0
    highest_price: float = 0.0
    lowest_price: float = 0.0
    active_plan: Optional[IntradayTradePlan] = None
    shadow_trade: Optional[SimulatedIntradayTrade] = None
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
        poll_interval_seconds: int = 10,
        enable_shadow_trading: bool = True
    ):
        self.quote_provider = quote_provider or MarketQuoteProvider()
        self.screener = screener or IntradayScreener(self.quote_provider)
        self.strategy_gen = strategy_gen or IntradayStrategyGenerator(self.screener)
        self.simulator = simulator or IntradaySimulator()
        self.poll_interval = poll_interval_seconds
        self.enable_shadow = enable_shadow_trading
        self.monitored_stocks: Dict[str, MonitoredStockState] = {}
        self.running = False
        self.tick_count = 0

    def add_stocks(self, tickers: List[str], profile: str = "BOTH"):
        """Adds a list of tickers to the continuous monitoring loop."""
        for t in tickers:
            ticker = t.strip().upper()
            report = self.strategy_gen.generate_for_ticker(ticker)
            if not report:
                print(f"{Fore.YELLOW}⚠️  Could not generate intraday strategy for {ticker}{Style.RESET_ALL}")
                continue

            # Pick active trade plan based on profile preference
            plan = report.high_risk_strategy if profile == "HIGH_RISK" else report.low_risk_strategy

            state = MonitoredStockState(
                ticker=ticker,
                report=report,
                active_profile=profile,
                current_price=report.current_price,
                previous_price=report.current_price,
                highest_price=report.current_price,
                lowest_price=report.current_price,
                active_plan=plan
            )

            # Auto-open shadow trade if enabled
            if self.enable_shadow and plan:
                state.shadow_trade = self.simulator.open_paper_trade(plan)
                state.state = "ENTERED"
                state.entry_price = report.current_price

            self.monitored_stocks[ticker] = state
            print(f"{Fore.GREEN}✓ Added {ticker} ({profile}) to Intraday Monitor [Odds Score: {report.intraday_odds_score}/100]{Style.RESET_ALL}")

    def poll_once(self) -> List[Dict[str, Any]]:
        """
        Executes a single polling iteration across all monitored stocks.
        """
        self.tick_count += 1
        now_str = datetime.now().strftime("%H:%M:%S")
        events = []

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

            # Check paper trade / threshold logic
            if self.enable_shadow and self.simulator:
                tick_events = self.simulator.update_with_tick(ticker, price, now_str)
                for ev in tick_events:
                    events.append(ev)
                    msg = f"[{now_str}] {ticker}: {ev['event']} at ${price:.2f} (P&L: {ev['pnl_pct']:+.2f}%)"
                    state.messages.append(msg)
                    if 'STOP' in ev['event']:
                        state.state = "STOP_HIT"
                    elif 'TARGET' in ev['event']:
                        state.state = "TARGET_HIT"

            # Check if near stop or target
            plan = state.active_plan
            if plan and state.state == "ENTERED":
                dist_stop_pct = ((price - plan.stop_loss_price) / price) * 100
                dist_target_pct = ((plan.target_1_price - price) / price) * 100
                if dist_stop_pct < 0.5:
                    events.append({'ticker': ticker, 'alert': 'NEAR_STOP_LOSS', 'price': price})
                elif dist_target_pct < 0.5:
                    events.append({'ticker': ticker, 'alert': 'NEAR_PROFIT_TARGET', 'price': price})

        return events

    def render_dashboard(self):
        """Renders a colorized live terminal dashboard."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        os.system('cls' if os.name == 'nt' else 'clear')

        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 80}")
        print(f" 🚀 ClariFi Intraday Strategy Engine & Live Monitor | Tick #{self.tick_count} | {now_str}")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

        print(f"{'Ticker':<7} {'Price':<10} {'Change':<12} {'Strategy':<11} {'Status':<12} {'Stop Loss':<11} {'Target 1':<11} {'R/R':<6} {'P&L %':<8}")
        print(f"{'-' * 80}")

        for ticker, state in self.monitored_stocks.items():
            diff = state.current_price - state.previous_price
            diff_pct = (diff / state.previous_price * 100) if state.previous_price > 0 else 0.0

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
            rr_str = f"{plan.risk_reward_ratio:.1f}x" if plan else "N/A"

            # Compute running P&L
            if state.entry_price > 0:
                pnl = ((state.current_price - state.entry_price) / state.entry_price) * 100
                pnl_str = f"{pnl:+.2f}%"
                pnl_color = Fore.GREEN if pnl >= 0 else Fore.RED
            else:
                pnl_str = "0.00%"
                pnl_color = Fore.WHITE

            status_color = Fore.YELLOW if state.state == "WATCHING" else (Fore.GREEN if state.state == "ENTERED" else Fore.MAGENTA)

            print(
                f"{Fore.WHITE}{Style.BRIGHT}{ticker:<7}{Style.RESET_ALL} "
                f"{p_color}{arrow} ${state.current_price:<7.2f}{Style.RESET_ALL} "
                f"{p_color}{diff_pct:>+5.2f}%{Style.RESET_ALL}     "
                f"{Fore.CYAN}{state.active_profile:<11}{Style.RESET_ALL} "
                f"{status_color}{state.state:<12}{Style.RESET_ALL} "
                f"{Fore.RED}{stop_str:<11}{Style.RESET_ALL} "
                f"{Fore.GREEN}{target_str:<11}{Style.RESET_ALL} "
                f"{rr_str:<6} "
                f"{pnl_color}{pnl_str:<8}{Style.RESET_ALL}"
            )

        # Print simulator stats
        if self.enable_shadow:
            perf = self.simulator.get_performance_summary()
            print(f"\n{Fore.BLUE}--- Intraday Paper Trading Summary ---{Style.RESET_ALL}")
            print(f"Closed Trades: {perf['total_trades']} | Open Trades: {perf['open_trades']} | Win Rate: {perf['win_rate_pct']}% | Total Realized P&L: {perf['total_realized_pnl_pct']:+.2f}%")

        print(f"\n{Fore.YELLOW}Press Ctrl+C to stop monitoring and liquidate positions.{Style.RESET_ALL}")

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
            print(f"\n{Fore.YELLOW}Stopping monitor and executing EOD liquidation...{Style.RESET_ALL}")
        finally:
            self.running = False
            # Force EOD liquidation
            prices = {t: s.current_price for t, s in self.monitored_stocks.items()}
            self.simulator.force_eod_exit(prices)
            perf = self.simulator.get_performance_summary()
            print(f"{Fore.GREEN}Session Finalized. Performance: Win Rate {perf['win_rate_pct']}%, Realized P&L: {perf['total_realized_pnl_pct']:+.2f}%{Style.RESET_ALL}")

    def run_loop(self, max_ticks: Optional[int] = None):
        """Synchronous wrapper for running the monitoring loop."""
        asyncio.run(self.run_loop_async(max_ticks))
