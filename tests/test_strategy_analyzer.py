import sys
import os
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
from strategy_analyzer import (
    StrategyAnalyzer,
    StrategyRecommendation,
    PricePrediction,
    OptimalMoment,
)


def make_price_data(start_price, daily_change_pct, num_days=120, volatility=0.01):
    """Generate synthetic OHLCV data with a trend and noise."""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=num_days, freq='B')
    n = len(dates)
    trend = np.linspace(0, daily_change_pct * n / 100, n)
    noise = np.random.normal(0, volatility, n)
    close = start_price * (1 + trend + noise)
    close = np.maximum(close, 1.0)
    return pd.DataFrame({
        'Open': close * (1 + np.random.uniform(-0.005, 0.005, n)),
        'High': close * (1 + np.abs(np.random.normal(0, 0.01, n))),
        'Low': close * (1 - np.abs(np.random.normal(0, 0.01, n))),
        'Close': close,
        'Volume': np.random.randint(1000000, 10000000, n),
    }, index=dates)


@pytest.fixture
def analyzer():
    return StrategyAnalyzer()


class TestInsufficientData:
    def test_returns_hold_with_low_confidence(self, analyzer):
        data = make_price_data(100, 0.1, num_days=30)
        result = analyzer.generate_strategy("TEST", data)

        assert result.action == 'HOLD'
        assert result.confidence == 'LOW'
        assert result.timeframe == 'N/A'
        assert result.predictions == {}
        assert result.risk_level == 'UNKNOWN'

    def test_insufficient_data_message(self, analyzer):
        data = make_price_data(100, 0.1, num_days=50)
        result = analyzer.generate_strategy("TEST", data)

        assert any('Insufficient data' in r for r in result.rationale)
        assert '60' in result.rationale[0]


class TestScoringBoundaries:
    def test_trending_up_gives_buy(self, analyzer):
        data = make_price_data(100, 20, num_days=120, volatility=0.002)
        result = analyzer.generate_strategy(
            "BULL", data,
            technical_indicators={'MACD': 1.0, 'MACD_Signal': 0.0, 'RSI_14': 55},
        )

        score = result.key_metrics['overall_score']
        assert score >= 40, f"Expected score >= 40 for uptrend, got {score}"
        assert result.action == 'BUY'

    def test_trending_down_gives_sell(self, analyzer):
        data = make_price_data(120, -30, num_days=120, volatility=0.002)
        result = analyzer.generate_strategy(
            "BEAR", data,
            technical_indicators={'MACD': -1.0, 'MACD_Signal': 0.0, 'RSI_14': 72},
        )

        score = result.key_metrics['overall_score']
        assert score <= -40, f"Expected score <= -40 for downtrend, got {score}"
        assert result.action == 'SELL'

    def test_sideways_gives_hold(self, analyzer):
        np.random.seed(99)
        dates = pd.date_range(end=datetime.now(), periods=120, freq='B')
        n = len(dates)
        noise = np.random.normal(0, 0.003, n)
        close = 100 * (1 + noise)
        close = np.maximum(close, 1.0)
        data = pd.DataFrame({
            'Open': close * (1 + np.random.uniform(-0.002, 0.002, n)),
            'High': close * (1 + np.abs(np.random.normal(0, 0.005, n))),
            'Low': close * (1 - np.abs(np.random.normal(0, 0.005, n))),
            'Close': close,
            'Volume': np.random.randint(1000000, 10000000, n),
        }, index=dates)

        result = analyzer.generate_strategy("FLAT", data)
        assert result.action == 'HOLD'

    def test_actionable_signal_exposes_independent_evidence(self, analyzer):
        data = make_price_data(100, 20, num_days=120, volatility=0.002)
        result = analyzer.generate_strategy(
            "BULL", data,
            technical_indicators={'MACD': 1.0, 'MACD_Signal': 0.0, 'RSI_14': 55},
        )

        assert result.action == 'BUY'
        assert result.decision_status == 'ACTIONABLE'
        assert 'trend_bullish' in result.evidence_tags
        assert result.evidence_score == len(result.evidence_tags)

    def test_high_evidence_threshold_suppresses_actionable_signal(self, analyzer):
        data = make_price_data(100, 20, num_days=120, volatility=0.002)
        result = analyzer.generate_strategy(
            "BULL", data,
            technical_indicators={'MACD': 1.0, 'MACD_Signal': 0.0, 'RSI_14': 55},
            evidence_threshold=10,
        )

        assert result.action == 'HOLD'
        assert result.decision_status == 'SUPPRESSED'
        assert result.gate_reasons == ['Insufficient independent evidence (3/10)']

    def test_actionable_signal_includes_bounded_trade_plan(self, analyzer):
        data = make_price_data(100, 20, num_days=120, volatility=0.002)
        result = analyzer.generate_strategy(
            "BULL", data,
            technical_indicators={'MACD': 1.0, 'MACD_Signal': 0.0, 'RSI_14': 55},
        )

        plan = result.trade_plan
        assert plan is not None
        assert plan.action == 'BUY'
        assert plan.stop_price < plan.entry_price < plan.target_price
        assert plan.time_stop_days >= 1
        assert plan.risk_per_share > 0
        assert plan.risk_reward_ratio > 0


class TestPredictions:
    def test_prediction_keys_exist(self, analyzer):
        data = make_price_data(100, 5, num_days=120)
        result = analyzer.generate_strategy("TEST", data)

        assert 'short_term' in result.predictions
        assert 'mid_term' in result.predictions
        assert 'long_term' in result.predictions

    def test_prediction_required_fields(self, analyzer):
        data = make_price_data(100, 5, num_days=120)
        result = analyzer.generate_strategy("TEST", data)

        for key in ('short_term', 'mid_term', 'long_term'):
            pred = result.predictions[key]
            assert hasattr(pred, 'predicted_price')
            assert hasattr(pred, 'price_lower_bound')
            assert hasattr(pred, 'price_upper_bound')
            assert hasattr(pred, 'confidence')
            assert hasattr(pred, 'reasoning')
            assert isinstance(pred.predicted_price, (int, float))
            assert isinstance(pred.confidence, str)
            assert isinstance(pred.reasoning, list)

    def test_predictions_include_volatility_adjusted_price_bounds(self, analyzer):
        data = make_price_data(100, 5, num_days=120)
        result = analyzer.generate_strategy("TEST", data)

        for key in ('short_term', 'mid_term', 'long_term'):
            prediction = result.predictions[key]
            volatility_pct = result.key_metrics['volatility']['volatility_20d']
            expected_margin = (
                volatility_pct / np.sqrt(252) / 100
                * np.sqrt(prediction.horizon_days)
                * result.entry_price
            )
            assert prediction.price_lower_bound == pytest.approx(
                max(0.01, prediction.predicted_price - expected_margin)
            )
            assert prediction.price_upper_bound == pytest.approx(
                prediction.predicted_price + expected_margin
            )

    def test_predicted_price_is_positive(self, analyzer):
        data = make_price_data(100, 5, num_days=120)
        result = analyzer.generate_strategy("TEST", data)

        for pred in result.predictions.values():
            assert pred.predicted_price > 0, (
                f"predicted_price must be positive, got {pred.predicted_price}"
            )

    def test_short_term_confidence_higher_than_long_term(self, analyzer):
        data = make_price_data(100, 10, num_days=120, volatility=0.005)
        result = analyzer.generate_strategy("TEST", data)

        hierarchy = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        short = hierarchy[result.predictions['short_term'].confidence]
        long = hierarchy[result.predictions['long_term'].confidence]
        assert short >= long, (
            f"Short-term confidence ({result.predictions['short_term'].confidence}) "
            f"should be >= long-term ({result.predictions['long_term'].confidence})"
        )


class TestOptimalMoment:
    def test_optimal_moment_not_none_when_requested(self, analyzer):
        data = make_price_data(100, 15, num_days=120, volatility=0.005)
        result = analyzer.generate_strategy("TEST", data, find_optimum=True)

        assert result.optimal_moment is not None

    def test_optimal_moment_not_set_by_default(self, analyzer):
        data = make_price_data(100, 15, num_days=120)
        result = analyzer.generate_strategy("TEST", data, find_optimum=False)

        assert result.optimal_moment is None

    def test_optimal_moment_required_fields(self, analyzer):
        data = make_price_data(100, 15, num_days=120, volatility=0.005)
        result = analyzer.generate_strategy("TEST", data, find_optimum=True)
        moment = result.optimal_moment

        assert hasattr(moment, 'action')
        assert hasattr(moment, 'optimal_date')
        assert hasattr(moment, 'confidence')
        assert hasattr(moment, 'reasoning')
        assert hasattr(moment, 'risk_reward_ratio')

        assert moment.action in ('BUY', 'SELL', 'HOLD')
        assert moment.confidence in ('HIGH', 'MEDIUM', 'LOW')
        assert isinstance(moment.reasoning, list)
        assert isinstance(moment.risk_reward_ratio, (int, float))
        assert moment.risk_reward_ratio > 0

    def test_optimal_date_is_valid_date_string(self, analyzer):
        data = make_price_data(100, 15, num_days=120, volatility=0.005)
        result = analyzer.generate_strategy("TEST", data, find_optimum=True)
        date_str = result.optimal_moment.optimal_date

        parsed = datetime.strptime(date_str, '%Y-%m-%d')
        assert parsed.date() > datetime.now().date()
        assert parsed <= datetime.now() + pd.Timedelta(days=366)

    def test_buy_and_sell_optimal_moments_are_future_dates(self, analyzer):
        data = make_price_data(100, 15, num_days=120, volatility=0.005)
        result = analyzer.generate_strategy("TEST", data, find_optimum=True)

        assert set(result.optimal_moments) == {'buy', 'sell'}
        for moment in result.optimal_moments.values():
            assert moment.action in {'BUY', 'SELL'}
            assert moment.days_from_now >= 1
            assert datetime.strptime(moment.optimal_date, '%Y-%m-%d').date() > datetime.now().date()


class TestRSIExtremes:
    def test_oversold_contributes_positive_score(self, analyzer):
        data = make_price_data(100, 5, num_days=120, volatility=0.005)
        result = analyzer.generate_strategy(
            "TEST", data,
            technical_indicators={'RSI_14': 25},
        )

        momentum = result.key_metrics['momentum']
        assert momentum['rsi_signal'] == 'OVERSOLD'
        assert momentum['rsi'] == 25
        assert 'Oversold conditions' in ' '.join(result.rationale)

    def test_overbought_reduces_score(self, analyzer):
        data = make_price_data(100, 5, num_days=120, volatility=0.005)
        result_with_ob = analyzer.generate_strategy(
            "TEST", data,
            technical_indicators={'RSI_14': 80},
        )

        result_neutral = analyzer.generate_strategy(
            "TEST", data,
            technical_indicators={'RSI_14': 50},
        )

        score_ob = result_with_ob.key_metrics['overall_score']
        score_neutral = result_neutral.key_metrics['overall_score']
        assert score_ob < score_neutral


class TestVolatilityImpact:
    def test_high_volatility_sets_high_risk(self, analyzer):
        data = make_price_data(100, 0, num_days=120, volatility=0.05)
        result = analyzer.generate_strategy("TEST", data)

        assert result.risk_level == 'HIGH'

    def test_high_volatility_reduces_score(self, analyzer):
        base_data = make_price_data(100, 10, num_days=120, volatility=0.002)
        ti = {'MACD': 1.0, 'MACD_Signal': 0.0, 'RSI_14': 55}

        result_base = analyzer.generate_strategy("TEST", base_data, technical_indicators=ti)

        high_vol_data = base_data.copy()
        np.random.seed(123)
        high_vol_data['Close'] = high_vol_data['Close'] * (
            1 + np.random.normal(0, 0.05, len(high_vol_data))
        )
        high_vol_data['Close'] = np.maximum(high_vol_data['Close'], 1.0)
        high_vol_data['Open'] = high_vol_data['Close'] * (1 + np.random.uniform(-0.005, 0.005, len(high_vol_data)))
        high_vol_data['High'] = high_vol_data['Close'] * (1 + np.abs(np.random.normal(0, 0.01, len(high_vol_data))))
        high_vol_data['Low'] = high_vol_data['Close'] * (1 - np.abs(np.random.normal(0, 0.01, len(high_vol_data))))

        result_high = analyzer.generate_strategy("TEST", high_vol_data, technical_indicators=ti)

        assert result_high.risk_level == 'HIGH'
        assert result_base.risk_level != 'HIGH'

    def test_low_volatility_sets_low_risk(self, analyzer):
        data = make_price_data(100, 5, num_days=120, volatility=0.003)
        result = analyzer.generate_strategy("TEST", data)

        assert result.risk_level == 'LOW'


class TestDaysToMonth:
    def test_same_month_returns_near_365(self, analyzer):
        current_month = datetime.now().month
        days = analyzer._calculate_days_to_month(current_month, current_month)
        assert days >= 300, f"Same month should return ~365 days (next year), got {days}"

    def test_next_month_returns_near_30(self, analyzer):
        current_month = datetime.now().month
        next_month = (current_month % 12) + 1
        days = analyzer._calculate_days_to_month(current_month, next_month)
        assert 1 <= days <= 62, f"Next month should return ~30 days, got {days}"

    def test_always_returns_at_least_1(self, analyzer):
        for target in range(1, 13):
            current = datetime.now().month
            days = analyzer._calculate_days_to_month(current, target)
            assert days >= 1


class TestMultiTimeframe:
    def test_has_expected_keys(self, analyzer):
        data = make_price_data(100, 5, num_days=120)
        result = analyzer.generate_strategy("TEST", data)

        mt = result.key_metrics
        assert 'trend' in mt
        assert 'momentum' in mt
        assert 'volatility' in mt
        assert 'risk_metrics' in mt

    def test_win_rates_between_0_and_100(self, analyzer):
        data = make_price_data(100, 5, num_days=120)
        analyzer_obj = StrategyAnalyzer()
        closes = data['Close']

        timeframes = analyzer_obj._analyze_multi_timeframe(data)
        for tf_name, tf_data in timeframes.items():
            wr = tf_data['win_rate']
            assert 0 <= wr <= 100, (
                f"{tf_name} win_rate {wr} out of [0, 100]"
            )

    def test_multi_timeframe_returns_populated(self, analyzer):
        data = make_price_data(100, 5, num_days=120)
        timeframes = analyzer._analyze_multi_timeframe(data)

        assert len(timeframes) > 0
        for tf_name, tf_data in timeframes.items():
            assert 'avg_return' in tf_data
            assert 'win_rate' in tf_data
