#!/usr/bin/env python3
"""
Lightweight Event Bus for ClariFi intraday trading.
Provides publish/subscribe event emission so trade decisions and lifecycle
events can be hooked to external notifiers (Telegram, Slack, webhooks, etc.).
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Canonical event names
EVENT_DECISION_MADE = "decision.made"
EVENT_TRADE_OPENED = "trade.opened"
EVENT_TRADE_CLOSED = "trade.closed"
EVENT_TRADE_STOP_TIGHTENED = "trade.stop_tightened"
EVENT_BUDGET_UPDATED = "budget.updated"
EVENT_SESSION_STARTED = "session.started"
EVENT_SESSION_ENDED = "session.ended"


class EventBus:
    """
    Thread-safe publish/subscribe event bus.

    Usage:
        bus = EventBus.get_instance()
        bus.on("trade.opened", my_callback)
        bus.emit("trade.opened", {"ticker": "AAPL", "price": 195.50})
    """

    _instance: Optional["EventBus"] = None
    _lock_class = threading.Lock()

    def __init__(self):
        self._listeners: Dict[str, List[Callable[[Dict[str, Any]], None]]] = (
            defaultdict(list)
        )
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "EventBus":
        """Singleton accessor."""
        if cls._instance is None:
            with cls._lock_class:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton (useful for testing)."""
        with cls._lock_class:
            cls._instance = None

    def on(self, event_name: str, callback: Callable[[Dict[str, Any]], None]):
        """Register a listener for an event type."""
        with self._lock:
            self._listeners[event_name].append(callback)

    def off(self, event_name: str, callback: Callable[[Dict[str, Any]], None]):
        """Remove a specific listener."""
        with self._lock:
            if event_name in self._listeners:
                try:
                    self._listeners[event_name].remove(callback)
                except ValueError:
                    pass

    def off_all(self, event_name: Optional[str] = None):
        """Remove all listeners for an event, or all listeners entirely."""
        with self._lock:
            if event_name:
                self._listeners.pop(event_name, None)
            else:
                self._listeners.clear()

    def emit(self, event_name: str, data: Optional[Dict[str, Any]] = None):
        """
        Fire all listeners for an event type.
        Each callback is invoked in a try/except so one failing listener
        never breaks the trading loop.
        """
        data = data or {}
        data["_event"] = event_name

        with self._lock:
            callbacks = list(self._listeners.get(event_name, []))

        for cb in callbacks:
            try:
                cb(data)
            except Exception as exc:
                logger.warning(
                    "EventBus listener %s for '%s' failed: %s", cb, event_name, exc
                )

    def listener_count(self, event_name: Optional[str] = None) -> int:
        """Count registered listeners."""
        with self._lock:
            if event_name:
                return len(self._listeners.get(event_name, []))
            return sum(len(v) for v in self._listeners.values())
