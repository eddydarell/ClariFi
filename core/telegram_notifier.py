#!/usr/bin/env python3
"""
Telegram Notifier — sends trade signals and decisions to a Telegram chat.
Plugs into the EventBus to receive trade.opened / trade.closed / decision.made events.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from event_emitter import (
    EventBus,
    EVENT_DECISION_MADE,
    EVENT_TRADE_OPENED,
    EVENT_TRADE_CLOSED,
    EVENT_TRADE_STOP_TIGHTENED,
)

try:
    import urllib.request
    import urllib.parse

    _HAS_URLLIB = True
except ImportError:
    _HAS_URLLIB = False

try:
    import requests as _requests

    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


class TelegramNotifier:
    """
    Sends formatted notifications to Telegram via Bot API.

    Environment variables:
        TELEGRAM_BOT_TOKEN  — Bot token from @BotFather
        TELEGRAM_CHAT_ID    — Target chat/channel ID

    Usage:
        notifier = TelegramNotifier()   # reads env vars
        notifier.start_listening()      # hooks into EventBus

    Or manually:
        notifier.send("AAPL BUY at $195.50")
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        send_decisions: bool = True,
        send_trades: bool = True,
        send_budget_updates: bool = False,
        verbose: bool = False,
    ):
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
        self.send_decisions = send_decisions
        self.send_trades = send_trades
        self.send_budget_updates = send_budget_updates
        self.verbose = verbose
        self._enabled = bool(self.bot_token and self.chat_id)

        if not self._enabled:
            logger.info(
                "TelegramNotifier disabled: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable"
            )

    @property
    def enabled(self) -> bool:
        return self._enabled

    def send(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a raw message to Telegram. Returns True on success."""
        if not self._enabled:
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps(
            {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            }
        ).encode("utf-8")

        headers = {"Content-Type": "application/json"}

        try:
            if _HAS_REQUESTS:
                resp = _requests.post(
                    url,
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": True,
                    },
                    timeout=10,
                )
                return resp.status_code == 200
            elif _HAS_URLLIB:
                req = urllib.request.Request(
                    url, data=payload, headers=headers, method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.status == 200
            else:
                logger.warning("No HTTP library available (requests or urllib)")
                return False
        except Exception as exc:
            logger.warning("Telegram send failed: %s", exc)
            return False

    def _format_trade_opened(self, data: Dict[str, Any]) -> str:
        ticker = data.get("ticker", "?")
        price = data.get("price", 0)
        profile = data.get("risk_profile", "?")
        confidence = data.get("confidence", 0) * 100
        plan = data.get("plan", {})
        stop = plan.get("stop_loss_price", 0)
        target = plan.get("target_1_price", 0)
        shares = data.get("shares", "?")
        budget = data.get("budget_remaining")

        lines = [
            f"<b>🟢 BUY {ticker}</b>",
            f"Price: <code>${price:.2f}</code>  |  Shares: <code>{shares}</code>",
            f"Profile: {profile}  |  Confidence: {confidence:.0f}%",
            f"Stop: <code>${stop:.2f}</code>  |  Target: <code>${target:.2f}</code>",
        ]
        if budget is not None:
            lines.append(f"Budget remaining: <code>${budget:,.2f}</code>")
        return "\n".join(lines)

    def _format_trade_closed(self, data: Dict[str, Any]) -> str:
        ticker = data.get("ticker", "?")
        price = data.get("price", 0)
        action = data.get("action", "?")
        pnl = data.get("pnl_pct", 0)
        reason = data.get("reason", "")
        budget = data.get("budget_remaining")

        emoji = "🔴" if pnl < 0 else "🟢"
        lines = [
            f"<b>{emoji} {action} {ticker}</b>",
            f"Exit: <code>${price:.2f}</code>  |  P&L: <b>{pnl:+.2f}%</b>",
        ]
        if reason:
            lines.append(f"Reason: {reason}")
        if budget is not None:
            lines.append(f"Budget remaining: <code>${budget:,.2f}</code>")
        return "\n".join(lines)

    def _format_decision(self, data: Dict[str, Any]) -> str:
        ticker = data.get("ticker", "?")
        action = data.get("action", "?")
        confidence = data.get("confidence", 0) * 100
        reasoning = data.get("reasoning_list", [])

        lines = [f"<b>🤖 {action} {ticker}</b> ({confidence:.0f}%)"]
        for r in reasoning[:3]:
            lines.append(f"  • {r}")
        return "\n".join(lines)

    def _on_trade_opened(self, data: Dict[str, Any]):
        if self.send_trades:
            msg = self._format_trade_opened(data)
            self.send(msg)

    def _on_trade_closed(self, data: Dict[str, Any]):
        if self.send_trades:
            msg = self._format_trade_closed(data)
            self.send(msg)

    def _on_decision(self, data: Dict[str, Any]):
        if self.send_decisions and data.get("action") not in ("HOLD",):
            msg = self._format_decision(data)
            self.send(msg)

    def start_listening(self, event_bus: Optional[EventBus] = None):
        """Register as listener on the EventBus."""
        bus = event_bus or EventBus.get_instance()
        if self.send_trades:
            bus.on(EVENT_TRADE_OPENED, self._on_trade_opened)
            bus.on(EVENT_TRADE_CLOSED, self._on_trade_closed)
            bus.on(EVENT_TRADE_STOP_TIGHTENED, self._on_trade_closed)
        if self.send_decisions:
            bus.on(EVENT_DECISION_MADE, self._on_decision)
