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
            distance_pct = ((level - current_price) / current_price) * 100
            distances.append({
                'level': level,
                'distance_pct': float(distance_pct),
                'direction': 'above' if distance_pct > 0 else 'below'
            })
        return sorted(distances, key=lambda x: abs(x['distance_pct']))

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
