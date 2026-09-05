#!/usr/bin/env python3
"""
Intraday Paper / Shadow Trade Simulator
Tracks paper trades initiated from intraday strategies with simulated fills,
slippage, stop-loss breaks, target triggers, and EOD auto-liquidation.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
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
    exit_reason: Optional[str] = None  # 'TARGET_1', 'TARGET_2', 'STOP_LOSS', 'EOD_EXPIRATION'
    gross_pnl_pct: float = 0.0
    net_pnl_pct: float = 0.0
    shares: int = 100
    slippage_cost_pct: float = 0.05  # 0.05% estimated round-trip slippage & fees

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IntradaySimulator:
    """
    Manages intraday paper trade lifecycles, persists orders, and evaluates tick updates.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager(os.environ.get("CLARIFI_DB_PATH", "clarifi.db"))
        self.active_trades: Dict[str, SimulatedIntradayTrade] = {}
        self.closed_trades: List[SimulatedIntradayTrade] = []

    def open_paper_trade(
        self,
        plan: IntradayTradePlan,
        fill_price: Optional[float] = None,
        shares: int = 100
    ) -> SimulatedIntradayTrade:
        """
        Opens a simulated paper trade from an IntradayTradePlan.
        """
        trade_id = str(uuid.uuid4())[:8]
        actual_entry = fill_price or plan.entry_price

        trade = SimulatedIntradayTrade(
            id=trade_id,
            ticker=plan.ticker.upper(),
            risk_profile=plan.risk_profile,
            entry_price=round(actual_entry, 2),
            entry_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            stop_loss_price=plan.stop_loss_price,
            target_1_price=plan.target_1_price,
            target_2_price=plan.target_2_price,
            status='OPEN',
            shares=shares
        )

        self.active_trades[trade.id] = trade

        # Persist to database if shadow_trades table exists
        try:
            with self.db.get_connection() as conn:
                conn.execute('''
                    INSERT INTO shadow_trades
                    (id, ticker, entry_date, entry_price, stop_price, target_price, time_stop_days,
                     estimated_round_trip_cost_pct, policy_version, provenance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade.id,
                    trade.ticker,
                    datetime.now().strftime("%Y-%m-%d"),
                    trade.entry_price,
                    trade.stop_loss_price,
                    trade.target_1_price,
                    1,  # Intraday = 1 day time stop
                    trade.slippage_cost_pct,
                    f"INTRADAY_{plan.risk_profile}",
                    json.dumps(plan.to_dict()),
                ))
                conn.commit()
        except Exception:
            pass  # Non-fatal if database schema is not migrated yet

        return trade

    def update_with_tick(self, ticker: str, current_price: float, current_time_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Updates open trades for the given ticker against the latest market tick.
        Checks for stop breaches, target hits, or time-based exits.
        """
        ticker = ticker.upper()
        now_str = current_time_str or datetime.now().strftime("%H:%M:%S")
        events = []

        trades_to_close = []

        for trade_id, trade in self.active_trades.items():
            if trade.ticker != ticker or trade.status != 'OPEN':
                continue

            # Check Stop Loss Breach
            if current_price <= trade.stop_loss_price:
                trade.status = 'STOP_HIT'
                trade.exit_price = trade.stop_loss_price
                trade.exit_reason = 'STOP_LOSS'
                trade.exit_time = now_str
                trades_to_close.append(trade)
                events.append({
                    'trade_id': trade.id,
                    'ticker': trade.ticker,
                    'event': 'STOP_LOSS_TRIGGERED',
                    'price': current_price,
                    'pnl_pct': trade.net_pnl_pct
                })
                continue

            # Check Profit Target 2
            if trade.target_2_price and current_price >= trade.target_2_price:
                trade.status = 'TARGET_HIT'
                trade.exit_price = trade.target_2_price
                trade.exit_reason = 'TARGET_2'
                trade.exit_time = now_str
                trades_to_close.append(trade)
                events.append({
                    'trade_id': trade.id,
                    'ticker': trade.ticker,
                    'event': 'TARGET_2_TRIGGERED',
                    'price': current_price,
                    'pnl_pct': trade.net_pnl_pct
                })
                continue

            # Check Profit Target 1
            if current_price >= trade.target_1_price:
                trade.status = 'TARGET_HIT'
                trade.exit_price = trade.target_1_price
                trade.exit_reason = 'TARGET_1'
                trade.exit_time = now_str
                trades_to_close.append(trade)
                events.append({
                    'trade_id': trade.id,
                    'ticker': trade.ticker,
                    'event': 'TARGET_1_TRIGGERED',
                    'price': current_price,
                    'pnl_pct': trade.net_pnl_pct
                })
                continue

        # Finalize closed trades
        for trade in trades_to_close:
            gross = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
            trade.gross_pnl_pct = round(gross, 2)
            trade.net_pnl_pct = round(gross - trade.slippage_cost_pct, 2)

            self.closed_trades.append(trade)
            if trade.id in self.active_trades:
                del self.active_trades[trade.id]

            # Update DB
            try:
                with self.db.get_connection() as conn:
                    conn.execute('''
                        UPDATE shadow_trades
                        SET status = 'CLOSED', exit_date = ?, exit_price = ?, exit_reason = ?,
                            realized_return_pct = ?, closed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        datetime.now().strftime("%Y-%m-%d"),
                        trade.exit_price,
                        trade.exit_reason,
                        trade.net_pnl_pct,
                        trade.id
                    ))
                    conn.commit()
            except Exception:
                pass

        return events

    def force_eod_exit(self, current_prices: Dict[str, float]) -> List[SimulatedIntradayTrade]:
        """
        Forces liquidation of all open intraday positions at the end of the day (15:55 EST).
        """
        now_str = datetime.now().strftime("%H:%M:%S")
        closed = []

        for trade_id, trade in list(self.active_trades.items()):
            exit_price = current_prices.get(trade.ticker, trade.entry_price)
            trade.status = 'EOD_CLOSED'
            trade.exit_price = round(exit_price, 2)
            trade.exit_reason = 'EOD_EXPIRATION'
            trade.exit_time = now_str

            gross = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
            trade.gross_pnl_pct = round(gross, 2)
            trade.net_pnl_pct = round(gross - trade.slippage_cost_pct, 2)

            self.closed_trades.append(trade)
            closed.append(trade)
            del self.active_trades[trade_id]

        return closed

    def get_performance_summary(self) -> Dict[str, Any]:
        """Calculates cumulative trading performance metrics."""
        if not self.closed_trades:
            return {
                'total_trades': 0,
                'open_trades': len(self.active_trades),
                'win_rate_pct': 0.0,
                'avg_return_pct': 0.0,
                'profit_factor': 0.0,
                'total_realized_pnl_pct': 0.0
            }

        wins = [t for t in self.closed_trades if t.net_pnl_pct > 0]
        losses = [t for t in self.closed_trades if t.net_pnl_pct <= 0]

        win_rate = (len(wins) / len(self.closed_trades)) * 100
        avg_ret = sum(t.net_pnl_pct for t in self.closed_trades) / len(self.closed_trades)
        gross_gains = sum(t.net_pnl_pct for t in wins)
        gross_losses = abs(sum(t.net_pnl_pct for t in losses))
        profit_factor = round(gross_gains / gross_losses, 2) if gross_losses > 0 else (99.0 if gross_gains > 0 else 1.0)

        return {
            'total_trades': len(self.closed_trades),
            'open_trades': len(self.active_trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate_pct': round(win_rate, 1),
            'avg_return_pct': round(avg_ret, 2),
            'profit_factor': profit_factor,
            'total_realized_pnl_pct': round(sum(t.net_pnl_pct for t in self.closed_trades), 2)
        }
