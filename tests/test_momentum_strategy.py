import numpy as np
import pandas as pd

from core.momentum_strategy import (
    MomentumConfig,
    backtest,
    build_target_portfolio,
    compute_signals,
    market_regime,
)


def make_frame(growth, days=420, volume=2_000_000):
    index = pd.bdate_range("2023-01-02", periods=days)
    close = 100 * (1 + growth) ** np.arange(days)
    return pd.DataFrame(
        {
            "Open": close * 0.999,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Adj Close": close,
            "Volume": volume,
        },
        index=index,
    )


def test_momentum_signal_uses_skip_period_and_is_point_in_time():
    frames = {"FAST": make_frame(0.003), "SLOW": make_frame(0.001)}
    config = MomentumConfig(minimum_dollar_volume=1_000_000)
    as_of = frames["FAST"].index[-1]
    before = compute_signals(frames, as_of=as_of, config=config)

    changed = {ticker: frame.copy() for ticker, frame in frames.items()}
    changed["FAST"].iloc[-10:, changed["FAST"].columns.get_loc("Close")] *= 5
    changed["FAST"].iloc[-10:, changed["FAST"].columns.get_loc("Adj Close")] *= 5
    after = compute_signals(changed, as_of=as_of, config=config)

    before_fast = next(signal for signal in before if signal.ticker == "FAST")
    after_fast = next(signal for signal in after if signal.ticker == "FAST")
    assert before_fast.returns == after_fast.returns

    future = {ticker: frame.copy() for ticker, frame in frames.items()}
    extra_index = pd.bdate_range(
        frames["FAST"].index[-1] + pd.Timedelta(days=1), periods=10
    )
    extra = make_frame(0.2, days=10)
    extra.index = extra_index
    future["FAST"] = pd.concat([future["FAST"], extra])
    earlier = compute_signals(future, as_of=as_of, config=config)
    assert (
        next(signal for signal in earlier if signal.ticker == "FAST").returns
        == before_fast.returns
    )


def test_risk_adjusted_rank_and_regime_gate_target_weights():
    frames = {
        "FAST": make_frame(0.004),
        "MEDIUM": make_frame(0.002),
        "SLOW": make_frame(0.0005),
        "SPY": make_frame(0.001),
    }
    config = MomentumConfig(
        minimum_dollar_volume=1_000_000,
        entry_percentile=0.66,
        retention_percentile=0.50,
        maximum_positions=2,
    )
    signals = compute_signals(frames, config=config)
    assert (
        next(signal for signal in signals if signal.ticker == "FAST").percentile_rank
        >= next(signal for signal in signals if signal.ticker == "SLOW").percentile_rank
    )
    assert market_regime(frames["SPY"]) == "RISK_ON"
    target = build_target_portfolio(signals, frames["SPY"], config=config)
    assert target["gross_exposure"] > 0
    assert target["cash_weight"] >= 0
    assert all(
        position["target_weight"] <= config.maximum_position_weight
        for position in target["positions"]
    )


def test_backtest_reports_costs_and_benchmark():
    frames = {
        "FAST": make_frame(0.003),
        "SLOW": make_frame(0.001),
        "SPY": make_frame(0.0015),
    }
    config = MomentumConfig(minimum_dollar_volume=1_000_000, maximum_positions=1)
    result = backtest(frames, frames["SPY"], config=config)
    assert result.strategy_id == "cross_sectional_momentum_12_1_v1"
    assert result.rebalances > 0
    assert result.net_return_pct <= result.gross_return_pct
    assert result.average_turnover_pct >= 0
