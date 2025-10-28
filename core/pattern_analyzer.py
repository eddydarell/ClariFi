#!/usr/bin/env python3
"""
Market Pattern Analyzer
Advanced analysis module for detecting patterns, correlations, and market behavior.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from scipy import stats
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')


class PatternAnalyzer:
    def __init__(self):
        self.patterns = {}
        self.correlations = {}

    def analyze_correlation_patterns(self, stock_data_dict, window=30):
        """
        Analyze correlation patterns between stocks over rolling windows.

        Args:
            stock_data_dict (dict): Dictionary of ticker -> DataFrame
            window (int): Rolling window size for correlation calculation

        Returns:
            dict: Analysis results
        """
        results = {
            'rolling_correlations': {},
            'correlation_stability': {},
            'leading_indicators': {},
            'pattern_summary': {}
        }

        if len(stock_data_dict) < 2:
            return results

        tickers = list(stock_data_dict.keys())

        # Calculate rolling correlations
        for i, ticker1 in enumerate(tickers):
            for ticker2 in tickers[i+1:]:
                data1 = stock_data_dict[ticker1]['Close'].pct_change()
                data2 = stock_data_dict[ticker2]['Close'].pct_change()

                # Align data on common dates
                common_dates = data1.index.intersection(data2.index)
                if len(common_dates) < window:
                    continue

                aligned_data1 = data1.loc[common_dates]
                aligned_data2 = data2.loc[common_dates]

                # Rolling correlation
                rolling_corr = aligned_data1.rolling(window=window).corr(aligned_data2)

                pair_key = f"{ticker1}-{ticker2}"
                results['rolling_correlations'][pair_key] = rolling_corr.dropna()

                # Correlation stability (standard deviation of rolling correlation)
                results['correlation_stability'][pair_key] = {
                    'mean_correlation': float(rolling_corr.mean()),
                    'std_correlation': float(rolling_corr.std()),
                    'stability_score': float(1 - rolling_corr.std())  # Higher = more stable
                }

        # Identify leading indicators
        results['leading_indicators'] = self._find_leading_indicators(stock_data_dict)

        # Pattern summary
        results['pattern_summary'] = self._summarize_patterns(results)

        return results

    def add_technical_indicators(self, data, validate=True):
        """
        Add advanced technical indicators to a DataFrame in-place:
        - RSI (14 & 30 period)
        - MACD with signal line and histogram
        - ADX (Average Directional Index)
        - ATR (Average True Range)
        - CCI (Commodity Channel Index)
        - Williams %R
        - OBV (On-Balance Volume)
        - Parabolic SAR
        - Bollinger Bands with width

        Args:
            data (pd.DataFrame): Stock data with OHLCV columns
            validate (bool): Add validation flags for indicator quality
        """
        # Ensure minimum data requirements
        if len(data) < 200:
            print(f"⚠️  Warning: Only {len(data)} rows available. Some indicators may be unreliable (recommended: 200+)")

        high = data['High']
        low = data['Low']
        close = data['Close']

        # RSI - Multiple timeframes
        def calculate_rsi(prices, period=14):
            """Calculate RSI with proper handling of edge cases"""
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / (loss + 1e-10)  # Avoid division by zero
            return 100 - (100 / (1 + rs))

        data['RSI_14'] = calculate_rsi(close, 14)
        data['RSI_30'] = calculate_rsi(close, 30)

        # MACD with signal line and histogram
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        data['MACD'] = exp1 - exp2
        data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
        data['MACD_Histogram'] = data['MACD'] - data['MACD_Signal']

        # Bollinger Bands with width
        data['BB_Middle'] = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
        data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)
        data['BB_Width'] = ((data['BB_Upper'] - data['BB_Lower']) / data['BB_Middle']) * 100

        # ADX (Average Directional Index)
        plus_dm = high.diff()
        minus_dm = low.diff().abs()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        data['ATR'] = atr
        plus_di = 100 * (plus_dm.rolling(14).sum() / (atr + 1e-10))
        minus_di = 100 * (minus_dm.rolling(14).sum() / (atr + 1e-10))
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)) * 100
        data['ADX'] = dx.rolling(14).mean()

        # CCI (Commodity Channel Index)
        tp = (high + low + close) / 3
        cci = (tp - tp.rolling(20).mean()) / (0.015 * tp.rolling(20).std() + 1e-10)
        data['CCI'] = cci

        # Williams %R
        highest_high = high.rolling(14).max()
        lowest_low = low.rolling(14).min()
        data['Williams_%R'] = -100 * (highest_high - close) / (highest_high - lowest_low + 1e-10)

        # OBV (On-Balance Volume)
        if 'Volume' in data.columns:
            obv = [0]
            for i in range(1, len(data)):
                if data['Close'].iloc[i] > data['Close'].iloc[i-1]:
                    obv.append(obv[-1] + data['Volume'].iloc[i])
                elif data['Close'].iloc[i] < data['Close'].iloc[i-1]:
                    obv.append(obv[-1] - data['Volume'].iloc[i])
                else:
                    obv.append(obv[-1])
            data['OBV'] = obv
        else:
            data['OBV'] = 0

        # Parabolic SAR
        sar = close.copy()
        af = 0.02
        max_af = 0.2
        trend = 1  # 1 for up, -1 for down
        ep = low.iloc[0]
        sar.iloc[0] = low.iloc[0]
        for i in range(1, len(data)):
            prev_sar = sar.iloc[i-1]
            if trend == 1:
                sar.iloc[i] = prev_sar + af * (ep - prev_sar)
                if low.iloc[i] < sar.iloc[i]:
                    trend = -1
                    sar.iloc[i] = ep
                    ep = high.iloc[i]
                    af = 0.02
                else:
                    if high.iloc[i] > ep:
                        ep = high.iloc[i]
                        af = min(af + 0.02, max_af)
            else:
                sar.iloc[i] = prev_sar + af * (ep - prev_sar)
                if high.iloc[i] > sar.iloc[i]:
                    trend = 1
                    sar.iloc[i] = ep
                    ep = low.iloc[i]
                    af = 0.02
                else:
                    if low.iloc[i] < ep:
                        ep = low.iloc[i]
                        af = min(af + 0.02, max_af)
        data['Parabolic_SAR'] = sar

        # Add validation flags if requested
        if validate:
            required_indicators = ['RSI_14', 'MACD', 'BB_Middle', 'ADX']
            data['Indicators_Valid'] = ~(
                data[required_indicators].isnull().any(axis=1)
            )

            # Mark first 50 rows as potentially unreliable due to warm-up period
            if len(data) > 50:
                data.loc[data.index[:50], 'Indicators_Valid'] = False

    def _find_leading_indicators(self, stock_data_dict, max_lag=5):
        """Find which stocks tend to lead others in price movements."""
        leading_indicators = {}
        tickers = list(stock_data_dict.keys())

        for i, leader in enumerate(tickers):
            for follower in tickers[i+1:]:
                leader_returns = stock_data_dict[leader]['Close'].pct_change()
                follower_returns = stock_data_dict[follower]['Close'].pct_change()

                # Align data
                common_dates = leader_returns.index.intersection(follower_returns.index)
                if len(common_dates) < 30:
                    continue

                leader_aligned = leader_returns.loc[common_dates]
                follower_aligned = follower_returns.loc[common_dates]

                best_correlation = 0
                best_lag = 0

                # Test different lags
                for lag in range(1, max_lag + 1):
                    if len(leader_aligned) > lag:
                        lagged_leader = leader_aligned.shift(lag)
                        correlation = float(lagged_leader.corr(follower_aligned))

                        if abs(correlation) > abs(best_correlation):
                            best_correlation = correlation
                            best_lag = lag

                if abs(best_correlation) > 0.3:  # Significant correlation threshold
                    pair_key = f"{leader}->{follower}"
                    leading_indicators[pair_key] = {
                        'correlation': float(best_correlation),
                        'lag_days': int(best_lag),
                        'strength': 'Strong' if abs(best_correlation) > 0.6 else 'Moderate'
                    }

        return leading_indicators

    def _summarize_patterns(self, analysis_results):
        """Create a summary of detected patterns."""
        summary = {
            'highly_correlated_pairs': [],
            'negatively_correlated_pairs': [],
            'stable_relationships': [],
            'volatile_relationships': [],
            'strong_leading_indicators': []
        }

        # Analyze correlation stability
        for pair, stats in analysis_results['correlation_stability'].items():
            mean_corr = stats['mean_correlation']
            stability = stats['stability_score']

            if mean_corr > 0.7:
                summary['highly_correlated_pairs'].append({
                    'pair': pair,
                    'correlation': mean_corr,
                    'stability': stability
                })
            elif mean_corr < -0.5:
                summary['negatively_correlated_pairs'].append({
                    'pair': pair,
                    'correlation': mean_corr,
                    'stability': stability
                })

            if stability > 0.8:
                summary['stable_relationships'].append({
                    'pair': pair,
                    'correlation': mean_corr,
                    'stability': stability
                })
            elif stability < 0.5:
                summary['volatile_relationships'].append({
                    'pair': pair,
                    'correlation': mean_corr,
                    'stability': stability
                })

        # Analyze leading indicators
        for pair, info in analysis_results['leading_indicators'].items():
            if info['strength'] == 'Strong':
                summary['strong_leading_indicators'].append({
                    'pair': pair,
                    'correlation': info['correlation'],
                    'lag_days': info['lag_days']
                })

        return summary

    def detect_volatility_patterns(self, stock_data_dict, window=20):
        """
        Detect volatility patterns and clustering.

        Args:
            stock_data_dict (dict): Dictionary of ticker -> DataFrame
            window (int): Window for volatility calculation

        Returns:
            dict: Volatility analysis results
        """
        volatility_analysis = {}

        for ticker, data in stock_data_dict.items():
            returns = data['Close'].pct_change()

            # Calculate rolling volatility
            rolling_vol = returns.rolling(window=window).std() * np.sqrt(252)  # Annualized

            # Detect volatility clusters
            high_vol_threshold = rolling_vol.quantile(0.8)
            low_vol_threshold = rolling_vol.quantile(0.2)

            high_vol_periods = rolling_vol[rolling_vol > high_vol_threshold]
            low_vol_periods = rolling_vol[rolling_vol < low_vol_threshold]

            volatility_analysis[ticker] = {
                'rolling_volatility': rolling_vol.dropna(),
                'high_volatility_periods': high_vol_periods.dropna(),
                'low_volatility_periods': low_vol_periods.dropna(),
                'avg_volatility': float(rolling_vol.mean()),
                'volatility_clustering_score': self._calculate_clustering_score(rolling_vol)
            }

        return volatility_analysis

    def _calculate_clustering_score(self, volatility_series):
        """Calculate a score indicating how clustered volatility periods are."""
        # Simple clustering score based on autocorrelation
        try:
            autocorr_1 = float(volatility_series.autocorr(lag=1))
            autocorr_5 = float(volatility_series.autocorr(lag=5))
            return float((autocorr_1 + autocorr_5) / 2)
        except:
            return 0.0

    def identify_support_resistance(self, stock_data, ticker, prominence=0.02):
        """
        Identify support and resistance levels using peak detection.

        Args:
            stock_data (DataFrame): Stock price data
            ticker (str): Stock ticker
            prominence (float): Minimum prominence for peak detection

        Returns:
            dict: Support and resistance levels
        """
        prices = stock_data['Close'].values

        # Find peaks (resistance) and troughs (support)
        resistance_indices, _ = find_peaks(prices, prominence=prominence * np.mean(prices))
        support_indices, _ = find_peaks(-prices, prominence=prominence * np.mean(prices))

        resistance_levels = prices[resistance_indices]
        support_levels = prices[support_indices]

        return {
            'ticker': ticker,
            'resistance_levels': {
                'prices': resistance_levels.tolist(),
                'dates': [date.isoformat() for date in stock_data.index[resistance_indices]],
                'current_distance': self._calculate_level_distances(float(prices[-1]), resistance_levels)
            },
            'support_levels': {
                'prices': support_levels.tolist(),
                'dates': [date.isoformat() for date in stock_data.index[support_indices]],
                'current_distance': self._calculate_level_distances(float(prices[-1]), support_levels)
            },
            'current_price': float(prices[-1])
        }

    def _calculate_level_distances(self, current_price, levels):
        """Calculate distances from current price to support/resistance levels."""
        distances = []
        for level in levels:
            level = float(level)  # Ensure it's a Python float
            pct_distance = ((level - current_price) / current_price) * 100
            distances.append({
                'price': level,
                'distance_pct': float(pct_distance)
            })
        return distances

    def calculate_risk_metrics(self, data):
        """
        Calculate comprehensive risk-adjusted performance metrics.

        Args:
            data (pd.DataFrame): Stock data with Close prices

        Returns:
            dict: Risk metrics including Sharpe, Sortino, Calmar, VaR, CVaR
        """
        if len(data) < 30:
            return {'error': 'Insufficient data for risk metrics (need 30+ days)'}

        returns = data['Close'].pct_change().dropna()

        if len(returns) == 0:
            return {'error': 'No valid returns calculated'}

        # Sharpe Ratio (assuming 4% annual risk-free rate)
        rf_rate = 0.04 / 252  # Daily risk-free rate
        excess_returns = returns - rf_rate
        sharpe = (excess_returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

        # Sortino Ratio (downside deviation only)
        downside_returns = returns[returns < 0]
        sortino = (excess_returns.mean() / downside_returns.std() * np.sqrt(252)) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0

        # Calmar Ratio (return / max drawdown)
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min()

        # Annualized return
        if len(returns) > 1:
            total_return = cumulative.iloc[-1] - 1
            years = len(returns) / 252
            annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        else:
            annual_return = 0

        calmar = annual_return / abs(max_dd) if max_dd != 0 else 0

        # Value at Risk (95% confidence)
        var_95 = returns.quantile(0.05)

        # Conditional VaR (average of worst 5%)
        cvar_95 = returns[returns <= var_95].mean() if (returns <= var_95).sum() > 0 else var_95

        # Win rate
        win_rate = (returns > 0).sum() / len(returns) * 100 if len(returns) > 0 else 0

        return {
            'sharpe_ratio': float(sharpe),
            'sortino_ratio': float(sortino),
            'calmar_ratio': float(calmar),
            'max_drawdown_pct': float(max_dd * 100),
            'var_95_daily_pct': float(var_95 * 100),
            'cvar_95_daily_pct': float(cvar_95 * 100),
            'annual_return_pct': float(annual_return * 100),
            'annual_volatility_pct': float(returns.std() * np.sqrt(252) * 100),
            'win_rate_pct': float(win_rate)
        }

    def detect_market_regime(self, data, spy_data=None):
        """
        Detect current market regime (trending/ranging/volatile).

        Args:
            data (pd.DataFrame): Stock data with OHLCV
            spy_data (pd.DataFrame, optional): SPY data for market correlation

        Returns:
            dict: Market regime information
        """
        if len(data) < 50:
            return {'error': 'Insufficient data for regime detection (need 50+ days)'}

        # Ensure ADX is calculated
        if 'ADX' not in data.columns:
            self.add_technical_indicators(data)

        # Get current ADX for trend strength
        current_adx = data['ADX'].iloc[-1] if not pd.isna(data['ADX'].iloc[-1]) else 20

        # Calculate volatility regime
        vol = data['Close'].pct_change().rolling(20).std() * np.sqrt(252) * 100
        current_vol = vol.iloc[-1]
        avg_vol = vol.mean()
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1

        # Detect regime based on ADX and volatility
        if current_adx > 25 and vol_ratio < 1.2:
            regime = 'TRENDING'
            confidence = 'HIGH'
            recommendation = 'Use trend-following strategies'
        elif current_adx < 20 and vol_ratio < 1.3:
            regime = 'RANGING'
            confidence = 'HIGH'
            recommendation = 'Use mean-reversion strategies'
        elif vol_ratio > 1.5:
            regime = 'VOLATILE'
            confidence = 'MEDIUM'
            recommendation = 'Reduce position sizes, use wider stops'
        else:
            regime = 'TRANSITIONAL'
            confidence = 'LOW'
            recommendation = 'Wait for clearer signals'

        result = {
            'regime': regime,
            'confidence': confidence,
            'adx': float(current_adx),
            'volatility_current': float(current_vol),
            'volatility_avg': float(avg_vol),
            'volatility_ratio': float(vol_ratio),
            'recommendation': recommendation
        }

        # Correlation with market (if SPY data provided)
        if spy_data is not None and len(spy_data) > 0:
            try:
                # Align dates
                common_dates = data.index.intersection(spy_data.index)
                if len(common_dates) > 20:
                    stock_returns = data.loc[common_dates, 'Close'].pct_change()
                    spy_returns = spy_data.loc[common_dates, 'Close'].pct_change()
                    correlation = stock_returns.corr(spy_returns)

                    if abs(correlation) > 0.7:
                        market_dependency = 'HIGH'
                    elif abs(correlation) > 0.4:
                        market_dependency = 'MEDIUM'
                    else:
                        market_dependency = 'LOW'

                    result['market_correlation'] = float(correlation)
                    result['market_dependency'] = market_dependency
            except Exception:
                pass

        return result

    def analyze_trend_strength(self, stock_data_dict):
        """
        Analyze trend strength using multiple indicators.

        Args:
            stock_data_dict (dict): Dictionary of ticker -> DataFrame

        Returns:
            dict: Trend analysis for each ticker
        """
        trend_analysis = {}

        for ticker, data in stock_data_dict.items():
            prices = data['Close']

            # Calculate various trend indicators
            sma_20 = prices.rolling(window=20).mean()
            sma_50 = prices.rolling(window=50).mean()

            # Trend direction
            current_trend = 'Bullish' if prices.iloc[-1] > sma_20.iloc[-1] > sma_50.iloc[-1] else \
                           'Bearish' if prices.iloc[-1] < sma_20.iloc[-1] < sma_50.iloc[-1] else 'Sideways'

            # Trend strength (R-squared of linear regression)
            x = np.arange(len(prices))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, prices)
            trend_strength = r_value ** 2

            # Recent momentum (20-day return)
            recent_momentum = (prices.iloc[-1] / prices.iloc[-20] - 1) * 100 if len(prices) >= 20 else 0

            trend_analysis[ticker] = {
                'current_trend': current_trend,
                'trend_strength': float(trend_strength),
                'slope': float(slope),
                'recent_momentum_pct': float(recent_momentum),
                'price_vs_sma20': float(((prices.iloc[-1] / sma_20.iloc[-1]) - 1) * 100),
                'price_vs_sma50': float(((prices.iloc[-1] / sma_50.iloc[-1]) - 1) * 100),
                'sma_crossover': 'Golden Cross' if sma_20.iloc[-1] > sma_50.iloc[-1] and sma_20.iloc[-2] <= sma_50.iloc[-2] else \
                                'Death Cross' if sma_20.iloc[-1] < sma_50.iloc[-1] and sma_20.iloc[-2] >= sma_50.iloc[-2] else 'None'
            }

        return trend_analysis
