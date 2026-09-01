"""Paper-trade lifecycle tracking for validated long-entry recommendations."""

from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from database.models import DatabaseManager


class ShadowTradeTracker:
    """Stores and resolves long-only paper trades against persisted OHLCV bars."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()

    def process_strategy(
        self,
        ticker: str,
        strategy: Any,
        entry_date: str,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        resolved = self.resolve_open_trades(ticker)
        trade_id = None
        if strategy.action == 'BUY' and strategy.decision_status == 'ACTIONABLE' and strategy.trade_plan:
            trade_id = self.open_trade(ticker, entry_date, strategy.trade_plan, provenance)
        return {'resolved': resolved, 'new_trade_id': trade_id}

    def open_trade(
        self,
        ticker: str,
        entry_date: str,
        trade_plan: Any,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> str:
        if is_dataclass(trade_plan):
            plan = asdict(trade_plan)
        elif isinstance(trade_plan, dict):
            plan = trade_plan
        else:
            plan = vars(trade_plan)
        trade_id = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            conn.execute('''
                INSERT INTO shadow_trades
                (id, ticker, entry_date, entry_price, stop_price, target_price, time_stop_days,
                 estimated_round_trip_cost_pct, policy_version, provenance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_id, ticker.upper(), entry_date, plan['entry_price'], plan['stop_price'],
                plan['target_price'], plan['time_stop_days'], plan['estimated_round_trip_cost_pct'],
                (provenance or {}).get('policy_version'), json.dumps(provenance or {}),
            ))
            conn.commit()
        return trade_id

    def resolve_open_trades(self, ticker: str) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            open_trades = [dict(row) for row in conn.execute('''
                SELECT * FROM shadow_trades
                WHERE ticker = ? AND status = 'OPEN'
                ORDER BY entry_date ASC
            ''', (ticker.upper(),))]

        prices = self.db.get_ticker_prices(ticker)
        resolved: List[Dict[str, Any]] = []
        for trade in open_trades:
            future_bars = [row for row in prices if row['price_date'] > trade['entry_date']]
            for bar_index, bar in enumerate(future_bars, start=1):
                # When both thresholds occur in a daily bar, take the adverse stop outcome.
                if bar['low'] is not None and float(bar['low']) <= trade['stop_price']:
                    resolved.append(self._close_trade(trade, bar, 'STOP'))
                    break
                if bar['high'] is not None and float(bar['high']) >= trade['target_price']:
                    resolved.append(self._close_trade(trade, bar, 'TARGET'))
                    break
                if bar_index >= trade['time_stop_days'] and bar['close'] is not None:
                    resolved.append(self._close_trade(trade, bar, 'TIME_STOP'))
                    break
        return resolved

    def _close_trade(self, trade: Dict[str, Any], bar: Dict[str, Any], reason: str) -> Dict[str, Any]:
        exit_price = (
            trade['stop_price'] if reason == 'STOP' else
            trade['target_price'] if reason == 'TARGET' else float(bar['close'])
        )
        gross_return_pct = ((exit_price / trade['entry_price']) - 1) * 100
        realized_return_pct = round(gross_return_pct - trade['estimated_round_trip_cost_pct'], 4)
        with self.db.get_connection() as conn:
            conn.execute('''
                UPDATE shadow_trades
                SET status = 'CLOSED', exit_date = ?, exit_price = ?, exit_reason = ?,
                    realized_return_pct = ?, closed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (bar['price_date'], exit_price, reason, realized_return_pct, trade['id']))
            conn.commit()
        return {
            'id': trade['id'], 'ticker': trade['ticker'], 'exit_date': bar['price_date'],
            'exit_price': exit_price, 'exit_reason': reason,
            'realized_return_pct': realized_return_pct,
        }