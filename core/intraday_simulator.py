#!/usr/bin/env python3
"""
Intraday Paper / Shadow Trade Simulator
Tracks paper trades initiated from intraday strategies with simulated fills,
slippage, stop-loss breaks, target triggers, and EOD auto-liquidation.
Budget-aware: deducts from a simulated cash balance on entry, restores on exit.
"""

from __future__ import annotations

import json
import math
import os
import sys
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from database.models import DatabaseManager

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from intraday_strategy import IntradayTradePlan


@dataclass
class SimulatedIntradayTrade:
    """Represents an active or closed simulated intraday trade."""

    id: str
    ticker: str
    risk_profile: str
    entry_price: float
    entry_time: str
    stop_loss_price: float
    target_1_price: float
    target_2_price: Optional[float]
    status: str  # 'OPEN', 'TARGET_HIT', 'STOP_HIT', 'EOD_CLOSED'
    exit_price: Optional[float] = None
    exit_time: Optional[float] = None
    exit_reason: Optional[str] = (
        None  # 'TARGET_1', 'TARGET_2', 'STOP_LOSS', 'EOD_EXPIRATION'
    )
    gross_pnl_pct: float = 0.0
    net_pnl_pct: float = 0.0
    shares: int = 0
    cost_basis: float = 0.0  # total dollar cost of this position (shares * entry_price)
    realized_pnl_dollars: float = 0.0
    slippage_cost_pct: float = 0.05  # 0.05% estimated round-trip slippage & fees

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IntradaySimulator:
    """
    Manages intraday paper trade lifecycles with budget tracking.
    Deducts from a simulated cash balance on entry, restores on exit.
    """

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        initial_budget: float = 100_000.0,
        session_id: Optional[str] = None,
    ):
        self.db = db_manager or DatabaseManager(
            os.environ.get("CLARIFI_DB_PATH", "clarifi.db")
        )
        self.initial_budget = initial_budget
        self.available_cash = initial_budget
        self.invested_amount = 0.0
        self.total_realized_pnl = 0.0
        self.trades_count = 0
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.active_trades: Dict[str, SimulatedIntradayTrade] = {}
        self.closed_trades: List[SimulatedIntradayTrade] = []

        self._persist_budget()

    def _persist_budget(self):
        """Write current budget state to the shadow_budgets table."""
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO shadow_budgets
                    (id, session_id, initial_budget, current_cash, invested_amount,
                     total_realized_pnl, trades_count, status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
                """,
                    (
                        f"budget_{self.session_id}",
                        self.session_id,
                        self.initial_budget,
                        round(self.available_cash, 2),
                        round(self.invested_amount, 2),
                        round(self.total_realized_pnl, 2),
                        self.trades_count,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
        except Exception:
            pass

    def open_paper_trade(
        self,
        plan: IntradayTradePlan,
        fill_price: Optional[float] = None,
        shares: Optional[int] = None,
    ) -> Optional[SimulatedIntradayTrade]:
        """
        Opens a simulated paper trade from an IntradayTradePlan.
        Shares are calculated from position_sizing_pct of the initial budget
        unless explicitly provided. Returns None if budget is insufficient.
        """
        actual_entry = fill_price or plan.entry_price
        if actual_entry <= 0:
            return None

        # Calculate shares from budget position sizing
        if shares is None:
            allocation = self.initial_budget * (plan.position_sizing_pct / 100.0)
            allocation = min(allocation, self.available_cash)
            if allocation <= 0:
                return None
            shares = max(1, math.floor(allocation / actual_entry))

        cost_basis = round(shares * actual_entry, 2)

        # Check if we have enough cash
        if cost_basis > self.available_cash:
            # Reduce shares to what we can afford
            shares = max(1, math.floor(self.available_cash / actual_entry))
            cost_basis = round(shares * actual_entry, 2)
            if cost_basis > self.available_cash:
                return None

        # Deduct from available cash
        self.available_cash = round(self.available_cash - cost_basis, 2)
        self.invested_amount = round(self.invested_amount + cost_basis, 2)
        self.trades_count += 1

        trade_id = str(uuid.uuid4())[:8]
        trade = SimulatedIntradayTrade(
            id=trade_id,
            ticker=plan.ticker.upper(),
            risk_profile=plan.risk_profile,
            entry_price=round(actual_entry, 2),
            entry_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            stop_loss_price=plan.stop_loss_price,
            target_1_price=plan.target_1_price,
            target_2_price=plan.target_2_price,
            status="OPEN",
            shares=shares,
            cost_basis=cost_basis,
        )

        self.active_trades[trade.id] = trade

        # Persist to shadow_trades table
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO shadow_trades
                    (id, ticker, entry_date, entry_price, stop_price, target_price, time_stop_days,
                     estimated_round_trip_cost_pct, policy_version, provenance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        trade.id,
                        trade.ticker,
                        datetime.now().strftime("%Y-%m-%d"),
                        trade.entry_price,
                        trade.stop_loss_price,
                        trade.target_1_price,
                        1,
                        trade.slippage_cost_pct,
                        f"INTRADAY_{plan.risk_profile}",
                        json.dumps(
                            {
                                "shares": shares,
                                "cost_basis": cost_basis,
                                **plan.to_dict(),
                            }
                        ),
                    ),
                )
                conn.commit()
        except Exception:
            pass

        self._persist_budget()
        return trade

    def _close_trade(
        self,
        trade: SimulatedIntradayTrade,
        exit_price: float,
        exit_reason: str,
        now_str: str,
    ):
        """Finalize a closed trade: compute P&L, restore cash, persist."""
        trade.exit_price = round(exit_price, 2)
        trade.exit_reason = exit_reason
        trade.exit_time = now_str

        gross = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
        trade.gross_pnl_pct = round(gross, 2)
        trade.net_pnl_pct = round(gross - trade.slippage_cost_pct, 2)

        # Dollar P&L
        proceeds = round(trade.shares * trade.exit_price, 2)
        slippage_dollars = round(
            trade.cost_basis * (trade.slippage_cost_pct / 100.0), 2
        )
        trade.realized_pnl_dollars = round(
            proceeds - trade.cost_basis - slippage_dollars, 2
        )

        # Restore cash
        self.available_cash = round(self.available_cash + proceeds, 2)
        self.invested_amount = round(self.invested_amount - trade.cost_basis, 2)
        self.total_realized_pnl = round(
            self.total_realized_pnl + trade.realized_pnl_dollars, 2
        )

        self.closed_trades.append(trade)
        if trade.id in self.active_trades:
            del self.active_trades[trade.id]

        # Update DB
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    """
                    UPDATE shadow_trades
                    SET status = 'CLOSED', exit_date = ?, exit_price = ?, exit_reason = ?,
                        realized_return_pct = ?, closed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (
                        datetime.now().strftime("%Y-%m-%d"),
                        trade.exit_price,
                        trade.exit_reason,
                        trade.net_pnl_pct,
                        trade.id,
                    ),
                )
                conn.commit()
        except Exception:
            pass

        self._persist_budget()

    def update_with_tick(
        self, ticker: str, current_price: float, current_time_str: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Updates open trades for the given ticker against the latest market tick.
        Checks for stop breaches, target hits, or time-based exits.
        """
        ticker = ticker.upper()
        now_str = current_time_str or datetime.now().strftime("%H:%M:%S")
        events = []

        trades_to_close = []

        for trade_id, trade in self.active_trades.items():
            if trade.ticker != ticker or trade.status != "OPEN":
                continue

            # Check Stop Loss Breach
            if current_price <= trade.stop_loss_price:
                trade.status = "STOP_HIT"
                trades_to_close.append((trade, trade.stop_loss_price, "STOP_LOSS"))
                events.append(
                    {
                        "trade_id": trade.id,
                        "ticker": trade.ticker,
                        "event": "STOP_LOSS_TRIGGERED",
                        "price": current_price,
                        "pnl_pct": trade.net_pnl_pct,
                    }
                )
                continue

            # Check Profit Target 2
            if trade.target_2_price and current_price >= trade.target_2_price:
                trade.status = "TARGET_HIT"
                trades_to_close.append((trade, trade.target_2_price, "TARGET_2"))
                events.append(
                    {
                        "trade_id": trade.id,
                        "ticker": trade.ticker,
                        "event": "TARGET_2_TRIGGERED",
                        "price": current_price,
                        "pnl_pct": trade.net_pnl_pct,
                    }
                )
                continue

            # Check Profit Target 1
            if current_price >= trade.target_1_price:
                trade.status = "TARGET_HIT"
                trades_to_close.append((trade, trade.target_1_price, "TARGET_1"))
                events.append(
                    {
                        "trade_id": trade.id,
                        "ticker": trade.ticker,
                        "event": "TARGET_1_TRIGGERED",
                        "price": current_price,
                        "pnl_pct": trade.net_pnl_pct,
                    }
                )
                continue

        # Finalize closed trades
        for trade, exit_price, reason in trades_to_close:
            self._close_trade(trade, exit_price, reason, now_str)

        return events

    def force_eod_exit(
        self, current_prices: Dict[str, float]
    ) -> List[SimulatedIntradayTrade]:
        """
        Forces liquidation of all open intraday positions at the end of the day (15:55 EST).
        """
        now_str = datetime.now().strftime("%H:%M:%S")
        closed = []

        for trade_id, trade in list(self.active_trades.items()):
            exit_price = current_prices.get(trade.ticker, trade.entry_price)
            trade.status = "EOD_CLOSED"
            self._close_trade(trade, exit_price, "EOD_EXPIRATION", now_str)
            closed.append(trade)

        return closed

    def force_exit_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_reason: str,
        current_time_str: Optional[str] = None,
    ):
        """
        Force-closes a single open trade at a given price. Used when the AI
        agent (or external signal) decides to exit immediately rather than
        waiting for the threshold check in update_with_tick.
        """
        trade = self.active_trades.get(trade_id)
        if not trade or trade.status != "OPEN":
            return
        now_str = current_time_str or datetime.now().strftime("%H:%M:%S")
        self._close_trade(trade, exit_price, exit_reason, now_str)

    def get_budget_summary(self) -> Dict[str, Any]:
        """Returns current budget state for display."""
        open_value = sum(t.shares * t.entry_price for t in self.active_trades.values())
        return {
            "initial_budget": self.initial_budget,
            "available_cash": round(self.available_cash, 2),
            "invested_amount": round(self.invested_amount, 2),
            "open_positions_value": round(open_value, 2),
            "total_realized_pnl": round(self.total_realized_pnl, 2),
            "trades_count": self.trades_count,
            "portfolio_value": round(self.available_cash + self.invested_amount, 2),
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Calculates cumulative trading performance metrics."""
        budget = self.get_budget_summary()

        if not self.closed_trades:
            return {
                **budget,
                "total_trades": 0,
                "open_trades": len(self.active_trades),
                "win_rate_pct": 0.0,
                "avg_return_pct": 0.0,
                "profit_factor": 0.0,
                "total_realized_pnl_pct": 0.0,
            }

        wins = [t for t in self.closed_trades if t.net_pnl_pct > 0]
        losses = [t for t in self.closed_trades if t.net_pnl_pct <= 0]

        win_rate = (len(wins) / len(self.closed_trades)) * 100
        avg_ret = sum(t.net_pnl_pct for t in self.closed_trades) / len(
            self.closed_trades
        )
        gross_gains = sum(t.net_pnl_pct for t in wins)
        gross_losses = abs(sum(t.net_pnl_pct for t in losses))
        profit_factor = (
            round(gross_gains / gross_losses, 2)
            if gross_losses > 0
            else (99.0 if gross_gains > 0 else 1.0)
        )

        return {
            **budget,
            "total_trades": len(self.closed_trades),
            "open_trades": len(self.active_trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate_pct": round(win_rate, 1),
            "avg_return_pct": round(avg_ret, 2),
            "profit_factor": profit_factor,
            "total_realized_pnl_pct": round(
                sum(t.net_pnl_pct for t in self.closed_trades), 2
            ),
        }
