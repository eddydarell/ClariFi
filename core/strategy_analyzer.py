#!/usr/bin/env python3
"""
Strategy Analyzer Module
Generates time-sensitive investment strategies based on comprehensive analysis.
Combines seasonal data, backtesting results, KPIs, and trend analysis to suggest
actionable strategies like "BUY now and SELL in 2 days" or "HOLD for 2 months".
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import calendar
from dataclasses import asdict, is_dataclass, replace


@dataclass
class OptimalMoment:
    """Identifies optimal buy/sell moment based on comprehensive analysis."""
    action: str  # BUY or SELL
    optimal_date: str  # Best date for action (YYYY-MM-DD)
    days_from_now: int  # Days until optimal moment
    expected_price: float  # Expected price at optimal moment
    expected_return_pct: float  # Expected return from current price
    confidence: str  # HIGH, MEDIUM, LOW
    reasoning: List[str]  # Key factors for this timing
    supporting_signals: Dict[str, any]  # Technical/seasonal/pattern signals
    risk_reward_ratio: float  # Risk/reward ratio


@dataclass
class PricePrediction:
    """Price prediction for a specific timeframe."""
    timeframe: str  # "short_term", "mid_term", "long_term"
    horizon_days: int  # Number of days ahead
    target_date: str  # Predicted date
    predicted_price: float  # Predicted price
    predicted_change_pct: float  # Predicted percentage change
    price_lower_bound: float  # Fixed -10% margin from predicted price
    price_upper_bound: float  # Fixed +10% margin from predicted price
    confidence: str  # HIGH, MEDIUM, LOW
    reasoning: List[str]  # Factors contributing to prediction


@dataclass
class StrategyRecommendation:
    """Time-sensitive investment strategy recommendation."""
    ticker: str
    action: str  # BUY, SELL, HOLD
    timeframe: str  # e.g., "2 days", "1 week", "2 months"
    target_date: str  # Estimated target date
    confidence: str  # HIGH, MEDIUM, LOW
    rationale: List[str]  # List of reasons
    entry_price: float  # Current/suggested entry price
    expected_return_pct: Optional[float]  # Expected return percentage
    risk_level: str  # LOW, MEDIUM, HIGH
    key_metrics: Dict[str, any]  # Supporting metrics
    predictions: Dict[str, PricePrediction]  # Short/mid/long-term predictions
    optimal_moment: Optional['OptimalMoment'] = None  # Optimal buy/sell timing
    optimal_moments: Dict[str, OptimalMoment] = field(default_factory=dict)


class StrategyAnalyzer:
    """Analyzes market data to generate time-sensitive investment strategies."""

    def __init__(self):
        self.min_data_points = 60  # Minimum required data points

    def generate_strategy(
        self,
        ticker: str,
        data: pd.DataFrame,
        period: str = "1y",
        seasonal_analysis: Optional[Dict] = None,
        deep_analysis: Optional[Dict] = None,
        technical_indicators: Optional[Dict] = None,
        find_optimum: bool = False,
    ) -> StrategyRecommendation:
        """
        Generate a comprehensive investment strategy for a single ticker.

        Args:
            ticker: Stock ticker symbol
            data: DataFrame with OHLCV data
            period: Time period of data
            seasonal_analysis: Optional seasonal analysis results
            deep_analysis: Optional deep backtesting results
            technical_indicators: Optional technical indicator values
            find_optimum: If True, identify optimal buy/sell moment

        Returns:
            StrategyRecommendation with actionable strategy
        """
        if len(data) < self.min_data_points:
            return self._create_insufficient_data_strategy(ticker, data)

        if is_dataclass(seasonal_analysis):
            seasonal_analysis = asdict(seasonal_analysis)

        # Ensure datetime index
        df = data.copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Calculate current price and returns
        current_price = float(df['Close'].iloc[-1])
        df['Return'] = df['Close'].pct_change()

        # Gather all signals
        signals = self._gather_signals(
            ticker, df, seasonal_analysis, deep_analysis, technical_indicators
        )

        # Analyze multiple timeframes for strategy determination
        multi_timeframe = self._analyze_multi_timeframe(df)

        # Generate strategy based on signals
        strategy = self._synthesize_strategy(
            ticker=ticker,
            current_price=current_price,
            signals=signals,
            multi_timeframe=multi_timeframe,
            seasonal_analysis=seasonal_analysis,
            deep_analysis=deep_analysis,
            technical_indicators=technical_indicators,
        )

        # Find independent, future opportunities for both actions when requested.
        if find_optimum:
            strategy.optimal_moments = {
                'buy': self._find_optimal_moment(
                    ticker=ticker,
                    data=df,
                    current_price=current_price,
                    signals=signals,
                    multi_timeframe=multi_timeframe,
                    seasonal_analysis=seasonal_analysis,
                    deep_analysis=deep_analysis,
                    preferred_action='BUY',
                ),
                'sell': self._find_optimal_moment(
                    ticker=ticker,
                    data=df,
                    current_price=current_price,
                    signals=signals,
                    multi_timeframe=multi_timeframe,
                    seasonal_analysis=seasonal_analysis,
                    deep_analysis=deep_analysis,
                    preferred_action='SELL',
                ),
            }
            strategy.optimal_moment = strategy.optimal_moments.get(strategy.action.lower())
            if strategy.optimal_moment is None:
                strategy.optimal_moment = self._create_default_optimal_moment(
                    action='HOLD',
                    current_price=current_price,
                    signals=signals,
                )

        return strategy

    def _gather_signals(
        self,
        ticker: str,
        data: pd.DataFrame,
        seasonal_analysis: Optional[Dict],
        deep_analysis: Optional[Dict],
        technical_indicators: Optional[Dict],
    ) -> Dict[str, any]:
        """Gather all relevant signals for strategy generation."""
        signals = {
            'trend': self._analyze_trend_signal(data),
            'momentum': self._analyze_momentum_signal(data, technical_indicators),
            'volatility': self._analyze_volatility_signal(data),
            'seasonal': self._analyze_seasonal_signal(seasonal_analysis),
            'deep_backtest': self._analyze_deep_backtest_signal(deep_analysis),
            'technical': self._analyze_technical_signal(technical_indicators),
            'risk_metrics': self._calculate_risk_metrics(data),
        }

        return signals

    def _analyze_trend_signal(self, data: pd.DataFrame) -> Dict[str, any]:
        """Analyze trend direction and strength."""
        closes = data['Close']

        # Calculate various moving averages
        sma_10 = closes.rolling(10).mean()
        sma_20 = closes.rolling(20).mean()
        sma_50 = closes.rolling(50).mean()
        sma_200 = closes.rolling(200).mean() if len(closes) >= 200 else None

        current_price = closes.iloc[-1]

        # Short-term trend (10 vs 20 day)
        short_term_trend = "BULLISH" if sma_10.iloc[-1] > sma_20.iloc[-1] else "BEARISH"

        # Medium-term trend (20 vs 50 day)
        medium_term_trend = "BULLISH" if sma_20.iloc[-1] > sma_50.iloc[-1] else "BEARISH"

        # Long-term trend (if enough data)
        long_term_trend = None
        if sma_200 is not None and not pd.isna(sma_200.iloc[-1]):
            long_term_trend = "BULLISH" if sma_50.iloc[-1] > sma_200.iloc[-1] else "BEARISH"

        # Recent slope (last 30 days)
        recent = closes.tail(30)
        x = np.arange(len(recent))
        slope = np.polyfit(x, recent.values, 1)[0]
        slope_pct = (slope / recent.mean()) * 100

        return {
            'short_term': short_term_trend,
            'medium_term': medium_term_trend,
            'long_term': long_term_trend,
            'slope_pct': slope_pct,
            'above_sma_50': current_price > sma_50.iloc[-1],
            'above_sma_200': current_price > sma_200.iloc[-1] if sma_200 is not None else None,
        }

    def _analyze_momentum_signal(
        self, data: pd.DataFrame, technical_indicators: Optional[Dict]
    ) -> Dict[str, any]:
        """Analyze momentum indicators."""
        closes = data['Close']

        # Calculate RSI if not provided
        rsi = None
        if technical_indicators and 'RSI_14' in technical_indicators:
            rsi = technical_indicators['RSI_14']
        else:
            rsi = self._calculate_rsi(closes, 14)

        # Calculate MACD if not provided
        macd_signal = None
        if technical_indicators and 'MACD' in technical_indicators:
            macd = technical_indicators['MACD']
            macd_sig = technical_indicators.get('MACD_Signal', 0)
            macd_signal = "BULLISH" if macd > macd_sig else "BEARISH"

        # Rate of change
        roc_10 = ((closes.iloc[-1] / closes.iloc[-10]) - 1) * 100 if len(closes) >= 10 else 0

        return {
            'rsi': rsi,
            'rsi_signal': self._interpret_rsi(rsi),
            'macd_signal': macd_signal,
            'roc_10_day': roc_10,
        }

    def _analyze_volatility_signal(self, data: pd.DataFrame) -> Dict[str, any]:
        """Analyze volatility metrics."""
        returns = data['Close'].pct_change().dropna()

        # Historical volatility
        vol_20 = returns.tail(20).std() * np.sqrt(252) * 100
        vol_60 = returns.tail(60).std() * np.sqrt(252) * 100 if len(returns) >= 60 else vol_20

        # Recent vs historical
        vol_increasing = vol_20 > vol_60

        return {
            'volatility_20d': vol_20,
            'volatility_60d': vol_60,
            'vol_increasing': vol_increasing,
            'risk_level': 'HIGH' if vol_20 > 40 else 'MEDIUM' if vol_20 > 25 else 'LOW',
        }

    def _analyze_seasonal_signal(self, seasonal_analysis: Optional[Dict]) -> Dict[str, any]:
        """Extract signals from seasonal analysis."""
        if not seasonal_analysis:
            return {'available': False}

        if is_dataclass(seasonal_analysis):
            seasonal_analysis = asdict(seasonal_analysis)

        current_month = datetime.now().month
        next_month = (current_month % 12) + 1
        month_name = calendar.month_name[current_month]
        next_month_name = calendar.month_name[next_month]

        # Get monthly stats
        monthly_stats = seasonal_analysis.get('monthly_stats', {})
        current_month_stats = monthly_stats.get(month_name, {})
        next_month_stats = monthly_stats.get(next_month_name, {})

        # Best/worst months
        best_months = seasonal_analysis.get('best_months', [])
        worst_months = seasonal_analysis.get('worst_months', [])

        # Seasonal bias
        bias_score = seasonal_analysis.get('bias_score', 0)

        return {
            'available': True,
            'current_month': month_name,
            'current_month_avg_return': current_month_stats.get('avg_return', 0) if current_month_stats else 0,
            'next_month_avg_return': next_month_stats.get('avg_return', 0) if next_month_stats else 0,
            'is_best_month': month_name in best_months,
            'is_worst_month': month_name in worst_months,
            'next_is_best': next_month_name in best_months,
            'next_is_worst': next_month_name in worst_months,
            'seasonal_bias': bias_score,
        }

    def _analyze_deep_backtest_signal(self, deep_analysis: Optional[Dict]) -> Dict[str, any]:
        """Extract signals from deep backtesting analysis."""
        if not deep_analysis:
            return {'available': False}

        summary = deep_analysis.get('summary', {})
        precision = summary.get('coefficient_of_precision', 0)
        chunks_evaluated = summary.get('chunks_evaluated', 0)

        # Get latest chunk results if available
        chunks = deep_analysis.get('chunks', [])
        latest_chunk = chunks[-1] if chunks else None

        latest_accuracy = None
        latest_performance = None

        if latest_chunk:
            latest_accuracy = latest_chunk.get('accuracy_pct', 0)
            latest_performance = latest_chunk.get('strategy_return_pct', 0)

        return {
            'available': True,
            'precision': precision,
            'chunks_evaluated': chunks_evaluated,
            'latest_accuracy': latest_accuracy,
            'latest_performance': latest_performance,
            'reliable': precision > 0.6,  # Consider reliable if >60% precision
        }

    def _analyze_technical_signal(self, technical_indicators: Optional[Dict]) -> Dict[str, any]:
        """Extract signals from technical indicators."""
        if not technical_indicators:
            return {'available': False}

        # Extract key indicators
        adx = technical_indicators.get('ADX')
        williams_r = technical_indicators.get('Williams_%R')
        cci = technical_indicators.get('CCI')

        # Market regime
        regime = technical_indicators.get('market_regime', {})

        # Bollinger Band signal
        bb_upper = technical_indicators.get('BB_Upper')
        bb_lower = technical_indicators.get('BB_Lower')
        bb_middle = technical_indicators.get('BB_Middle')
        bb_width = technical_indicators.get('BB_Width')
        bb_signal = None
        if bb_upper and bb_lower and bb_middle:
            last_close = technical_indicators.get('_last_close')
            if last_close:
                bb_position = (last_close - bb_lower) / (bb_upper - bb_lower + 1e-10)
                if bb_position < 0.1:
                    bb_signal = 'OVERSOLD'
                elif bb_position > 0.9:
                    bb_signal = 'OVERBOUGHT'
                else:
                    bb_signal = 'NEUTRAL'

        return {
            'available': True,
            'adx': adx,
            'trend_strength': 'STRONG' if adx and adx > 25 else 'WEAK' if adx else None,
            'williams_r': williams_r,
            'cci': cci,
            'market_regime': regime.get('regime', 'UNKNOWN'),
            'bb_signal': bb_signal,
            'bb_width': bb_width,
        }

    def _calculate_risk_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate comprehensive risk metrics."""
        closes = data['Close']
        returns = closes.pct_change().dropna()

        # Max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative / running_max - 1)
        max_drawdown = drawdown.min() * 100

        # Sharpe ratio (annualized)
        avg_return = returns.mean() * 252
        std_return = returns.std() * np.sqrt(252)
        sharpe = avg_return / std_return if std_return > 0 else 0

        # Value at Risk (95%)
        var_95 = np.percentile(returns, 5) * 100

        return {
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'var_95': var_95,
        }

    def _analyze_multi_timeframe(self, data: pd.DataFrame) -> Dict[str, any]:
        """Analyze multiple timeframes to determine optimal holding period."""
        closes = data['Close']

        # Calculate returns for various forward periods
        timeframes = {}

        # Short-term (2-5 days)
        if len(closes) >= 5:
            returns_2d = []
            returns_5d = []
            for i in range(len(closes) - 5):
                returns_2d.append((closes.iloc[i+2] / closes.iloc[i] - 1) * 100)
                returns_5d.append((closes.iloc[i+5] / closes.iloc[i] - 1) * 100)
            timeframes['2_day'] = {
                'avg_return': np.mean(returns_2d),
                'win_rate': sum(1 for r in returns_2d if r > 0) / len(returns_2d) * 100,
            }
            timeframes['5_day'] = {
                'avg_return': np.mean(returns_5d),
                'win_rate': sum(1 for r in returns_5d if r > 0) / len(returns_5d) * 100,
            }

        # Medium-term (1-2 weeks)
        if len(closes) >= 10:
            returns_1w = []
            returns_2w = []
            for i in range(len(closes) - 7):
                returns_1w.append((closes.iloc[i+7] / closes.iloc[i] - 1) * 100)
            for i in range(len(closes) - 10):
                returns_2w.append((closes.iloc[i+10] / closes.iloc[i] - 1) * 100)
            timeframes['1_week'] = {
                'avg_return': np.mean(returns_1w) if returns_1w else 0,
                'win_rate': sum(1 for r in returns_1w if r > 0) / len(returns_1w) * 100 if returns_1w else 50,
            }
            if returns_2w:
                timeframes['2_week'] = {
                    'avg_return': np.mean(returns_2w),
                    'win_rate': sum(1 for r in returns_2w if r > 0) / len(returns_2w) * 100,
                }

        # Long-term (1-2 months)
        if len(closes) >= 40:
            returns_1m = []
            returns_2m = []
            for i in range(len(closes) - 40):
                returns_1m.append((closes.iloc[i+20] / closes.iloc[i] - 1) * 100)
                if i + 40 < len(closes):
                    returns_2m.append((closes.iloc[i+40] / closes.iloc[i] - 1) * 100)
            timeframes['1_month'] = {
                'avg_return': np.mean(returns_1m),
                'win_rate': sum(1 for r in returns_1m if r > 0) / len(returns_1m) * 100,
            }
            if returns_2m:
                timeframes['2_month'] = {
                    'avg_return': np.mean(returns_2m),
                    'win_rate': sum(1 for r in returns_2m if r > 0) / len(returns_2m) * 100,
                }

        return timeframes

    def _synthesize_strategy(
        self,
        ticker: str,
        current_price: float,
        signals: Dict[str, any],
        multi_timeframe: Dict[str, any],
        seasonal_analysis: Optional[Dict],
        deep_analysis: Optional[Dict],
        technical_indicators: Optional[Dict],
    ) -> StrategyRecommendation:
        """Synthesize all signals into a coherent strategy."""

        # Calculate overall score (-100 to +100)
        score = 0
        rationale = []
        confidence_factors = []

        # Trend signals (40% weight)
        trend = signals['trend']
        if trend['short_term'] == 'BULLISH':
            score += 15
            rationale.append(f"Short-term uptrend (SMA10 > SMA20)")
        else:
            score -= 15
            rationale.append(f"Short-term downtrend (SMA10 < SMA20)")

        if trend['medium_term'] == 'BULLISH':
            score += 15
        else:
            score -= 15

        if trend['long_term'] == 'BULLISH':
            score += 10
            confidence_factors.append('long_term_trend_aligned')
        elif trend['long_term'] == 'BEARISH':
            score -= 10

        # Momentum signals (25% weight)
        momentum = signals['momentum']
        rsi_signal = momentum['rsi_signal']
        if rsi_signal == 'OVERSOLD':
            score += 15
            rationale.append(f"Oversold conditions (RSI: {momentum['rsi']:.1f})")
            confidence_factors.append('oversold')
        elif rsi_signal == 'OVERBOUGHT':
            score -= 15
            rationale.append(f"Overbought conditions (RSI: {momentum['rsi']:.1f})")
        elif rsi_signal == 'NEUTRAL':
            score += 5

        if momentum['macd_signal'] == 'BULLISH':
            score += 10
        elif momentum['macd_signal'] == 'BEARISH':
            score -= 10

        # Seasonal signals (15% weight)
        seasonal = signals['seasonal']
        if seasonal['available']:
            if seasonal['next_is_best']:
                score += 10
                rationale.append(f"Entering historically strong month")
                confidence_factors.append('seasonal_tailwind')
            elif seasonal['next_is_worst']:
                score -= 10
                rationale.append(f"Entering historically weak month")

            if seasonal['seasonal_bias'] > 0.3:
                score += 5
            elif seasonal['seasonal_bias'] < -0.3:
                score -= 5

        # Deep backtest signals (10% weight)
        deep = signals['deep_backtest']
        if deep['available'] and deep['reliable']:
            if deep['latest_performance'] and deep['latest_performance'] > 5:
                score += 10
                confidence_factors.append('backtest_validated')
            elif deep['latest_performance'] and deep['latest_performance'] < -5:
                score -= 10

        # Volatility/Risk signals (10% weight)
        volatility = signals['volatility']
        if volatility['risk_level'] == 'HIGH':
            score -= 10
            rationale.append(f"High volatility environment")
        elif volatility['risk_level'] == 'LOW':
            score += 10
            rationale.append(f"Low volatility environment")

        # Determine action based on score
        if score >= 40:
            action = 'BUY'
        elif score <= -40:
            action = 'SELL'
        else:
            action = 'HOLD'

        # Determine timeframe based on multi-timeframe analysis
        timeframe, target_date, expected_return = self._determine_optimal_timeframe(
            action, multi_timeframe, seasonal, trend
        )

        # Determine confidence
        confidence = self._determine_confidence(score, confidence_factors, signals)

        # Determine risk level
        risk_level = volatility['risk_level']

        # Add more specific rationale
        if action == 'BUY':
            rationale.insert(0, f"BUY signal (score: {score}/100)")
        elif action == 'SELL':
            rationale.insert(0, f"SELL signal (score: {score}/100)")
        else:
            rationale.insert(0, f"HOLD signal (score: {score}/100) - Mixed signals")

        # Add risk context
        risk_metrics = signals['risk_metrics']
        if risk_metrics['max_drawdown'] < -20:
            rationale.append(f"Significant drawdown risk ({risk_metrics['max_drawdown']:.1f}%)")

        # Generate future predictions
        predictions = self._generate_predictions(
            current_price=current_price,
            signals=signals,
            multi_timeframe=multi_timeframe,
            seasonal=seasonal,
            score=score,
            trend=trend,
            momentum=momentum,
        )

        return StrategyRecommendation(
            ticker=ticker,
            action=action,
            timeframe=timeframe,
            target_date=target_date,
            confidence=confidence,
            rationale=rationale[:5],  # Top 5 reasons
            entry_price=current_price,
            expected_return_pct=expected_return,
            risk_level=risk_level,
            key_metrics={
                'overall_score': score,
                'trend': trend,
                'momentum': momentum,
                'volatility': volatility,
                'risk_metrics': risk_metrics,
            },
            predictions=predictions,
        )

    def _determine_optimal_timeframe(
        self,
        action: str,
        multi_timeframe: Dict[str, any],
        seasonal: Dict[str, any],
        trend: Dict[str, any],
    ) -> Tuple[str, str, Optional[float]]:
        """Determine optimal timeframe for the strategy."""

        if action == 'HOLD':
            return "Current", datetime.now().strftime('%Y-%m-%d'), 0.0

        # Analyze which timeframe has best risk/reward
        best_timeframe = None
        best_score = -999

        timeframe_map = {
            '2_day': ('2 days', 2),
            '5_day': ('5 days', 5),
            '1_week': ('1 week', 7),
            '2_week': ('2 weeks', 14),
            '1_month': ('1 month', 30),
            '2_month': ('2 months', 60),
        }

        for tf_key, (tf_label, days) in timeframe_map.items():
            if tf_key not in multi_timeframe:
                continue

            tf_data = multi_timeframe[tf_key]
            avg_return = tf_data['avg_return']
            win_rate = tf_data['win_rate']

            # Score combines return and win rate
            score = avg_return * (win_rate / 100)

            # Boost score if action matches expected direction
            if action == 'BUY' and avg_return > 0:
                score *= 1.5
            elif action == 'SELL' and avg_return < 0:
                score *= 1.5

            if score > best_score:
                best_score = score
                best_timeframe = (tf_label, days, avg_return)

        if best_timeframe:
            label, days, expected_return = best_timeframe
            target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            return label, target_date, expected_return

        # Default to 1 week if no data
        target_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        return "1 week", target_date, None

    def _determine_confidence(
        self, score: int, confidence_factors: List[str], signals: Dict[str, any]
    ) -> str:
        """Determine confidence level of the strategy."""

        # High confidence: strong score + multiple confirming factors
        if abs(score) >= 60 and len(confidence_factors) >= 2:
            return 'HIGH'

        # Low confidence: weak score or conflicting signals
        if abs(score) < 30:
            return 'LOW'

        # Check for conflicting signals
        trend = signals['trend']
        if trend['short_term'] != trend['medium_term']:
            return 'MEDIUM'

        return 'MEDIUM'

    def _interpret_rsi(self, rsi: Optional[float]) -> str:
        """Interpret RSI value."""
        if rsi is None or np.isnan(rsi):
            return 'NEUTRAL'
        if rsi < 30:
            return 'OVERSOLD'
        if rsi > 70:
            return 'OVERBOUGHT'
        return 'NEUTRAL'

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator."""
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        ema_up = up.ewm(com=period - 1, adjust=False).mean()
        ema_down = down.ewm(com=period - 1, adjust=False).mean()
        rs = ema_up / (ema_down + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not rsi.empty and not np.isnan(rsi.iloc[-1]) else 50.0

    def _generate_predictions(
        self,
        current_price: float,
        signals: Dict[str, any],
        multi_timeframe: Dict[str, any],
        seasonal: Dict[str, any],
        score: int,
        trend: Dict[str, any],
        momentum: Dict[str, any],
    ) -> Dict[str, PricePrediction]:
        """Generate short, mid, and long-term price predictions."""

        predictions = {}

        # Short-term prediction (5 days)
        short_term = self._predict_timeframe(
            timeframe="short_term",
            horizon_days=5,
            current_price=current_price,
            signals=signals,
            multi_timeframe=multi_timeframe,
            seasonal=seasonal,
            score=score,
            trend=trend,
            momentum=momentum,
            weight_trend=0.6,  # Heavy weight on recent trends
            weight_momentum=0.3,
            weight_seasonal=0.1,
        )
        predictions['short_term'] = short_term

        # Mid-term prediction (30 days / 1 month)
        mid_term = self._predict_timeframe(
            timeframe="mid_term",
            horizon_days=30,
            current_price=current_price,
            signals=signals,
            multi_timeframe=multi_timeframe,
            seasonal=seasonal,
            score=score,
            trend=trend,
            momentum=momentum,
            weight_trend=0.4,  # Balanced weights
            weight_momentum=0.3,
            weight_seasonal=0.3,
        )
        predictions['mid_term'] = mid_term

        # Long-term prediction (90 days / 3 months)
        long_term = self._predict_timeframe(
            timeframe="long_term",
            horizon_days=90,
            current_price=current_price,
            signals=signals,
            multi_timeframe=multi_timeframe,
            seasonal=seasonal,
            score=score,
            trend=trend,
            momentum=momentum,
            weight_trend=0.3,  # More weight on fundamentals
            weight_momentum=0.2,
            weight_seasonal=0.5,
        )
        predictions['long_term'] = long_term

        # Tracked horizons used for accuracy scoring (week/month/3mo/6mo/1yr).
        # 1_month and 3_month reuse the mid/long-term computations (30/90 days match exactly).
        predictions['1_week'] = self._predict_timeframe(
            timeframe="1_week",
            horizon_days=7,
            current_price=current_price,
            signals=signals,
            multi_timeframe=multi_timeframe,
            seasonal=seasonal,
            score=score,
            trend=trend,
            momentum=momentum,
            weight_trend=0.6,
            weight_momentum=0.3,
            weight_seasonal=0.1,
            bucket='short_term',
        )
        predictions['1_month'] = replace(mid_term, timeframe='1_month')
        predictions['3_month'] = replace(long_term, timeframe='3_month')
        predictions['6_month'] = self._predict_timeframe(
            timeframe="6_month",
            horizon_days=180,
            current_price=current_price,
            signals=signals,
            multi_timeframe=multi_timeframe,
            seasonal=seasonal,
            score=score,
            trend=trend,
            momentum=momentum,
            weight_trend=0.25,
            weight_momentum=0.15,
            weight_seasonal=0.6,
            bucket='long_term',
        )
        predictions['1_year'] = self._predict_timeframe(
            timeframe="1_year",
            horizon_days=365,
            current_price=current_price,
            signals=signals,
            multi_timeframe=multi_timeframe,
            seasonal=seasonal,
            score=score,
            trend=trend,
            momentum=momentum,
            weight_trend=0.2,
            weight_momentum=0.1,
            weight_seasonal=0.7,
            bucket='long_term',
        )

        return predictions

    def _predict_timeframe(
        self,
        timeframe: str,
        horizon_days: int,
        current_price: float,
        signals: Dict[str, any],
        multi_timeframe: Dict[str, any],
        seasonal: Dict[str, any],
        score: int,
        trend: Dict[str, any],
        momentum: Dict[str, any],
        weight_trend: float,
        weight_momentum: float,
        weight_seasonal: float,
        bucket: Optional[str] = None,
    ) -> PricePrediction:
        """Predict price for a specific timeframe using statistical methods.

        `bucket` selects which internal weighting/clamp regime to use
        (short_term/mid_term/long_term) when `timeframe` is a tracked-horizon
        label (e.g. "1_week") rather than one of those three literal buckets.
        """
        bucket = bucket or timeframe

        target_date = (datetime.now() + timedelta(days=horizon_days)).strftime('%Y-%m-%d')

        trend_prediction = 0.0
        momentum_prediction = 0.0
        seasonal_prediction = 0.0
        reasoning = []

        # --- Trend-based prediction via linear regression ---
        # Use the appropriate lookback for the timeframe
        lookback_map = {'short_term': 20, 'mid_term': 60, 'long_term': 120}
        lookback = lookback_map.get(bucket, 60)

        # We need the original data for regression, approximate from signals
        slope_pct = trend.get('slope_pct', 0)
        # Annualized slope projected to horizon
        # slope_pct is already a percent change per observed trading row.
        daily_slope_pct = slope_pct
        trend_prediction = daily_slope_pct * horizon_days

        # Clamp trend prediction to reasonable bounds
        max_trend_pct = 15.0 if bucket == 'long_term' else 8.0 if bucket == 'mid_term' else 4.0
        # Wider horizons within the long-term bucket get proportionally more room to move
        if horizon_days > 270:
            max_trend_pct = 30.0
        elif horizon_days > 150:
            max_trend_pct = 20.0
        trend_prediction = max(-max_trend_pct, min(max_trend_pct, trend_prediction))

        if trend_prediction > 0.5:
            reasoning.append(f"{'Strong ' if abs(slope_pct) > 1 else ''}upward trend ({slope_pct:.2f}%/month)")
        elif trend_prediction < -0.5:
            reasoning.append(f"{'Strong ' if abs(slope_pct) > 1 else ''}downward trend ({slope_pct:.2f}%/month)")

        # --- Momentum prediction using EMA-weighted signals ---
        rsi = momentum.get('rsi', 50)
        roc = momentum.get('roc_10_day', 0)

        # RSI mean reversion component (stronger for extreme values)
        if rsi < 30:
            momentum_prediction = (30 - rsi) * 0.15  # Scale with distance from oversold
            reasoning.append(f"Oversold RSI ({rsi:.0f}) — mean reversion expected")
        elif rsi > 70:
            momentum_prediction = (70 - rsi) * 0.15
            reasoning.append(f"Overbought RSI ({rsi:.0f}) — pullback expected")
        else:
            # Linear interpolation: RSI 50 = neutral, moving toward extremes
            momentum_prediction = (rsi - 50) * 0.05

        # ROC momentum (exponential decay — recent momentum persists but fades)
        roc_contribution = roc * 0.2 * np.exp(-horizon_days / 30.0)
        momentum_prediction += roc_contribution

        # MACD signal with decay
        if momentum.get('macd_signal') == 'BULLISH':
            macd_boost = 1.5 * np.exp(-horizon_days / 20.0)
            momentum_prediction += macd_boost
            if bucket == 'short_term':
                reasoning.append("MACD bullish crossover")
        elif momentum.get('macd_signal') == 'BEARISH':
            macd_drop = -1.5 * np.exp(-horizon_days / 20.0)
            momentum_prediction += macd_drop
            if bucket == 'short_term':
                reasoning.append("MACD bearish crossover")

        # --- Seasonal prediction with decay ---
        if seasonal and seasonal.get('available'):
            seasonal_bias = seasonal.get('seasonal_bias', 0)
            if bucket == 'long_term':
                seasonal_prediction = seasonal_bias * 8
                if seasonal.get('next_is_best'):
                    seasonal_prediction += 2.0
                    reasoning.append("Entering historically strong period")
                elif seasonal.get('next_is_worst'):
                    seasonal_prediction -= 2.0
                    reasoning.append("Entering historically weak period")
            else:
                next_month_return = seasonal.get('next_month_avg_return', 0)
                # Seasonal returns are decimal ratios; prediction components are percent.
                seasonal_prediction = next_month_return * 100 * 0.5

        # --- Blend with historical forward returns ---
        hist_key_map = {'short_term': '5_day', 'mid_term': '1_month', 'long_term': '2_month'}
        hist_key = hist_key_map.get(bucket)
        if hist_key and hist_key in multi_timeframe:
            hist_return = multi_timeframe[hist_key].get('avg_return', 0)
            # Weighted blend: more weight to statistical prediction for shorter horizons
            blend_weight = 0.3 if bucket == 'short_term' else 0.5 if bucket == 'mid_term' else 0.6
            trend_prediction = trend_prediction * (1 - blend_weight) + hist_return * blend_weight

        # --- Combine with configured weights ---
        predicted_change_pct = (
            trend_prediction * weight_trend +
            momentum_prediction * weight_momentum +
            seasonal_prediction * weight_seasonal
        )

        # --- Volatility-adjusted confidence intervals ---
        volatility = signals['volatility']
        vol_level = volatility.get('volatility_20d', 25)
        vol_daily = vol_level / np.sqrt(252)

        # Scale prediction magnitude by volatility regime
        if vol_level > 40:
            predicted_change_pct *= 1.2
            confidence = 'LOW'
        elif vol_level > 25:
            predicted_change_pct *= 1.1
            confidence = 'MEDIUM'
        else:
            confidence = 'HIGH'

        # --- Confidence refinement ---
        if abs(score) < 30:
            confidence = 'LOW'
        elif abs(score) >= 60:
            confidence = 'HIGH' if confidence != 'LOW' else 'MEDIUM'
        elif abs(score) >= 40:
            confidence = 'MEDIUM' if confidence == 'LOW' else confidence

        # Reduce confidence for longer horizons
        if horizon_days > 60 and confidence == 'HIGH':
            confidence = 'MEDIUM'
        elif horizon_days > 30 and confidence == 'MEDIUM':
            pass  # Keep MEDIUM

        # Calculate predicted price
        predicted_price = current_price * (1 + predicted_change_pct / 100)

        # Add risk context to reasoning
        risk_metrics = signals['risk_metrics']
        if risk_metrics['max_drawdown'] < -20:
            reasoning.append(f"High drawdown risk ({risk_metrics['max_drawdown']:.1f}%)")

        # Add confidence interval context
        margin = (vol_daily / 100) * np.sqrt(horizon_days) * current_price
        if margin > 0:
            reasoning.append(f"Expected range: ${predicted_price - margin:.2f} – ${predicted_price + margin:.2f}")

        reasoning = reasoning[:3]

        return PricePrediction(
            timeframe=timeframe,
            horizon_days=horizon_days,
            target_date=target_date,
            predicted_price=predicted_price,
            predicted_change_pct=predicted_change_pct,
            price_lower_bound=predicted_price * 0.90,
            price_upper_bound=predicted_price * 1.10,
            confidence=confidence,
            reasoning=reasoning,
        )

    def _find_optimal_moment(
        self,
        ticker: str,
        data: pd.DataFrame,
        current_price: float,
        signals: Dict[str, any],
        multi_timeframe: Dict[str, any],
        seasonal_analysis: Optional[Dict],
        deep_analysis: Optional[Dict],
        preferred_action: Optional[str] = None,
    ) -> OptimalMoment:
        """
        Identify the optimal buy/sell moment based on comprehensive analysis.

        This method analyzes:
        - Seasonal patterns to find best/worst months
        - Technical indicators for entry/exit points
        - Historical patterns and win rates
        - Risk-reward ratios
        - Price cycles and support/resistance
        """

        # Determine primary action based on overall trend
        trend = signals['trend']
        overall_bullish = (
            trend['short_term'] == 'BULLISH' and
            trend['medium_term'] == 'BULLISH'
        )

        # Initialize candidates for optimal moments
        buy_candidates = []
        sell_candidates = []

        # 1. SEASONAL ANALYSIS - Find best months
        if seasonal_analysis and seasonal_analysis.get('available'):
            best_months = seasonal_analysis.get('best_months', [])
            worst_months = seasonal_analysis.get('worst_months', [])
            monthly_stats = seasonal_analysis.get('monthly_stats', {})

            current_month = datetime.now().month
            current_month_name = calendar.month_name[current_month]

            # Find next best month for buying
            for i in range(1, 13):  # Look ahead 12 months
                future_month = ((current_month - 1 + i) % 12) + 1
                future_month_name = calendar.month_name[future_month]

                if future_month_name in best_months and monthly_stats.get(future_month_name):
                    stats = monthly_stats[future_month_name]
                    days_ahead = self._calculate_days_to_month(current_month, future_month)

                    buy_candidates.append({
                        'type': 'seasonal_buy',
                        'days_ahead': days_ahead,
                        'month': future_month_name,
                        'expected_return': stats.get('avg_return', 0),
                        'win_rate': stats.get('win_rate', 0),
                        'score': stats.get('avg_return', 0) * stats.get('win_rate', 0) / 100,
                    })
            # Find next worst month for selling
            for i in range(1, 13):
                future_month = ((current_month - 1 + i) % 12) + 1
                future_month_name = calendar.month_name[future_month]

                if future_month_name in worst_months and monthly_stats.get(future_month_name):
                    stats = monthly_stats[future_month_name]
                    days_ahead = self._calculate_days_to_month(current_month, future_month)

                    sell_candidates.append({
                        'type': 'seasonal_sell',
                        'days_ahead': days_ahead,
                        'month': future_month_name,
                        'expected_return': stats.get('avg_return', 0),
                        'win_rate': stats.get('win_rate', 0),
                        'score': abs(stats.get('avg_return', 0)) * stats.get('win_rate', 0) / 100,
                    })
        # 2. TECHNICAL ANALYSIS - RSI extremes
        momentum = signals['momentum']
        rsi = momentum.get('rsi', 50)

        if rsi < 35:  # Oversold - good buy opportunity
            buy_candidates.append({
                'type': 'technical_buy_oversold',
                'days_ahead': 0,  # Now
                'expected_return': 5.0,  # Historical mean reversion
                'win_rate': 65,
                'score': 3.25,
                'indicator': 'RSI Oversold',
            })
        elif rsi > 65:  # Overbought - good sell opportunity
            sell_candidates.append({
                'type': 'technical_sell_overbought',
                'days_ahead': 0,  # Now
                'expected_return': -3.0,
                'win_rate': 60,
                'score': 1.8,
                'indicator': 'RSI Overbought',
            })

        # 3. MULTI-TIMEFRAME ANALYSIS - Best performing timeframe
        best_timeframe = None
        best_win_rate = 0
        best_return = 0

        for tf_name, tf_data in multi_timeframe.items():
            win_rate = tf_data.get('win_rate', 0)
            avg_return = tf_data.get('avg_return', 0)

            if win_rate > best_win_rate and avg_return > 0:
                best_win_rate = win_rate
                best_return = avg_return
                best_timeframe = tf_name

        if best_timeframe and best_return > 2:
            # Map timeframe to days
            tf_days_map = {
                '2_day': 2, '5_day': 5, '1_week': 7,
                '2_week': 14, '1_month': 30, '2_month': 60
            }
            days = tf_days_map.get(best_timeframe, 7)

            buy_candidates.append({
                'type': 'pattern_buy',
                'days_ahead': 0,  # Buy now, hold for optimal period
                'hold_days': days,
                'expected_return': best_return,
                'win_rate': best_win_rate,
                'score': best_return * best_win_rate / 100,
                'timeframe': best_timeframe,
            })

        # 4. DEEP BACKTEST - Recent performance
        if deep_analysis and not deep_analysis.get('error'):
            latest_chunks = deep_analysis.get('latest_chunks', [])
            if latest_chunks:
                recent = latest_chunks[0]
                recent_return = recent.get('return_pct', 0)

                if recent_return > 3:
                    buy_candidates.append({
                        'type': 'backtest_buy',
                        'days_ahead': 0,
                        'expected_return': recent_return,
                        'win_rate': 55,
                        'score': recent_return * 0.55,
                    })
                elif recent_return < -3:
                    sell_candidates.append({
                        'type': 'backtest_sell',
                        'days_ahead': 0,
                        'expected_return': recent_return,
                        'win_rate': 55,
                        'score': abs(recent_return) * 0.55,
                    })

        # 5. SUPPORT/RESISTANCE LEVELS
        closes = data['Close']
        recent_high = closes.rolling(30).max().iloc[-1]
        recent_low = closes.rolling(30).min().iloc[-1]

        # If near support, consider buying
        if current_price <= recent_low * 1.02:  # Within 2% of support
            buy_candidates.append({
                'type': 'support_buy',
                'days_ahead': 0,
                'expected_return': ((recent_high - current_price) / current_price) * 100 * 0.5,
                'win_rate': 60,
                'score': 2.0,
                'level': 'Support',
            })

        # If near resistance, consider selling
        if current_price >= recent_high * 0.98:  # Within 2% of resistance
            sell_candidates.append({
                'type': 'resistance_sell',
                'days_ahead': 0,
                'expected_return': -2.5,
                'win_rate': 65,
                'score': 1.625,
                'level': 'Resistance',
            })

        # 6. BOLLINGER BAND SIGNALS
        technical = signals.get('technical', {})
        if technical.get('available'):
            bb_signal = technical.get('bb_signal')
            bb_width = technical.get('bb_width', 0)

            if bb_signal == 'OVERSOLD':
                buy_candidates.append({
                    'type': 'bollinger_buy',
                    'days_ahead': 0,
                    'expected_return': 4.0,
                    'win_rate': 62,
                    'score': 2.48,
                    'indicator': 'Bollinger Band oversold',
                })
            elif bb_signal == 'OVERBOUGHT':
                sell_candidates.append({
                    'type': 'bollinger_sell',
                    'days_ahead': 0,
                    'expected_return': -3.0,
                    'win_rate': 60,
                    'score': 1.8,
                    'indicator': 'Bollinger Band overbought',
                })

            # Squeeze detection — low bandwidth predicts breakout
            if bb_width is not None and bb_width < 5:
                buy_candidates.append({
                    'type': 'squeeze_breakout',
                    'days_ahead': 0,
                    'expected_return': 6.0,
                    'win_rate': 55,
                    'score': 3.3,
                    'indicator': 'Bollinger squeeze — breakout imminent',
                })

        # Select the requested action independently, or preserve the primary strategy
        # selection when this method is called without an action preference.
        if preferred_action == 'BUY':
            candidates = buy_candidates
            action = 'BUY'
            best_candidate = max(candidates, key=lambda x: x['score']) if candidates else None
        elif preferred_action == 'SELL':
            candidates = sell_candidates
            action = 'SELL'
            best_candidate = max(candidates, key=lambda x: x['score']) if candidates else None
        elif overall_bullish and buy_candidates:
            best_candidate = max(buy_candidates, key=lambda x: x['score'])
            action = 'BUY'
            candidates = buy_candidates
        elif not overall_bullish and sell_candidates:
            best_candidate = max(sell_candidates, key=lambda x: x['score'])
            action = 'SELL'
            candidates = sell_candidates
        else:
            # Default to best of either
            all_candidates = buy_candidates + sell_candidates
            if all_candidates:
                best_candidate = max(all_candidates, key=lambda x: x['score'])
                action = 'BUY' if best_candidate in buy_candidates else 'SELL'
                candidates = all_candidates
            else:
                # No clear optimal moment
                return self._create_default_optimal_moment(
                    action=preferred_action or 'HOLD',
                    current_price=current_price,
                    signals=signals,
                )

        if best_candidate is None:
            return self._create_default_optimal_moment(
                action=action,
                current_price=current_price,
                signals=signals,
            )

        # Calculate optimal date
        days_ahead = max(best_candidate.get('days_ahead', 0), 1)
        optimal_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

        # Expected price at optimal moment
        expected_return = best_candidate.get('expected_return', 0)
        if action == 'BUY':
            # Price to buy at (current) and expected sell price
            expected_price = current_price
            future_price = current_price * (1 + expected_return / 100)
            display_return = expected_return
        else:  # SELL
            # Price to sell at
            expected_price = current_price
            display_return = 0  # Already at peak

        # Determine confidence
        win_rate = best_candidate.get('win_rate', 50)
        score = best_candidate.get('score', 0)

        if win_rate >= 65 and score >= 3:
            confidence = 'HIGH'
        elif win_rate >= 55 and score >= 2:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'

        # Build reasoning
        reasoning = []

        if best_candidate['type'].startswith('seasonal'):
            month = best_candidate.get('month', 'N/A')
            reasoning.append(f"Historically strong month: {month}")
            reasoning.append(f"Average {month} return: {expected_return:.1f}% (win rate: {win_rate:.0f}%)")

        if best_candidate['type'].startswith('technical'):
            indicator = best_candidate.get('indicator', 'Technical signal')
            reasoning.append(f"{indicator} suggests {action.lower()} opportunity")

        if best_candidate['type'].startswith('pattern'):
            tf = best_candidate.get('timeframe', 'N/A')
            reasoning.append(f"Best historical timeframe: {tf}")
            reasoning.append(f"Win rate: {win_rate:.0f}%, avg return: {expected_return:.1f}%")

        if best_candidate['type'] in ['support_buy', 'resistance_sell']:
            level = best_candidate.get('level', 'Key level')
            reasoning.append(f"Price near {level.lower()}: ${current_price:.2f}")

        # Add volatility context
        volatility = signals['volatility']
        vol_level = volatility.get('volatility_20d', 25)
        if vol_level > 35:
            reasoning.append(f"High volatility ({vol_level:.1f}%) - use tight stops")

        # Risk metrics
        risk_metrics = signals['risk_metrics']
        max_dd = risk_metrics.get('max_drawdown', 0)

        # Calculate risk-reward ratio
        if action == 'BUY':
            potential_gain = abs(expected_return)
            potential_loss = abs(max_dd) * 0.3  # Assume 30% of max drawdown as risk
            risk_reward = potential_gain / max(potential_loss, 1)
        else:
            potential_gain = 5.0  # Assume average gain from avoiding loss
            potential_loss = abs(expected_return) if expected_return < 0 else 3.0
            risk_reward = potential_gain / max(potential_loss, 1)

        # Supporting signals
        supporting_signals = {
            'candidate_type': best_candidate['type'],
            'all_candidates_count': len(candidates),
            'score': score,
            'win_rate': win_rate,
            'trend_alignment': overall_bullish if action == 'BUY' else not overall_bullish,
            'volatility': vol_level,
            'max_drawdown': max_dd,
        }

        if best_candidate.get('month'):
            supporting_signals['target_month'] = best_candidate['month']
        if best_candidate.get('hold_days'):
            supporting_signals['optimal_hold_period'] = best_candidate['hold_days']

        return OptimalMoment(
            action=action,
            optimal_date=optimal_date,
            days_from_now=days_ahead,
            expected_price=expected_price,
            expected_return_pct=display_return,
            confidence=confidence,
            reasoning=reasoning[:5],  # Top 5 reasons
            supporting_signals=supporting_signals,
            risk_reward_ratio=risk_reward,
        )

    def _calculate_days_to_month(self, current_month: int, target_month: int) -> int:
        """Calculate days from now to the start of target month."""
        now = datetime.now()
        current_year = now.year

        # Determine target year — if target month is same as or before current, it's next year
        if target_month <= current_month:
            target_year = current_year + 1
        else:
            target_year = current_year

        target_date = datetime(target_year, target_month, 1)
        days_diff = (target_date - now).days

        return max(days_diff, 1)

    def _create_default_optimal_moment(
        self, action: str, current_price: float, signals: Dict[str, any]
    ) -> OptimalMoment:
        """Create a default optimal moment when no clear signal exists."""
        return OptimalMoment(
            action=action,
            optimal_date=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            days_from_now=1,
            expected_price=current_price,
            expected_return_pct=0.0,
            confidence='LOW',
            reasoning=['Insufficient signals for optimal timing', 'Consider waiting for clearer indicators'],
            supporting_signals={'reason': 'no_clear_signal'},
            risk_reward_ratio=1.0,
        )

    def _create_insufficient_data_strategy(
        self, ticker: str, data: pd.DataFrame
    ) -> StrategyRecommendation:
        """Create a default strategy when insufficient data is available."""
        current_price = float(data['Close'].iloc[-1]) if len(data) > 0 else 0.0

        return StrategyRecommendation(
            ticker=ticker,
            action='HOLD',
            timeframe='N/A',
            target_date=datetime.now().strftime('%Y-%m-%d'),
            confidence='LOW',
            rationale=[
                f'Insufficient data for analysis (need {self.min_data_points}+ points, have {len(data)})',
                'Recommend gathering more historical data before making investment decisions'
            ],
            entry_price=current_price,
            expected_return_pct=None,
            risk_level='UNKNOWN',
            key_metrics={},
            predictions={},
        )
