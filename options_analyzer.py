#!/usr/bin/env python3
"""
Options and Risk Analysis Module
Implements Black-Scholes model for options pricing and risk assessment.
Provides investment suggestions based on comprehensive analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')


class OptionsAnalyzer:
    def __init__(self):
        self.risk_free_rate = 0.05  # Default 5% risk-free rate (10-year Treasury)

    def black_scholes_call(self, S, K, T, r, sigma):
        """
        Calculate Black-Scholes call option price.

        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to expiration (in years)
            r (float): Risk-free rate
            sigma (float): Volatility (annualized)

        Returns:
            float: Call option price
        """
        if T <= 0:
            return max(S - K, 0)

        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return call_price

    def black_scholes_put(self, S, K, T, r, sigma):
        """
        Calculate Black-Scholes put option price.

        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to expiration (in years)
            r (float): Risk-free rate
            sigma (float): Volatility (annualized)

        Returns:
            float: Put option price
        """
        if T <= 0:
            return max(K - S, 0)

        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return put_price

    def calculate_greeks(self, S, K, T, r, sigma, option_type='call'):
        """
        Calculate option Greeks for risk assessment.

        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to expiration (in years)
            r (float): Risk-free rate
            sigma (float): Volatility (annualized)
            option_type (str): 'call' or 'put'

        Returns:
            dict: Greeks (delta, gamma, theta, vega, rho)
        """
        if T <= 0:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}

        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        # Common calculations
        pdf_d1 = norm.pdf(d1)
        cdf_d1 = norm.cdf(d1)
        cdf_d2 = norm.cdf(d2)

        if option_type.lower() == 'call':
            delta = cdf_d1
            rho = K * T * np.exp(-r * T) * cdf_d2
        else:  # put
            delta = cdf_d1 - 1
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)

        # Greeks that are the same for calls and puts
        gamma = pdf_d1 / (S * sigma * np.sqrt(T))
        theta = (-S * pdf_d1 * sigma / (2 * np.sqrt(T))
                - r * K * np.exp(-r * T) * (cdf_d2 if option_type.lower() == 'call' else norm.cdf(-d2)))
        vega = S * pdf_d1 * np.sqrt(T)

        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta / 365,  # Convert to daily theta
            'vega': vega / 100,    # Convert to 1% volatility change
            'rho': rho / 100       # Convert to 1% interest rate change
        }

    def calculate_implied_volatility(self, option_price, S, K, T, r, option_type='call',
                                   max_iterations=100, tolerance=1e-6):
        """
        Calculate implied volatility using Newton-Raphson method.

        Args:
            option_price (float): Market price of the option
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to expiration (in years)
            r (float): Risk-free rate
            option_type (str): 'call' or 'put'
            max_iterations (int): Maximum iterations for convergence
            tolerance (float): Convergence tolerance

        Returns:
            float: Implied volatility
        """
        if T <= 0:
            return 0

        # Initial guess
        sigma = 0.2

        for i in range(max_iterations):
            if option_type.lower() == 'call':
                price = self.black_scholes_call(S, K, T, r, sigma)
            else:
                price = self.black_scholes_put(S, K, T, r, sigma)

            # Vega for Newton-Raphson
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            vega = S * norm.pdf(d1) * np.sqrt(T)

            if abs(vega) < tolerance:
                break

            # Newton-Raphson update
            price_diff = price - option_price
            if abs(price_diff) < tolerance:
                break

            sigma = sigma - price_diff / vega

            # Ensure sigma stays positive
            sigma = max(sigma, 0.001)

        return sigma

    def analyze_stock_risk(self, stock_data, window=30):
        """
        Analyze stock risk metrics using Black-Scholes framework.

        Args:
            stock_data (pd.DataFrame): Stock price data
            window (int): Rolling window for calculations

        Returns:
            dict: Risk analysis results
        """
        # Calculate returns and volatility
        returns = stock_data['Close'].pct_change().dropna()

        # Rolling volatility (annualized)
        rolling_vol = returns.rolling(window=window).std() * np.sqrt(252)

        # Current metrics
        current_price = stock_data['Close'].iloc[-1]
        current_vol = rolling_vol.iloc[-1] if not pd.isna(rolling_vol.iloc[-1]) else returns.std() * np.sqrt(252)

        # Calculate at-the-money option prices for different expiration dates
        expiration_days = [30, 60, 90, 180, 365]
        risk_metrics = {}

        for days in expiration_days:
            T = days / 365

            # At-the-money call and put prices
            call_price = self.black_scholes_call(current_price, current_price, T, self.risk_free_rate, current_vol)
            put_price = self.black_scholes_put(current_price, current_price, T, self.risk_free_rate, current_vol)

            # Calculate Greeks
            call_greeks = self.calculate_greeks(current_price, current_price, T, self.risk_free_rate, current_vol, 'call')
            put_greeks = self.calculate_greeks(current_price, current_price, T, self.risk_free_rate, current_vol, 'put')

            risk_metrics[f'{days}d'] = {
                'call_price': call_price,
                'put_price': put_price,
                'call_greeks': call_greeks,
                'put_greeks': put_greeks,
                'straddle_price': call_price + put_price,  # Market expectation of movement
                'expected_move': (call_price + put_price) / current_price  # Expected percentage move
            }

        return {
            'current_price': current_price,
            'current_volatility': current_vol,
            'rolling_volatility': rolling_vol,
            'risk_metrics': risk_metrics,
            'volatility_percentile': self._calculate_vol_percentile(rolling_vol),
            'risk_assessment': self._assess_risk_level(current_vol, rolling_vol)
        }

    def _calculate_vol_percentile(self, rolling_vol, lookback_period=252):
        """Calculate where current volatility ranks historically."""
        if len(rolling_vol) < lookback_period:
            lookback_period = len(rolling_vol)

        recent_vol = rolling_vol.iloc[-lookback_period:]
        current_vol = rolling_vol.iloc[-1]

        if pd.isna(current_vol):
            return None

        percentile = (recent_vol < current_vol).sum() / len(recent_vol) * 100
        return percentile

    def _assess_risk_level(self, current_vol, rolling_vol):
        """Assess the current risk level based on volatility analysis."""
        if pd.isna(current_vol):
            return "Unable to assess"

        # Calculate historical volatility statistics
        vol_mean = rolling_vol.mean()
        vol_std = rolling_vol.std()

        if pd.isna(vol_mean) or pd.isna(vol_std):
            return "Insufficient data"

        # Z-score of current volatility
        vol_zscore = (current_vol - vol_mean) / vol_std

        if vol_zscore > 2:
            return "Very High Risk"
        elif vol_zscore > 1:
            return "High Risk"
        elif vol_zscore > -1:
            return "Moderate Risk"
        elif vol_zscore > -2:
            return "Low Risk"
        else:
            return "Very Low Risk"


class InvestmentAdvisor:
    def __init__(self):
        self.advice_history = []

    def generate_investment_suggestion(self, stock_data, pattern_analysis=None,
                                     risk_analysis=None, correlation_data=None):
        """
        Generate investment suggestions based on comprehensive analysis.

        Args:
            stock_data (pd.DataFrame): Stock price data
            pattern_analysis (dict): Results from pattern analysis
            risk_analysis (dict): Results from risk analysis
            correlation_data (dict): Correlation analysis results

        Returns:
            dict: Investment suggestion with reasoning
        """
        if len(stock_data) < 20:
            return {
                'suggestion': 'HOLD',
                'confidence': 'LOW',
                'reasoning': 'Insufficient data for analysis',
                'risk_level': 'UNKNOWN'
            }

        # Initialize scoring system
        buy_signals = 0
        sell_signals = 0
        risk_factors = []

        # Technical Analysis
        current_price = stock_data['Close'].iloc[-1]
        sma_20 = stock_data['Close'].rolling(20).mean().iloc[-1]
        sma_50 = stock_data['Close'].rolling(50).mean().iloc[-1] if len(stock_data) >= 50 else sma_20

        # Price momentum
        if current_price > sma_20:
            buy_signals += 1
        else:
            sell_signals += 1

        if current_price > sma_50:
            buy_signals += 1
        else:
            sell_signals += 1

        # Volatility analysis
        returns = stock_data['Close'].pct_change().dropna()
        recent_volatility = returns.tail(20).std() * np.sqrt(252)

        # Risk analysis integration
        if risk_analysis:
            risk_level = risk_analysis.get('risk_assessment', 'Moderate Risk')
            current_vol = risk_analysis.get('current_volatility', recent_volatility)
            vol_percentile = risk_analysis.get('volatility_percentile', 50)

            risk_factors.append(f"Risk Level: {risk_level}")

            # High volatility might indicate opportunity or danger
            if vol_percentile > 80:
                sell_signals += 1
                risk_factors.append("Very high volatility (top 20%)")
            elif vol_percentile < 20:
                buy_signals += 1
                risk_factors.append("Low volatility environment")

        # Pattern analysis integration
        if pattern_analysis:
            # Check for trend patterns
            if 'trend_strength' in pattern_analysis:
                trend_strength = pattern_analysis['trend_strength']
                if trend_strength > 0.6:
                    buy_signals += 2
                elif trend_strength < -0.6:
                    sell_signals += 2

        # Volume analysis
        if 'Volume' in stock_data.columns:
            avg_volume = stock_data['Volume'].tail(20).mean()
            recent_volume = stock_data['Volume'].tail(5).mean()

            if recent_volume > avg_volume * 1.5:
                # High volume could support the current trend
                if current_price > sma_20:
                    buy_signals += 1
                else:
                    sell_signals += 1

        # RSI-like momentum indicator
        price_changes = stock_data['Close'].diff().tail(14)
        gains = price_changes.where(price_changes > 0, 0).mean()
        losses = -price_changes.where(price_changes < 0, 0).mean()

        if losses != 0:
            rs = gains / losses
            rsi = 100 - (100 / (1 + rs))

            if rsi < 30:  # Oversold
                buy_signals += 1
                risk_factors.append("Potentially oversold (RSI < 30)")
            elif rsi > 70:  # Overbought
                sell_signals += 1
                risk_factors.append("Potentially overbought (RSI > 70)")

        # Final decision logic
        total_signals = buy_signals + sell_signals
        if total_signals == 0:
            suggestion = 'HOLD'
            confidence = 'LOW'
        else:
            buy_ratio = buy_signals / total_signals

            if buy_ratio >= 0.7:
                suggestion = 'BUY'
                confidence = 'HIGH' if buy_ratio >= 0.8 else 'MEDIUM'
            elif buy_ratio <= 0.3:
                suggestion = 'SELL'
                confidence = 'HIGH' if buy_ratio <= 0.2 else 'MEDIUM'
            else:
                suggestion = 'HOLD'
                confidence = 'MEDIUM'

        # Determine overall risk level
        if risk_analysis:
            overall_risk = risk_analysis.get('risk_assessment', 'MODERATE')
        else:
            if recent_volatility > 0.3:
                overall_risk = 'HIGH'
            elif recent_volatility < 0.15:
                overall_risk = 'LOW'
            else:
                overall_risk = 'MODERATE'

        # Build reasoning
        reasoning_parts = [
            f"Buy signals: {buy_signals}, Sell signals: {sell_signals}",
            f"Current price vs SMA20: {'Above' if current_price > sma_20 else 'Below'}",
            f"Recent volatility: {recent_volatility:.2%}"
        ]

        if risk_factors:
            reasoning_parts.extend(risk_factors)

        result = {
            'suggestion': suggestion,
            'confidence': confidence,
            'reasoning': '; '.join(reasoning_parts),
            'risk_level': overall_risk,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Store in history
        self.advice_history.append(result)

        return result

    def get_portfolio_suggestions(self, portfolio_data, correlation_analysis=None):
        """
        Generate portfolio-level investment suggestions.

        Args:
            portfolio_data (dict): Dictionary of ticker -> analysis results
            correlation_analysis (dict): Portfolio correlation analysis

        Returns:
            dict: Portfolio suggestions and risk assessment
        """
        suggestions = {}
        risk_summary = {}

        for ticker, data in portfolio_data.items():
            stock_data = data.get('stock_data')
            pattern_analysis = data.get('pattern_analysis')
            risk_analysis = data.get('risk_analysis')

            if stock_data is not None:
                suggestion = self.generate_investment_suggestion(
                    stock_data, pattern_analysis, risk_analysis
                )
                suggestions[ticker] = suggestion
                risk_summary[ticker] = suggestion['risk_level']

        # Portfolio-level insights
        buy_count = sum(1 for s in suggestions.values() if s['suggestion'] == 'BUY')
        sell_count = sum(1 for s in suggestions.values() if s['suggestion'] == 'SELL')
        hold_count = sum(1 for s in suggestions.values() if s['suggestion'] == 'HOLD')

        high_risk_count = sum(1 for r in risk_summary.values() if 'HIGH' in r.upper())

        portfolio_advice = {
            'individual_suggestions': suggestions,
            'portfolio_summary': {
                'buy_recommendations': buy_count,
                'sell_recommendations': sell_count,
                'hold_recommendations': hold_count,
                'high_risk_positions': high_risk_count,
                'total_positions': len(suggestions)
            },
            'portfolio_risk': 'HIGH' if high_risk_count > len(suggestions) * 0.5 else 'MODERATE',
            'diversification_note': self._assess_diversification(correlation_analysis)
        }

        return portfolio_advice

    def _assess_diversification(self, correlation_analysis):
        """Assess portfolio diversification based on correlation analysis."""
        if not correlation_analysis or 'correlation_stability' not in correlation_analysis:
            return "Unable to assess diversification - insufficient correlation data"

        correlations = correlation_analysis['correlation_stability']

        if not correlations:
            return "Single stock portfolio - no diversification"

        high_corr_pairs = sum(1 for pair_data in correlations.values()
                             if abs(pair_data.get('mean_correlation', 0)) > 0.7)

        total_pairs = len(correlations)

        if high_corr_pairs > total_pairs * 0.5:
            return "Low diversification - many highly correlated positions"
        elif high_corr_pairs > total_pairs * 0.3:
            return "Moderate diversification - some correlated positions"
        else:
            return "Good diversification - low correlation between positions"
