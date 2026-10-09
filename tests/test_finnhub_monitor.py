import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from database.models import DatabaseManager
from intraday_agent import AutonomousIntradayAgent
from intraday_monitor import IntradayLoopMonitor
from intraday_simulator import IntradaySimulator
from intraday_strategy import DualIntradayReport, IntradayTradePlan


class FakeWsClient:
    def __init__(self, price):
        self.price = price
        self.subscribed = []
        self.started = False
        self.closed = False

    def subscribe(self, symbols):
        self.subscribed.extend(symbols)

    def start(self):
        self.started = True

    def get_quote(self, ticker, max_age_seconds=300.0):
        return {
            "symbol": ticker,
            "price": self.price,
            "provider": "finnhub_ws",
            "freshness": "real_time",
            "timestamp": "2026-09-07T15:00:00+00:00",
        }

    def close(self):
        self.closed = True


class FakeQuoteProvider:
    def __init__(self, price=None):
        self.price = price
        self.calls = 0

    def get_quote(self, ticker):
        self.calls += 1
        return {
            "symbol": ticker,
            "price": self.price,
            "provider": "finnhub",
            "freshness": "real_time",
        }


class FakeMarketStatusProvider:
    def __init__(
        self,
        minutes,
        session="regular",
        is_open=True,
        holiday=None,
        market_time=None,
        timezone="America/New_York",
    ):
        self.minutes = minutes
        self.session = session
        self.is_open = is_open
        self.holiday = holiday
        self.market_time = market_time
        self.timezone = timezone

    def get_status(self, exchange="US"):
        return {
            "exchange": exchange,
            "is_open": self.is_open,
            "session": self.session,
            "holiday": self.holiday,
            "t": int(self.market_time.timestamp()) if self.market_time else None,
            "timezone": self.timezone,
        }

    def minutes_to_close(self, exchange="US"):
        return self.minutes


def _plan(profile, ticker):
    kwargs = dict(
        risk_profile=profile,
        ticker=ticker,
        action="BUY",
        entry_price=10.0,
        entry_window="09:30-10:30",
        entry_condition="breakout",
        stop_loss_price=10.5,
        stop_loss_pct=5.0,
        target_1_price=11.0,
        target_1_pct=10.0,
        target_2_price=12.0,
        target_2_pct=20.0,
        trailing_stop_activation_price=10.5,
        evening_exit_time="15:55 EST",
        risk_per_share=0.5,
        reward_per_share=1.0,
        risk_reward_ratio=2.0,
        position_sizing_pct=10.0,
        reasons=["r"],
        valid=True,
    )
    return IntradayTradePlan(**kwargs)


class FakeStrategyGen:
    def generate_for_ticker(self, ticker):
        report = DualIntradayReport(
            ticker=ticker,
            current_price=10.0,
            intraday_odds_score=70.0,
            timestamp="t",
            high_risk_strategy=_plan("HIGH_RISK", ticker),
            low_risk_strategy=_plan("LOW_RISK", ticker),
            candidate_summary={
                "vwap": 10.0,
                "rvol": 1.5,
                "atr": 0.2,
                "atr_pct": 2.0,
                "gap_pct": 1.0,
            },
        )
        return report


def test_poll_uses_websocket_price_over_rest():
    ws = FakeWsClient(price=11.05)
    rest = FakeQuoteProvider(price=12.99)
    monitor = IntradayLoopMonitor(
        quote_provider=rest,
        websocket_client=ws,
        strategy_gen=FakeStrategyGen(),
        agent=AutonomousIntradayAgent(),
        poll_interval_seconds=1,
        enable_shadow_trading=False,
    )
    monitor.add_stocks(["AAAA"], profile="HIGH_RISK")
    monitor.poll_once()

    state = monitor.monitored_stocks["AAAA"]
    assert state.current_price == 11.05
    assert rest.calls == 0
    assert ws.subscribed == ["AAAA"]
    assert ws.started is True


def test_market_status_zero_drives_eod_commit(tmp_path):
    db_path = str(tmp_path / "test.db")
    db = DatabaseManager(db_path=db_path)
    sim = IntradaySimulator(db_manager=db, initial_budget=1000.0)
    ws = FakeWsClient(price=11.05)
    rest = FakeQuoteProvider(price=12.99)
    monitor = IntradayLoopMonitor(
        quote_provider=rest,
        websocket_client=ws,
        strategy_gen=FakeStrategyGen(),
        agent=AutonomousIntradayAgent(),
        simulator=sim,
        poll_interval_seconds=1,
        enable_shadow_trading=True,
        market_status_provider=FakeMarketStatusProvider(minutes=0),
    )
    monitor.add_stocks(["BBBB"], profile="HIGH_RISK")
    state = monitor.monitored_stocks["BBBB"]
    state.shadow_trade = sim.open_paper_trade(state.active_plan, fill_price=10.0)
    state.state = "ENTERED"
    state.entry_price = 10.0
    assert len(sim.active_trades) == 1

    monitor.poll_once()

    assert monitor.monitored_stocks["BBBB"].state == "EOD_CLOSED"
    assert len(sim.active_trades) == 0
    assert sim.total_realized_pnl > 0
    assert ws.subscribed == ["BBBB"]


def test_no_market_status_falls_back_to_legacy_clock():
    ws = FakeWsClient(price=11.05)
    rest = FakeQuoteProvider(price=None)
    monitor = IntradayLoopMonitor(
        quote_provider=rest,
        websocket_client=ws,
        strategy_gen=FakeStrategyGen(),
        agent=AutonomousIntradayAgent(),
        poll_interval_seconds=1,
        enable_shadow_trading=False,
    )
    minutes = monitor._compute_minutes_to_close()  # noqa: SLF001
    assert 0 <= minutes < 24 * 60


def test_holiday_market_blocks_entries_and_banners(tmp_path):
    db_path = str(tmp_path / "test.db")
    db = DatabaseManager(db_path=db_path)
    sim = IntradaySimulator(db_manager=db, initial_budget=1000.0)
    ws = FakeWsClient(price=11.05)
    rest = FakeQuoteProvider(price=12.99)
    provider = FakeMarketStatusProvider(
        minutes=None, session=None, is_open=False, holiday="Labor Day"
    )
    monitor = IntradayLoopMonitor(
        quote_provider=rest,
        websocket_client=ws,
        strategy_gen=FakeStrategyGen(),
        agent=AutonomousIntradayAgent(),
        simulator=sim,
        poll_interval_seconds=1,
        enable_shadow_trading=True,
        market_status_provider=provider,
    )
    monitor.add_stocks(["CCCC"], profile="HIGH_RISK")
    assert monitor.market_state["tradable"] is False
    assert "Labor Day" in monitor.market_state["label"]
    assert monitor.monitored_stocks["CCCC"].state == "WATCHING"
    assert len(sim.active_trades) == 0

    events = monitor.poll_once()
    assert monitor.monitored_stocks["CCCC"].state == "WATCHING"
    assert len(sim.active_trades) == 0
    assert events == []


def test_closed_market_flattens_open_positions(tmp_path):
    db_path = str(tmp_path / "test.db")
    db = DatabaseManager(db_path=db_path)
    sim = IntradaySimulator(db_manager=db, initial_budget=1000.0)
    ws = FakeWsClient(price=10.20)
    rest = FakeQuoteProvider(price=None)
    provider = FakeMarketStatusProvider(
        minutes=None, session=None, is_open=False, holiday="Labor Day"
    )
    monitor = IntradayLoopMonitor(
        quote_provider=rest,
        websocket_client=ws,
        strategy_gen=FakeStrategyGen(),
        agent=AutonomousIntradayAgent(),
        simulator=sim,
        poll_interval_seconds=1,
        enable_shadow_trading=True,
        market_status_provider=provider,
    )
    monitor.add_stocks(["DDDD"], profile="HIGH_RISK")
    state = monitor.monitored_stocks["DDDD"]
    # Simulate a position that was opened during a regular session.
    state.state = "ENTERED"
    state.entry_price = 10.0
    state.shadow_trade = sim.open_paper_trade(state.active_plan, fill_price=10.0)
    assert len(sim.active_trades) == 1

    events = monitor.poll_once()

    assert state.state == "EOD_CLOSED"
    assert len(sim.active_trades) == 0
    assert events == [
        {"ticker": "DDDD", "action": "MARKET_CLOSED", "price": 10.20, "pnl_pct": 2.0}
    ]


def test_premarket_session_not_tradable(tmp_path):
    ws = FakeWsClient(price=11.05)
    rest = FakeQuoteProvider(price=12.99)
    provider = FakeMarketStatusProvider(
        minutes=300, session="pre-market", is_open=False
    )
    monitor = IntradayLoopMonitor(
        quote_provider=rest,
        websocket_client=ws,
        strategy_gen=FakeStrategyGen(),
        agent=AutonomousIntradayAgent(),
        poll_interval_seconds=1,
        enable_shadow_trading=False,
        market_status_provider=provider,
    )
    monitor.add_stocks(["EEEE"], profile="HIGH_RISK")
    assert monitor.market_state["tradable"] is False
    assert monitor.monitored_stocks["EEEE"].state == "WATCHING"
