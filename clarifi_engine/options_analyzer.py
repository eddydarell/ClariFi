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
            'delta': float(delta),
            'gamma': float(gamma),
            'theta': float(theta / 365),  # Convert to daily theta
            'vega': float(vega / 100),    # Convert to 1% volatility change
            'rho': float(rho / 100)       # Convert to 1% interest rate change
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
        # Handle MultiIndex columns - get the first ticker if present
        if hasattr(stock_data.columns, 'nlevels') and stock_data.columns.nlevels > 1:
            # MultiIndex columns - get the ticker from the first column
            ticker_name = stock_data.columns[0][1] if stock_data.columns[0][1] else list(stock_data.columns)[0][1]
            close_col = ('Close', ticker_name)
            print(f"DEBUG: analyze_stock_risk using MultiIndex columns - ticker: {ticker_name}")
        else:
            # Simple column names
            close_col = 'Close'
            print(f"DEBUG: analyze_stock_risk using simple column names")

        # Calculate returns and volatility
        returns = stock_data[close_col].pct_change().dropna()

        # Rolling volatility (annualized)
        rolling_vol = returns.rolling(window=window).std() * np.sqrt(252)

        # Current metrics
        current_price = float(stock_data[close_col].iloc[-1])

        # Ensure rolling_vol is properly calculated and current_vol is a scalar
        try:
            current_vol_value = rolling_vol.iloc[-1]
            if pd.isna(current_vol_value):
                current_vol = float(returns.std() * np.sqrt(252))
            else:
                current_vol = float(current_vol_value)
        except:
            current_vol = float(returns.std() * np.sqrt(252))
            current_vol = float(returns.std() * np.sqrt(252))

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
            'current_price': float(current_price),
            'current_volatility': float(current_vol),
            'rolling_volatility': rolling_vol.dropna().values.tolist() if hasattr(rolling_vol, 'values') else rolling_vol.dropna().tolist(),
            'risk_metrics': risk_metrics,
            'volatility_percentile': self._calculate_vol_percentile(rolling_vol),
            'risk_assessment': self._assess_risk_level(current_vol, rolling_vol)
        }

    def _calculate_vol_percentile(self, rolling_vol, lookback_period=252):
        """Calculate where current volatility ranks historically."""
        if len(rolling_vol) < lookback_period:
            lookback_period = len(rolling_vol)

        recent_vol = rolling_vol.iloc[-lookback_period:]
        current_vol_value = rolling_vol.iloc[-1]

        if pd.isna(current_vol_value):
            return None

        current_vol = float(current_vol_value)
        percentile = float((recent_vol < current_vol).sum() / len(recent_vol) * 100)
        return percentile

    def _assess_risk_level(self, current_vol, rolling_vol):
        """Assess the current risk level based on volatility analysis."""
        # Ensure current_vol is a scalar
        if isinstance(current_vol, pd.Series):
            current_vol = float(current_vol.iloc[0])
        elif pd.isna(current_vol):
            return "Unable to assess"

        # Calculate historical volatility statistics
        vol_mean = float(rolling_vol.mean())
        vol_std = float(rolling_vol.std())

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

    def analyze_options(self, ticker, stock_data=None):
        """
        Comprehensive options analysis for a given ticker.

        Args:
            ticker (str): Stock ticker symbol
            stock_data (pd.DataFrame, optional): Stock price data

        Returns:
            dict: Options analysis results
        """
        try:
            # If no stock data provided, use basic analysis
            if stock_data is None or len(stock_data) == 0:
                return {
                    'ticker': ticker,
                    'analysis_type': 'basic_options',
                    'message': 'Options analysis requires stock price data',
                    'recommendations': []
                }

            print(f"DEBUG: Options analysis for {ticker} - stock_data shape: {stock_data.shape}")

            # Calculate implied volatility from historical data
            returns = stock_data['Close'].pct_change().dropna()
            volatility = float(returns.std() * np.sqrt(252))  # Annualized volatility
            current_price = float(stock_data['Close'].iloc[-1])

            print(f"DEBUG: Calculated volatility: {volatility}, current_price: {current_price}")

            # Time to expiration options (30, 60, 90 days)
            expiration_days = [30, 60, 90]
            options_analysis = []

            for days in expiration_days:
                T = days / 365.0  # Convert to years

                # Strike prices around current price
                strikes = [
                    current_price * 0.95,  # 5% OTM put
                    current_price,         # ATM
                    current_price * 1.05   # 5% OTM call
                ]

                for strike in strikes:
                    # Calculate call and put prices
                    call_price = self.black_scholes_call(
                        current_price, strike, T, self.risk_free_rate, volatility
                    )
                    put_price = self.black_scholes_put(
                        current_price, strike, T, self.risk_free_rate, volatility
                    )

                    # Calculate Greeks
                    call_greeks = self.calculate_greeks(
                        current_price, strike, T, self.risk_free_rate, volatility, 'call'
                    )
                    put_greeks = self.calculate_greeks(
                        current_price, strike, T, self.risk_free_rate, volatility, 'put'
                    )

                    try:
                        # Helper to coerce scalar
                        def _scalar(x, lbl=""):
                            try:
                                if isinstance(x, (list, tuple)) and len(x) == 1:
                                    x = x[0]
                                if hasattr(x, 'item') and not isinstance(x, (bytes, str)):
                                    try:
                                        x = x.item()
                                    except Exception:
                                        pass
                                if isinstance(x, pd.Series):
                                    x = x.iloc[-1]
                                return float(x)
                            except Exception as err:
                                print(f"DEBUG: _scalar failed for {lbl}: {err}; defaulting to 0.0")
                                return 0.0

                        option_data = {
                            'expiration_days': int(days),
                            'strike': float(np.round(_scalar(strike, 'strike'), 2)),
                            'current_price': float(np.round(_scalar(current_price, 'current_price'), 2)),
                            'call_price': float(np.round(_scalar(call_price, 'call_price'), 2)),
                            'put_price': float(np.round(_scalar(put_price, 'put_price'), 2)),
                            'call_delta': float(np.round(_scalar(call_greeks['delta'], 'call_delta'), 4)),
                            'call_gamma': float(np.round(_scalar(call_greeks['gamma'], 'call_gamma'), 4)),
                            'call_theta': float(np.round(_scalar(call_greeks['theta'], 'call_theta'), 4)),
                            'put_delta': float(np.round(_scalar(put_greeks['delta'], 'put_delta'), 4)),
                            'put_gamma': float(np.round(_scalar(put_greeks['gamma'], 'put_gamma'), 4)),
                            'put_theta': float(np.round(_scalar(put_greeks['theta'], 'put_theta'), 4)),
                            'volatility': float(np.round(_scalar(volatility, 'volatility') * 100, 2))  # As percentage
                        }
                        options_analysis.append(option_data)
                    except Exception as opt_build_err:
                        print(f"DEBUG: Failed building option_data for strike {strike}: {opt_build_err}")
                        options_analysis.append({'expiration_days': int(days), 'strike': float(strike) if not isinstance(strike, (list, tuple, pd.Series)) else 0.0, 'error': f'build_failed: {opt_build_err}'})

            # Generate strategy recommendations
            print("DEBUG: About to call analyze_stock_risk")
            risk_analysis = self.analyze_stock_risk(stock_data)
            print(f"DEBUG: analyze_stock_risk completed, result keys: {list(risk_analysis.keys()) if isinstance(risk_analysis, dict) else type(risk_analysis)}")

            print("DEBUG: About to call _generate_options_strategies")
            strategies = self._generate_options_strategies(current_price, volatility, risk_analysis)
            print("DEBUG: _generate_options_strategies completed")

            return {
                'ticker': ticker,
                'current_price': float(np.round(float(current_price), 2)),
                'implied_volatility': float(np.round(float(volatility) * 100, 2)),
                'risk_assessment': risk_analysis.get('risk_level', 'Unknown'),
                'options_prices': options_analysis,
                'recommended_strategies': strategies,
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'ticker': ticker,
                'error': f"Options analysis failed: {str(e)}",
                'analysis_timestamp': datetime.now().isoformat()
            }

    def _generate_options_strategies(self, current_price, volatility, risk_analysis):
        """
        Generate recommended options strategies based on analysis.

        Args:
            current_price (float): Current stock price
            volatility (float): Implied volatility
            risk_analysis (dict): Risk analysis results

        Returns:
            list: List of recommended strategies
        """
        strategies = []
        risk_level = risk_analysis.get('risk_level', 'Unknown')

        # High volatility strategies
        if volatility > 0.3:  # 30% volatility
            strategies.append({
                'strategy': 'Short Straddle',
                'description': 'Sell both call and put at ATM to profit from volatility decline',
                'risk': 'High',
                'market_outlook': 'Neutral with volatility decrease'
            })

        # Low volatility strategies
        elif volatility < 0.15:  # 15% volatility
            strategies.append({
                'strategy': 'Long Straddle',
                'description': 'Buy both call and put at ATM to profit from volatility increase',
                'risk': 'Medium',
                'market_outlook': 'Neutral with volatility increase'
            })

        # Medium volatility strategies
        else:
            strategies.append({
                'strategy': 'Iron Condor',
                'description': 'Sell call spread and put spread to profit from range-bound movement',
                'risk': 'Medium',
                'market_outlook': 'Neutral within range'
            })

        # Risk-based strategies
        if risk_level in ['High Risk', 'Very High Risk']:
            strategies.append({
                'strategy': 'Protective Put',
                'description': 'Buy put options to hedge against downside risk',
                'risk': 'Low',
                'market_outlook': 'Insurance against decline'
            })
        elif risk_level in ['Low Risk', 'Very Low Risk']:
            strategies.append({
                'strategy': 'Covered Call',
                'description': 'Sell call options against stock holdings for income',
                'risk': 'Low',
                'market_outlook': 'Neutral to slightly bullish'
            })

        return strategies


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
        print(f"DEBUG: Investment advice method called with stock_data type: {type(stock_data)}")
        print(f"DEBUG: stock_data shape: {stock_data.shape if hasattr(stock_data, 'shape') else 'No shape'}")
        print(f"DEBUG: stock_data columns: {list(stock_data.columns)}")

        # Handle MultiIndex columns - get the first ticker if present
        if hasattr(stock_data.columns, 'nlevels') and stock_data.columns.nlevels > 1:
            # MultiIndex columns - get the ticker from the first column
            ticker_name = stock_data.columns[0][1] if stock_data.columns[0][1] else list(stock_data.columns)[0][1]
            close_col = ('Close', ticker_name)
            volume_col = ('Volume', ticker_name)
            print(f"DEBUG: Using MultiIndex columns - ticker: {ticker_name}")
        else:
            # Simple column names
            close_col = 'Close'
            volume_col = 'Volume'
            print(f"DEBUG: Using simple column names")

        if stock_data is None:
            print("DEBUG: stock_data is None")
            return {
                'suggestion': 'HOLD',
                'confidence': 'LOW',
                'reasoning': 'No stock data provided',
                'risk_level': 'UNKNOWN'
            }

        print(f"DEBUG: About to check len(stock_data) - type: {type(stock_data)}")

        # Check data length carefully to avoid Series boolean issues
        try:
            data_length = len(stock_data)
            print(f"DEBUG: data_length = {data_length}")
        except Exception as e:
            print(f"DEBUG: Error getting length: {e}")
            return {
                'suggestion': 'HOLD',
                'confidence': 'LOW',
                'reasoning': f'Data length check failed: {str(e)}',
                'risk_level': 'UNKNOWN'
            }

        if data_length == 0 or data_length < 20:
            return {
                'suggestion': 'HOLD',
                'confidence': 'LOW',
                'reasoning': 'Insufficient data for analysis',
                'risk_level': 'UNKNOWN'
            }

        try:
            print("DEBUG: Starting investment suggestion analysis")

            # Helper to coerce any pandas/NumPy object to a float safely
            def _to_float(value, default=0.0, label=""):
                try:
                    if isinstance(value, (list, tuple)) and len(value) == 1:
                        value = value[0]
                    if hasattr(value, 'item') and not isinstance(value, (bytes, str)):
                        # numpy scalar or 0-d array
                        try:
                            value = value.item()
                        except Exception:
                            pass
                    if isinstance(value, (pd.Series, pd.DataFrame)):
                        # Take last value if Series, else default
                        if isinstance(value, pd.Series) and len(value) > 0:
                            value = value.iloc[-1]
                        else:
                            return float(default)
                    return float(value)
                except Exception as conv_err:
                    print(f"DEBUG: _to_float conversion failed for {label}: {conv_err}; using default {default}")
                    return float(default)

            # Early sanity checks to catch ambiguous Series boolean usage
            ambiguous_candidates = {
                'pattern_analysis': pattern_analysis if isinstance(pattern_analysis, pd.Series) else None,
                'risk_analysis': risk_analysis if isinstance(risk_analysis, pd.Series) else None,
            }
            for name, candidate in ambiguous_candidates.items():
                if candidate is not None:
                    print(f"DEBUG: WARNING - {name} is a pandas Series; converting to dict")
                    try:
                        if isinstance(candidate, pd.Series):
                            if candidate.index.is_unique:
                                converted = candidate.to_dict()
                            else:
                                converted = candidate.reset_index().to_dict(orient='list')
                            if name == 'pattern_analysis':
                                pattern_analysis = converted
                            else:
                                risk_analysis = converted
                    except Exception as conv_ser_err:
                        print(f"DEBUG: Failed to convert {name} Series to dict: {conv_ser_err}")

            # Initialize scoring system
            buy_signals = 0
            sell_signals = 0
            risk_factors = []

            print("DEBUG: Calculating technical indicators")
            # Technical Analysis
            current_price = float(stock_data[close_col].iloc[-1])
            sma_20 = float(stock_data[close_col].rolling(20).mean().iloc[-1])
            sma_50 = float(stock_data[close_col].rolling(50).mean().iloc[-1]) if len(stock_data) >= 50 else sma_20
            print(f"DEBUG: current_price={current_price}, sma_20={sma_20}, sma_50={sma_50}")

            # Price momentum
            try:
                print("DEBUG: Evaluating price momentum vs SMA20")
                cond1 = float(current_price) > float(sma_20)
                print(f"DEBUG: cond1 (current > sma20) = {cond1}")
                if cond1:
                    buy_signals += 1
                else:
                    sell_signals += 1
            except Exception as pm_err1:
                print(f"DEBUG: Price momentum SMA20 error: {pm_err1}")

            try:
                print("DEBUG: Evaluating price momentum vs SMA50")
                cond2 = float(current_price) > float(sma_50)
                print(f"DEBUG: cond2 (current > sma50) = {cond2}")
                if cond2:
                    buy_signals += 1
                else:
                    sell_signals += 1
            except Exception as pm_err2:
                print(f"DEBUG: Price momentum SMA50 error: {pm_err2}")

            print(f"DEBUG: After price momentum - buy_signals={buy_signals}, sell_signals={sell_signals}")

            # Volatility analysis
            returns = stock_data[close_col].pct_change().dropna()
            try:
                recent_volatility = _to_float(returns.tail(20).std() * np.sqrt(252), default=0.0, label="recent_volatility")
            except Exception as rv_err:
                print(f"DEBUG: recent_volatility computation failed: {rv_err}")
                recent_volatility = 0.0

            # Risk analysis integration
            print(f"DEBUG: risk_analysis type: {type(risk_analysis)} value preview: {str(risk_analysis)[:120] if risk_analysis is not None else 'None'}")
            try:
                print("DEBUG: Checking risk_analysis truthiness")
                risk_dict_cond = isinstance(risk_analysis, dict) and len(risk_analysis) > 0
                if not risk_dict_cond:
                    risk_dict_cond = isinstance(risk_analysis, pd.Series) and len(risk_analysis) > 0
                print(f"DEBUG: risk_dict_cond = {risk_dict_cond}")
            except Exception as ra_eval_err:
                print(f"DEBUG: risk_analysis evaluation error: {ra_eval_err}")
                risk_dict_cond = False

            if risk_dict_cond:
                risk_level = risk_analysis.get('risk_assessment', 'Moderate Risk')
                current_vol = risk_analysis.get('current_volatility', recent_volatility)
                vol_percentile = risk_analysis.get('volatility_percentile', 50)

                # Ensure values are scalars, not Series
                if isinstance(current_vol, pd.Series):
                    current_vol = float(current_vol.iloc[0]) if len(current_vol) > 0 else recent_volatility

                if isinstance(vol_percentile, pd.Series):
                    vol_percentile = float(vol_percentile.iloc[0]) if len(vol_percentile) > 0 else 50

                risk_factors.append(f"Risk Level: {risk_level}")

                # High volatility might indicate opportunity or danger
                if vol_percentile > 80:
                    sell_signals += 1
                    risk_factors.append("Very high volatility (top 20%)")
                elif vol_percentile < 20:
                    buy_signals += 1
                    risk_factors.append("Low volatility environment")

            # Pattern analysis integration
            print(f"DEBUG: pattern_analysis type: {type(pattern_analysis)} value preview: {str(pattern_analysis)[:120] if pattern_analysis is not None else 'None'}")
            try:
                print("DEBUG: Checking pattern_analysis truthiness")
                pattern_dict_cond = isinstance(pattern_analysis, dict) and len(pattern_analysis) > 0
                print(f"DEBUG: pattern_dict_cond = {pattern_dict_cond}")
            except Exception as pa_eval_err:
                print(f"DEBUG: pattern_analysis evaluation error: {pa_eval_err}")
                pattern_dict_cond = False

            if pattern_dict_cond:
                # Check for trend patterns
                if 'trend_strength' in pattern_analysis:
                    trend_strength = pattern_analysis['trend_strength']

                    # Ensure trend_strength is a scalar, not a Series - fix Series boolean ambiguity
                    if isinstance(trend_strength, pd.Series):
                        trend_strength = float(trend_strength.iloc[0]) if len(trend_strength) > 0 and not trend_strength.iloc[0] != trend_strength.iloc[0] else 0.0  # NaN check without pd.notna
                    elif trend_strength is None or (hasattr(trend_strength, '__iter__') and not isinstance(trend_strength, str)):
                        trend_strength = 0.0
                    elif trend_strength != trend_strength:  # NaN check without pd.isna
                        trend_strength = 0.0
                    else:
                        trend_strength = float(trend_strength)

                    if trend_strength > 0.6:
                        buy_signals += 2
                    elif trend_strength < -0.6:
                        sell_signals += 2

            # Volume analysis - use safe column checking for MultiIndex
            try:
                has_volume_col = any(volume_col == col for col in stock_data.columns)
                print(f"DEBUG: Volume column check - has_volume_col: {has_volume_col}")

                if has_volume_col:
                    avg_volume = float(stock_data[volume_col].tail(20).mean())
                    recent_volume = float(stock_data[volume_col].tail(5).mean())
                    print(f"DEBUG: Volume analysis - avg_volume: {avg_volume}, recent_volume: {recent_volume}")

                    if recent_volume > avg_volume * 1.5:
                        # High volume could support the current trend
                        if current_price > sma_20:
                            buy_signals += 1
                        else:
                            sell_signals += 1
                        print(f"DEBUG: High volume detected, signals updated")
                else:
                    print(f"DEBUG: Volume column not found in: {list(stock_data.columns)}")
            except Exception as vol_error:
                print(f"DEBUG: Volume analysis error: {vol_error}")
                # Continue without volume analysis

            # RSI-like momentum indicator
            price_changes = stock_data[close_col].diff().tail(14)
            gains_series = price_changes.where(price_changes > 0, 0)
            losses_series = -price_changes.where(price_changes < 0, 0)

            # Convert to float and handle NaN values - ensure scalar values
            try:
                gains_mean = gains_series.mean()
                # Fix Series boolean ambiguity: check type first, then use != for NaN check
                if isinstance(gains_mean, pd.Series):
                    gains = float(gains_mean.iloc[0]) if len(gains_mean) > 0 and gains_mean.iloc[0] == gains_mean.iloc[0] else 0.0  # NaN check
                elif gains_mean == gains_mean:  # Not NaN
                    gains = float(gains_mean)
                else:
                    gains = 0.0
            except:
                gains = 0.0

            try:
                losses_mean = losses_series.mean()
                # Fix Series boolean ambiguity: check type first, then use != for NaN check
                if isinstance(losses_mean, pd.Series):
                    losses = float(losses_mean.iloc[0]) if len(losses_mean) > 0 and losses_mean.iloc[0] == losses_mean.iloc[0] else 0.0  # NaN check
                elif losses_mean == losses_mean:  # Not NaN
                    losses = float(losses_mean)
                else:
                    losses = 0.0
            except:
                losses = 0.0

            if losses != 0:
                rs = gains / losses
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 50  # Neutral if no data

            if float(rsi) < 30:  # Oversold
                buy_signals += 1
                risk_factors.append("Potentially oversold (RSI < 30)")
            elif float(rsi) > 70:  # Overbought
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
            if isinstance(risk_analysis, dict) and len(risk_analysis) > 0:
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
                f"Current price vs SMA20: {'Above' if float(current_price) > float(sma_20) else 'Below'}",
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

        except Exception as e:
            print(f"Error in investment advice generation: {e}")
            import traceback
            traceback.print_exc()
            return {
                'suggestion': 'HOLD',
                'confidence': 'LOW',
                'reasoning': f'Analysis error: {str(e)}',
                'risk_level': 'UNKNOWN'
            }

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
