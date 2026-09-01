from types import SimpleNamespace

from core.shadow_trade_tracker import ShadowTradeTracker
from database.models import DatabaseManager


def make_plan():
    return SimpleNamespace(
        entry_price=100.0, stop_price=95.0, target_price=110.0,
        time_stop_days=3, estimated_round_trip_cost_pct=0.2,
    )


def test_shadow_trade_closes_at_stop_before_target_on_same_bar(tmp_path):
    db = DatabaseManager(str(tmp_path / 'shadow.db'))
    tracker = ShadowTradeTracker(db)
    trade_id = tracker.open_trade('TEST', '2026-01-02', make_plan(), {'policy_version': 'swing-v1'})
    db.upsert_ticker_price_rows('TEST', [{
        'price_date': '2026-01-05', 'open': 100.0, 'high': 112.0, 'low': 94.0,
        'close': 105.0, 'adj_close': 105.0, 'volume': 1_000_000,
    }])

    resolved = tracker.resolve_open_trades('TEST')

    assert resolved[0]['id'] == trade_id
    assert resolved[0]['exit_reason'] == 'STOP'
    assert resolved[0]['exit_price'] == 95.0
    assert resolved[0]['realized_return_pct'] == -5.2


def test_shadow_trade_closes_at_time_stop_after_configured_bars(tmp_path):
    db = DatabaseManager(str(tmp_path / 'shadow.db'))
    tracker = ShadowTradeTracker(db)
    tracker.open_trade('TEST', '2026-01-02', make_plan())
    db.upsert_ticker_price_rows('TEST', [
        {'price_date': '2026-01-05', 'open': 100.0, 'high': 105.0, 'low': 98.0, 'close': 102.0, 'adj_close': 102.0, 'volume': 1_000_000},
        {'price_date': '2026-01-06', 'open': 102.0, 'high': 106.0, 'low': 99.0, 'close': 103.0, 'adj_close': 103.0, 'volume': 1_000_000},
        {'price_date': '2026-01-07', 'open': 103.0, 'high': 107.0, 'low': 100.0, 'close': 104.0, 'adj_close': 104.0, 'volume': 1_000_000},
    ])

    resolved = tracker.resolve_open_trades('TEST')

    assert resolved[0]['exit_reason'] == 'TIME_STOP'
    assert resolved[0]['exit_price'] == 104.0
    assert resolved[0]['realized_return_pct'] == 3.8