#!/usr/bin/env python3
"""
Decision Logger — persistent audit trail for intraday agent decisions.
Writes to the decision_logs DB table and optionally to a JSON-lines file.
Supports CSV export for post-session analysis.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from database.models import DatabaseManager

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from intraday_agent import AgentDecision, IntradayAgentContext


class DecisionLogger:
    """
    Persists every agent decision to the database and optionally to a JSONL file.
    Supports session grouping and CSV export.
    """

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        session_id: Optional[str] = None,
        log_dir: Optional[str] = None,
    ):
        self.db = db_manager or DatabaseManager(
            os.environ.get("CLARIFI_DB_PATH", "clarifi.db")
        )
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self._decisions: List[Dict[str, Any]] = []

        # Optional file-based logging
        self.log_dir = log_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "logs"
        )
        self._jsonl_path: Optional[str] = None
        if self.log_dir:
            try:
                os.makedirs(self.log_dir, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                self._jsonl_path = os.path.join(
                    self.log_dir, f"decisions_{self.session_id}_{ts}.jsonl"
                )
            except OSError:
                self._jsonl_path = None

    def log(
        self,
        decision: AgentDecision,
        context: Optional[IntradayAgentContext] = None,
        budget_info: Optional[Dict[str, Any]] = None,
    ):
        """Write a single decision to DB and in-memory buffer."""
        record = {
            "id": str(uuid.uuid4())[:12],
            "session_id": self.session_id,
            "ticker": decision.ticker,
            "action": decision.action,
            "price": decision.suggested_price,
            "confidence": decision.confidence,
            "risk_profile": decision.risk_profile,
            "reasoning": json.dumps(decision.reasoning),
            "context": json.dumps(context.to_dict() if context else {}),
            "budget_info": json.dumps(budget_info) if budget_info else None,
            "timestamp": decision.timestamp,
            "created_at": datetime.now().isoformat(),
        }
        self._decisions.append(record)

        # Persist to DB
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO decision_logs
                    (id, ticker, action, price, confidence, reasoning, context, session_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        record["id"],
                        record["ticker"],
                        record["action"],
                        record["price"],
                        record["confidence"],
                        record["reasoning"],
                        record["context"],
                        record["session_id"],
                        record["created_at"],
                    ),
                )
                conn.commit()
        except Exception:
            pass  # Non-fatal if table does not exist yet

        # Append to JSONL file
        if self._jsonl_path:
            try:
                with open(self._jsonl_path, "a") as f:
                    f.write(json.dumps(record) + "\n")
            except OSError:
                pass

    def get_decisions(
        self, ticker: Optional[str] = None, action: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve decisions from the in-memory buffer with optional filters."""
        results = self._decisions
        if ticker:
            results = [d for d in results if d["ticker"] == ticker.upper()]
        if action:
            results = [d for d in results if d["action"] == action.upper()]
        return results

    def export_csv(self, filepath: Optional[str] = None) -> str:
        """
        Export the current session's decisions to CSV.
        Returns the path to the written file.
        """
        if not filepath:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(
                self.log_dir or ".", f"decisions_{self.session_id}_{ts}.csv"
            )

        headers = [
            "id",
            "session_id",
            "created_at",
            "ticker",
            "action",
            "price",
            "confidence",
            "risk_profile",
            "reasoning",
        ]

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for record in self._decisions:
                writer.writerow({h: record.get(h, "") for h in headers})

        return filepath

    def summary(self) -> Dict[str, Any]:
        """Quick session summary."""
        total = len(self._decisions)
        if total == 0:
            return {"session_id": self.session_id, "total_decisions": 0}

        actions = {}
        tickers = set()
        for d in self._decisions:
            act = d["action"]
            actions[act] = actions.get(act, 0) + 1
            tickers.add(d["ticker"])

        buys = sum(1 for d in self._decisions if d["action"] == "BUY")
        sells = sum(
            1
            for d in self._decisions
            if d["action"] in ("TAKE_PROFIT", "STOP_LOSS_EXIT", "FORCE_EOD_EXIT")
        )

        return {
            "session_id": self.session_id,
            "total_decisions": total,
            "tickers_monitored": sorted(tickers),
            "action_counts": actions,
            "buy_count": buys,
            "exit_count": sells,
            "jsonl_path": self._jsonl_path,
        }
