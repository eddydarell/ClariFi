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
from scipy.stats import norm, poisson, t
from scipy.optimize import minimize
import math
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

    def merton_jump_diffusion_price(self, S, K, T, r, sigma, lambda_jump, mu_jump, sigma_jump, option_type='call'):
        """
        Calculate option price using Merton Jump-Diffusion model.
        Accounts for sudden jumps in stock prices (e.g., earnings surprises, crashes).

        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to expiration (in years)
            r (float): Risk-free rate
            sigma (float): Volatility of the diffusion component
            lambda_jump (float): Jump intensity (jumps per year)
            mu_jump (float): Expected jump size (mean of log-jump)
            sigma_jump (float): Jump volatility (std of log-jump)
            option_type (str): 'call' or 'put'

        Returns:
            float: Option price under jump-diffusion model
        """
        if T <= 0:
            return max(S - K, 0) if option_type == 'call' else max(K - S, 0)

        # Maximum number of jumps to consider
        max_jumps = int(lambda_jump * T * 3) + 10  # 3 standard deviations + buffer

        option_price = 0.0

        for n in range(max_jumps):
            # Probability of exactly n jumps
            jump_prob = (np.exp(-lambda_jump * T) * (lambda_jump * T)**n) / math.factorial(n)

            # Adjusted parameters for n jumps
            r_adj = r - lambda_jump * (np.exp(mu_jump + 0.5 * sigma_jump**2) - 1)
            sigma_adj = np.sqrt(sigma**2 + n * sigma_jump**2 / T)
            S_adj = S * np.exp(n * (mu_jump + 0.5 * sigma_jump**2))

            # Black-Scholes price with adjusted parameters
            if option_type == 'call':
                bs_price = self.black_scholes_call(S_adj, K, T, r_adj, sigma_adj)
            else:
                bs_price = self.black_scholes_put(S_adj, K, T, r_adj, sigma_adj)

            option_price += jump_prob * bs_price

            # Early termination if probability becomes negligible
            if jump_prob < 1e-8:
                break

        return option_price

    def heston_model_price(self, S, K, T, r, v0, kappa, theta, sigma_v, rho, option_type='call'):
        """
        Calculate option price using Heston stochastic volatility model.
        Allows volatility to be random, capturing volatility clustering.

        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to expiration (in years)
            r (float): Risk-free rate
            v0 (float): Initial volatility
            kappa (float): Mean reversion speed
            theta (float): Long-term volatility mean
            sigma_v (float): Volatility of volatility
            rho (float): Correlation between stock and volatility
            option_type (str): 'call' or 'put'

        Returns:
            float: Option price under Heston model
        """
        if T <= 0:
            return max(S - K, 0) if option_type == 'call' else max(K - S, 0)

        # Use characteristic function approach (simplified implementation)
        # For production use, would implement full Fourier transform method

        # Approximate using time-averaged volatility approach
        # This is a simplified version - full Heston requires complex numerical methods
        avg_vol = np.sqrt(theta + (v0 - theta) * (1 - np.exp(-kappa * T)) / (kappa * T))

        # Adjust for volatility risk premium
        vol_adjustment = 1 + 0.1 * sigma_v * np.sqrt(T)  # Simplified adjustment
        effective_vol = avg_vol * vol_adjustment

        # Use Black-Scholes with effective volatility
        if option_type == 'call':
            return self.black_scholes_call(S, K, T, r, effective_vol)
        else:
            return self.black_scholes_put(S, K, T, r, effective_vol)

    def calculate_var(self, returns, confidence_level=0.05, method='historical'):
        """
        Calculate Value-at-Risk (VaR) - maximum potential loss over time horizon.

        Args:
            returns (pd.Series): Return series
            confidence_level (float): Confidence level (0.05 = 95% VaR)
            method (str): 'historical', 'parametric', or 'monte_carlo'

        Returns:
            float: VaR estimate (positive value representing loss)
        """
        if len(returns) == 0:
            return 0.0

        if method == 'historical':
            # Historical simulation VaR
            return -np.percentile(returns, confidence_level * 100)

        elif method == 'parametric':
            # Assume normal distribution
            mean = returns.mean()
            std = returns.std()
            var_cutoff = norm.ppf(confidence_level, mean, std)
            return -var_cutoff

        elif method == 'monte_carlo':
            # Monte Carlo simulation (simplified)
            mean = returns.mean()
            std = returns.std()
            n_simulations = 10000

            # Generate random returns
            simulated_returns = np.random.normal(mean, std, n_simulations)
            return -np.percentile(simulated_returns, confidence_level * 100)

        else:
            raise ValueError("Method must be 'historical', 'parametric', or 'monte_carlo'")

    def calculate_cvar(self, returns, confidence_level=0.05):
        """
        Calculate Conditional Value-at-Risk (CVaR) - expected loss beyond VaR.
        More robust for tail risks than VaR.

        Args:
            returns (pd.Series): Return series
            confidence_level (float): Confidence level (0.05 = 95% CVaR)

        Returns:
            float: CVaR estimate (positive value representing expected loss)
        """
        if len(returns) == 0:
            return 0.0

        var_threshold = -self.calculate_var(returns, confidence_level, 'historical')

        # Calculate expected loss beyond VaR threshold
        tail_losses = returns[returns <= var_threshold]

        if len(tail_losses) == 0:
            return -var_threshold  # Return VaR if no tail losses

        return -tail_losses.mean()

    def calculate_risk_ratios(self, returns, risk_free_rate=None):
        """
        Calculate Sharpe and Sortino ratios for risk-adjusted performance.

        Args:
            returns (pd.Series): Return series
            risk_free_rate (float): Risk-free rate (annualized)

        Returns:
            dict: Risk ratios and metrics
        """
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate

        if len(returns) == 0:
            return {'sharpe_ratio': 0, 'sortino_ratio': 0, 'calmar_ratio': 0}

        # Annualize returns
        annual_return = returns.mean() * 252
        annual_vol = returns.std() * np.sqrt(252)

        # Downside deviation (for Sortino ratio)
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0

        # Maximum drawdown
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()

        # Calculate ratios
        excess_return = annual_return - risk_free_rate

        sharpe_ratio = excess_return / annual_vol if annual_vol > 0 else 0
        sortino_ratio = excess_return / downside_vol if downside_vol > 0 else 0
        calmar_ratio = excess_return / abs(max_drawdown) if max_drawdown < 0 else 0

        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'annual_return': annual_return,
            'annual_volatility': annual_vol,
            'max_drawdown': max_drawdown,
            'downside_volatility': downside_vol
        }

    def comprehensive_risk_analysis(self, stock_data, window=30):
        """
        Perform comprehensive risk analysis using multiple models and measures.

        Args:
            stock_data (pd.DataFrame): Stock price data
            window (int): Rolling window for calculations

        Returns:
            dict: Comprehensive risk analysis results
        """
        try:
            returns = stock_data['Close'].pct_change().dropna()
            current_price = stock_data['Close'].iloc[-1]

            # Basic risk metrics
            basic_risk = self.analyze_stock_risk(stock_data, window)

            # Advanced VaR measures
            var_95 = self.calculate_var(returns, 0.05, 'historical')
            var_99 = self.calculate_var(returns, 0.01, 'historical')
            cvar_95 = self.calculate_cvar(returns, 0.05)
            cvar_99 = self.calculate_cvar(returns, 0.01)

            # Risk ratios
            risk_ratios = self.calculate_risk_ratios(returns)

            # Jump-diffusion parameters estimation (simplified)
            # In practice, these would be calibrated to market data
            lambda_jump = 2.0  # 2 jumps per year on average
            mu_jump = -0.1     # Average jump is -10%
            sigma_jump = 0.2   # Jump volatility 20%

            # Heston model parameters (simplified calibration)
            vol = basic_risk['current_volatility']
            v0 = vol**2
            kappa = 2.0        # Mean reversion speed
            theta = 0.04       # Long-term variance (20% vol)
            sigma_v = 0.3      # Volatility of volatility
            rho = -0.7         # Correlation (typically negative)

            # Calculate option prices using different models for comparison
            T = 30/365  # 30-day options
            K = current_price  # At-the-money

            bs_call = self.black_scholes_call(current_price, K, T, self.risk_free_rate, vol)
            merton_call = self.merton_jump_diffusion_price(
                current_price, K, T, self.risk_free_rate, vol,
                lambda_jump, mu_jump, sigma_jump, 'call'
            )
            heston_call = self.heston_model_price(
                current_price, K, T, self.risk_free_rate,
                v0, kappa, theta, sigma_v, rho, 'call'
            )

            # Model comparison
            merton_premium = (merton_call - bs_call) / bs_call * 100 if bs_call > 0 else 0
            heston_premium = (heston_call - bs_call) / bs_call * 100 if bs_call > 0 else 0

            return {
                **basic_risk,  # Include all basic risk metrics
                'advanced_var_measures': {
                    'var_95_1day': var_95,
                    'var_99_1day': var_99,
                    'cvar_95_1day': cvar_95,
                    'cvar_99_1day': cvar_99,
                    'var_95_pct': var_95 * 100,  # As percentage
                    'cvar_95_pct': cvar_95 * 100
                },
                'risk_ratios': risk_ratios,
                'model_comparison': {
                    'black_scholes_call': bs_call,
                    'merton_jump_call': merton_call,
                    'heston_call': heston_call,
                    'merton_premium_pct': merton_premium,
                    'heston_premium_pct': heston_premium
                },
                'model_parameters': {
                    'jump_intensity': lambda_jump,
                    'expected_jump_size': mu_jump,
                    'jump_volatility': sigma_jump,
                    'vol_mean_reversion': kappa,
                    'long_term_vol': np.sqrt(theta),
                    'vol_of_vol': sigma_v,
                    'stock_vol_correlation': rho
                },
                'risk_interpretation': self._interpret_comprehensive_risk(
                    var_95, cvar_95, risk_ratios, merton_premium, heston_premium
                )
            }

        except Exception as e:
            return {
                'error': f"Comprehensive risk analysis failed: {str(e)}",
                'fallback_analysis': self.analyze_stock_risk(stock_data, window)
            }

    def _interpret_comprehensive_risk(self, var_95, cvar_95, risk_ratios, merton_premium, heston_premium):
        """Interpret comprehensive risk analysis results."""
        interpretation = []

        # VaR interpretation
        if var_95 > 0.05:  # More than 5% daily VaR
            interpretation.append("🚨 HIGH DAILY RISK: Expected 1-day loss >5% with 5% probability")
        elif var_95 > 0.03:
            interpretation.append("⚠️ MODERATE DAILY RISK: Expected 1-day loss 3-5% with 5% probability")
        else:
            interpretation.append("✅ LOW DAILY RISK: Expected 1-day loss <3% with 5% probability")

        # CVaR interpretation
        if cvar_95 > var_95 * 1.5:
            interpretation.append("⚠️ SIGNIFICANT TAIL RISK: Losses beyond VaR are much larger")
        else:
            interpretation.append("✅ MODERATE TAIL RISK: Losses beyond VaR are manageable")

        # Sharpe ratio interpretation
        sharpe = risk_ratios['sharpe_ratio']
        if sharpe > 1.5:
            interpretation.append("🌟 EXCELLENT RISK-ADJUSTED RETURNS")
        elif sharpe > 1.0:
            interpretation.append("✅ GOOD RISK-ADJUSTED RETURNS")
        elif sharpe > 0.5:
            interpretation.append("📊 MODERATE RISK-ADJUSTED RETURNS")
        else:
            interpretation.append("❌ POOR RISK-ADJUSTED RETURNS")

        # Jump risk interpretation
        if abs(merton_premium) > 5:
            interpretation.append("⚡ SIGNIFICANT JUMP RISK: Options price notably higher due to crash risk")
        elif abs(merton_premium) > 2:
            interpretation.append("⚡ MODERATE JUMP RISK: Some premium for sudden price movements")
        else:
            interpretation.append("✅ LOW JUMP RISK: Minimal crash/spike risk premium")

        # Volatility clustering interpretation
        if abs(heston_premium) > 3:
            interpretation.append("📊 STRONG VOLATILITY CLUSTERING: Vol tends to persist at levels")
        elif abs(heston_premium) > 1:
            interpretation.append("📊 MODERATE VOLATILITY CLUSTERING")
        else:
            interpretation.append("📊 LOW VOLATILITY CLUSTERING: More stable volatility")

        return interpretation

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
        else:
            # Simple column names
            close_col = 'Close'

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


            # Calculate implied volatility from historical data
            returns = stock_data['Close'].pct_change().dropna()
            volatility = float(returns.std() * np.sqrt(252))  # Annualized volatility
            current_price = float(stock_data['Close'].iloc[-1])


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
                                    except Exception as e:
                                        warnings.warn(f"Warning: Unable to convert numpy/pandas item to scalar - {str(e)}")
                                if isinstance(x, pd.Series):
                                    x = x.iloc[-1]
                                return float(x)
                            except Exception as err:
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
                        options_analysis.append({'expiration_days': int(days), 'strike': float(strike) if not isinstance(strike, (list, tuple, pd.Series)) else 0.0, 'error': f'build_failed: {opt_build_err}'})

            # Generate strategy recommendations using comprehensive risk analysis
            risk_analysis = self.comprehensive_risk_analysis(stock_data)

            strategies = self._generate_options_strategies(current_price, volatility, risk_analysis)

            return {
                'ticker': ticker,
                'current_price': float(np.round(float(current_price), 2)),
                'implied_volatility': float(np.round(float(volatility) * 100, 2)),
                'risk_assessment': risk_analysis.get('risk_assessment', 'Unknown'),
                'comprehensive_risk': {
                    'var_95_daily': f"{risk_analysis.get('advanced_var_measures', {}).get('var_95_pct', 0):.2f}%",
                    'cvar_95_daily': f"{risk_analysis.get('advanced_var_measures', {}).get('cvar_95_pct', 0):.2f}%",
                    'sharpe_ratio': round(risk_analysis.get('risk_ratios', {}).get('sharpe_ratio', 0), 3),
                    'sortino_ratio': round(risk_analysis.get('risk_ratios', {}).get('sortino_ratio', 0), 3),
                    'model_comparison': risk_analysis.get('model_comparison', {}),
                    'risk_interpretation': risk_analysis.get('risk_interpretation', [])
                },
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

        # Handle MultiIndex columns - get the first ticker if present
        if hasattr(stock_data.columns, 'nlevels') and stock_data.columns.nlevels > 1:
            # MultiIndex columns - get the ticker from the first column
            ticker_name = stock_data.columns[0][1] if stock_data.columns[0][1] else list(stock_data.columns)[0][1]
            close_col = ('Close', ticker_name)
            volume_col = ('Volume', ticker_name)
        else:
            # Simple column names
            close_col = 'Close'
            volume_col = 'Volume'

        if stock_data is None:
            return {
                'suggestion': 'HOLD',
                'confidence': 'LOW',
                'reasoning': 'No stock data provided',
                'risk_level': 'UNKNOWN'
            }


        # Check data length carefully to avoid Series boolean issues
        try:
            data_length = len(stock_data)
        except Exception as e:
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

            # Helper to coerce any pandas/NumPy object to a float safely
            def _to_float(value, default=0.0, label=""):
                try:
                    if isinstance(value, (list, tuple)) and len(value) == 1:
                        value = value[0]
                    if hasattr(value, 'item') and not isinstance(value, (bytes, str)):
                        # numpy scalar or 0-d array
                        try:
                            value = value.item()
                        except Exception as e:
                            warnings.warn(f"Warning: Unable to convert pandas item to scalar - {str(e)}")
                    if isinstance(value, (pd.Series, pd.DataFrame)):
                        # Take last value if Series, else default
                        if isinstance(value, pd.Series) and len(value) > 0:
                            value = value.iloc[-1]
                        else:
                            return float(default)
                    return float(value)
                except Exception as conv_err:
                    return float(default)

            # Early sanity checks to catch ambiguous Series boolean usage
            ambiguous_candidates = {
                'pattern_analysis': pattern_analysis if isinstance(pattern_analysis, pd.Series) else None,
                'risk_analysis': risk_analysis if isinstance(risk_analysis, pd.Series) else None,
            }
            for name, candidate in ambiguous_candidates.items():
                if candidate is not None:
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
                        warnings.warn(f"Warning: Failed to convert risk analysis data - {str(conv_ser_err)}")  # Continue with original data if conversion fails

            # Initialize scoring system
            buy_signals = 0
            sell_signals = 0
            risk_factors = []

            # Technical Analysis
            current_price = float(stock_data[close_col].iloc[-1])
            sma_20 = float(stock_data[close_col].rolling(20).mean().iloc[-1])
            sma_50 = float(stock_data[close_col].rolling(50).mean().iloc[-1]) if len(stock_data) >= 50 else sma_20

            # Price momentum
            try:
                cond1 = float(current_price) > float(sma_20)
                if cond1:
                    buy_signals += 1
                else:
                    sell_signals += 1
            except Exception as pm_err1:
                warnings.warn(f"Warning: Failed to compare current price with SMA-20 - {str(pm_err1)}")  # Continue with defaults if comparison fails

            try:
                cond2 = float(current_price) > float(sma_50)
                if cond2:
                    buy_signals += 1
                else:
                    sell_signals += 1
            except Exception as pm_err2:
                warnings.warn(f"Warning: Failed to compare current price with SMA-50 - {str(pm_err2)}")  # Continue with defaults if comparison fails

            # Volatility analysis
            returns = stock_data[close_col].pct_change().dropna()
            try:
                recent_volatility = _to_float(returns.tail(20).std() * np.sqrt(252), default=0.0, label="recent_volatility")
            except Exception as rv_err:
                recent_volatility = 0.0

            # Enhanced risk analysis integration
            try:
                risk_dict_cond = isinstance(risk_analysis, dict) and len(risk_analysis) > 0
                if not risk_dict_cond:
                    risk_dict_cond = isinstance(risk_analysis, pd.Series) and len(risk_analysis) > 0
            except Exception as ra_eval_err:
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

                # Process comprehensive risk measures
                advanced_var = risk_analysis.get('advanced_var_measures', {})
                risk_ratios = risk_analysis.get('risk_ratios', {})
                model_comparison = risk_analysis.get('model_comparison', {})
                risk_interpretation = risk_analysis.get('risk_interpretation', [])

                risk_factors.append(f"Risk Level: {risk_level}")

                # VaR-based signals
                var_95_pct = advanced_var.get('var_95_pct', 0)
                cvar_95_pct = advanced_var.get('cvar_95_pct', 0)

                if var_95_pct > 5:  # High daily VaR
                    sell_signals += 1
                    risk_factors.append(f"High VaR: {var_95_pct:.1f}% daily risk")
                elif var_95_pct < 2:  # Low daily VaR
                    buy_signals += 1
                    risk_factors.append(f"Low VaR: {var_95_pct:.1f}% daily risk")

                # Sharpe ratio signals
                sharpe_ratio = risk_ratios.get('sharpe_ratio', 0)
                if sharpe_ratio > 1.0:
                    buy_signals += 1
                    risk_factors.append(f"Strong risk-adjusted returns (Sharpe: {sharpe_ratio:.2f})")
                elif sharpe_ratio < 0:
                    sell_signals += 1
                    risk_factors.append(f"Poor risk-adjusted returns (Sharpe: {sharpe_ratio:.2f})")

                # Jump risk signals
                merton_premium = model_comparison.get('merton_premium_pct', 0)
                if abs(merton_premium) > 5:
                    sell_signals += 1
                    risk_factors.append(f"High jump risk premium: {merton_premium:.1f}%")

                # Traditional volatility signals
                if vol_percentile > 80:
                    sell_signals += 1
                    risk_factors.append("Very high volatility (top 20%)")
                elif vol_percentile < 20:
                    buy_signals += 1
                    risk_factors.append("Low volatility environment")

                # Add risk interpretation insights
                for insight in risk_interpretation[:2]:  # Include top 2 insights
                    risk_factors.append(insight)

            # Pattern analysis integration
            try:
                pattern_dict_cond = isinstance(pattern_analysis, dict) and len(pattern_analysis) > 0
            except Exception as pa_eval_err:
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

                if has_volume_col:
                    avg_volume = float(stock_data[volume_col].tail(20).mean())
                    recent_volume = float(stock_data[volume_col].tail(5).mean())

                    if recent_volume > avg_volume * 1.5:
                        # High volume could support the current trend
                        if current_price > sma_20:
                            buy_signals += 1
                        else:
                            sell_signals += 1
                else:
                    warnings.warn("Warning: Volume not significantly elevated compared to average")
            except Exception as vol_error:
                warnings.warn(f"Warning: Failed to analyze volume patterns - {str(vol_error)}")  # Continue without volume analysis

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

            # Enhanced overall risk assessment
            if isinstance(risk_analysis, dict) and len(risk_analysis) > 0:
                overall_risk = risk_analysis.get('risk_assessment', 'MODERATE')

                # Adjust risk level based on comprehensive metrics
                advanced_var = risk_analysis.get('advanced_var_measures', {})
                risk_ratios = risk_analysis.get('risk_ratios', {})

                var_95_pct = advanced_var.get('var_95_pct', 0)
                sharpe_ratio = risk_ratios.get('sharpe_ratio', 0)
                max_drawdown = abs(risk_ratios.get('max_drawdown', 0))

                # Risk escalation factors
                risk_escalations = 0
                if var_95_pct > 5:  # High VaR
                    risk_escalations += 1
                if sharpe_ratio < 0:  # Negative risk-adjusted returns
                    risk_escalations += 1
                if max_drawdown > 0.2:  # Large historical drawdowns
                    risk_escalations += 1

                # Adjust risk level
                if risk_escalations >= 2:
                    if 'HIGH' not in overall_risk:
                        overall_risk = 'VERY HIGH'
                elif risk_escalations == 1:
                    if overall_risk == 'LOW':
                        overall_risk = 'MODERATE'
                    elif overall_risk == 'MODERATE':
                        overall_risk = 'HIGH'
            else:
                if recent_volatility > 0.3:
                    overall_risk = 'HIGH'
                elif recent_volatility < 0.15:
                    overall_risk = 'LOW'
                else:
                    overall_risk = 'MODERATE'

            # Calculate holding period suggestion and recovery forecast
            holding_analysis = self.calculate_holding_period_suggestion(stock_data)
            recovery_forecast = self.calculate_forecast_recovery_date(stock_data)

            # Build reasoning
            reasoning_parts = [
                f"Buy signals: {buy_signals}, Sell signals: {sell_signals}",
                f"Current price vs SMA20: {'Above' if float(current_price) > float(sma_20) else 'Below'}",
                f"Recent volatility: {recent_volatility:.2%}"
            ]

            if risk_factors:
                reasoning_parts.extend(risk_factors)

            # Add holding period insights to reasoning
            if holding_analysis['confidence'] in ['HIGH', 'MEDIUM']:
                reasoning_parts.append(f"Suggested holding period: {holding_analysis['suggested_holding_days']} days")

            # Add recovery forecast insights
            if recovery_forecast.get('is_currently_in_dip', False) and recovery_forecast.get('forecast_recovery_date'):
                reasoning_parts.append(f"Expected recovery by: {recovery_forecast['forecast_recovery_date']}")
            elif recovery_forecast.get('confidence') in ['HIGH', 'MEDIUM'] and recovery_forecast.get('recovery_statistics'):
                avg_recovery = recovery_forecast['recovery_statistics'].get('average_days', 0)
                reasoning_parts.append(f"Historical recovery pattern: {avg_recovery:.1f} days average")

            result = {
                'suggestion': suggestion,
                'confidence': confidence,
                'reasoning': '; '.join(reasoning_parts),
                'risk_level': overall_risk,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'holding_period_analysis': holding_analysis,
                'recovery_forecast': recovery_forecast
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

    def calculate_holding_period_suggestion(self, stock_data):
        """
        Calculate suggested holding period based on historical positive trends.

        Args:
            stock_data (pd.DataFrame): Stock price data

        Returns:
            dict: Holding period analysis with suggested duration
        """
        try:
            # Handle MultiIndex columns
            if hasattr(stock_data.columns, 'nlevels') and stock_data.columns.nlevels > 1:
                close_col = ('Close', stock_data.columns[0][1]) if stock_data.columns[0][1] else list(stock_data.columns)[0]
            else:
                close_col = 'Close'

            if len(stock_data) < 30:
                return {
                    'suggested_holding_days': 30,
                    'confidence': 'LOW',
                    'reasoning': 'Insufficient data for trend analysis',
                    'historical_positive_streaks': []
                }

            # Calculate daily returns
            prices = stock_data[close_col]
            daily_returns = prices.pct_change().dropna()

            # Find positive streaks (consecutive positive days)
            positive_streaks = []
            current_streak = 0

            for return_val in daily_returns:
                if return_val > 0:
                    current_streak += 1
                else:
                    if current_streak > 0:
                        positive_streaks.append(current_streak)
                    current_streak = 0

            # Add final streak if it ends positively
            if current_streak > 0:
                positive_streaks.append(current_streak)

            if not positive_streaks:
                return {
                    'suggested_holding_days': 14,
                    'confidence': 'LOW',
                    'reasoning': 'No positive streaks found in historical data',
                    'historical_positive_streaks': []
                }

            # Calculate statistics
            avg_positive_streak = np.mean(positive_streaks)
            max_positive_streak = max(positive_streaks)
            median_positive_streak = np.median(positive_streaks)

            # Calculate cumulative returns during positive periods
            cumulative_positive_returns = []
            streak_start = None
            current_streak = 0

            for i, return_val in enumerate(daily_returns):
                if return_val > 0:
                    if current_streak == 0:
                        streak_start = i
                    current_streak += 1
                else:
                    if current_streak > 0 and streak_start is not None:
                        # Calculate cumulative return for this streak
                        streak_returns = daily_returns.iloc[streak_start:i]
                        cum_return = (1 + streak_returns).prod() - 1
                        cumulative_positive_returns.append({
                            'duration': current_streak,
                            'cumulative_return': cum_return,
                            'avg_daily_return': streak_returns.mean()
                        })
                    current_streak = 0
                    streak_start = None

            # Add final streak if it ends positively
            if current_streak > 0 and streak_start is not None:
                streak_returns = daily_returns.iloc[streak_start:]
                cum_return = (1 + streak_returns).prod() - 1
                cumulative_positive_returns.append({
                    'duration': current_streak,
                    'cumulative_return': cum_return,
                    'avg_daily_return': streak_returns.mean()
                })

            # Determine optimal holding period based on historical performance
            if cumulative_positive_returns:
                # Find the duration that maximizes average cumulative return
                avg_returns_by_duration = {}
                for streak_data in cumulative_positive_returns:
                    duration = streak_data['duration']
                    if duration not in avg_returns_by_duration:
                        avg_returns_by_duration[duration] = []
                    avg_returns_by_duration[duration].append(streak_data['cumulative_return'])

                # Calculate average return for each duration
                duration_performance = {}
                for duration, returns in avg_returns_by_duration.items():
                    duration_performance[duration] = {
                        'avg_return': np.mean(returns),
                        'frequency': len(returns),
                        'max_return': max(returns),
                        'min_return': min(returns)
                    }

                # Find optimal duration (considering both return and frequency)
                optimal_duration = max(duration_performance.keys(),
                                     key=lambda d: duration_performance[d]['avg_return'] *
                                                  min(duration_performance[d]['frequency'] / len(positive_streaks), 1.0))

                suggested_holding = min(max(optimal_duration, 7), 90)  # Cap between 1 week and 3 months
            else:
                suggested_holding = int(median_positive_streak)

            # Determine confidence level
            if len(positive_streaks) >= 10 and avg_positive_streak >= 5:
                confidence = 'HIGH'
            elif len(positive_streaks) >= 5 and avg_positive_streak >= 3:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'

            # Build reasoning
            reasoning_parts = [
                f"Historical analysis shows {len(positive_streaks)} positive streaks",
                f"Average positive streak: {avg_positive_streak:.1f} days",
                f"Longest streak: {max_positive_streak} days",
                f"Median streak: {median_positive_streak:.1f} days"
            ]

            if cumulative_positive_returns:
                avg_cum_return = np.mean([data['cumulative_return'] for data in cumulative_positive_returns])
                reasoning_parts.append(f"Average cumulative return during positive periods: {avg_cum_return:.2%}")

            return {
                'suggested_holding_days': int(suggested_holding),
                'confidence': confidence,
                'reasoning': '; '.join(reasoning_parts),
                'historical_positive_streaks': positive_streaks,
                'streak_statistics': {
                    'average': avg_positive_streak,
                    'median': median_positive_streak,
                    'maximum': max_positive_streak,
                    'total_streaks': len(positive_streaks)
                },
                'cumulative_returns_analysis': cumulative_positive_returns[:5]  # Top 5 for summary
            }

        except Exception as e:
            return {
                'suggested_holding_days': 30,
                'confidence': 'LOW',
                'reasoning': f'Error in holding period analysis: {str(e)}',
                'historical_positive_streaks': []
            }

    def calculate_forecast_recovery_date(self, stock_data):
        """
        Forecast when a ticker is expected to climb based on historical recovery patterns after dips.

        Args:
            stock_data (pd.DataFrame): Stock price data

        Returns:
            dict: Recovery forecast with expected date and confidence
        """
        try:
            # Handle MultiIndex columns
            if hasattr(stock_data.columns, 'nlevels') and stock_data.columns.nlevels > 1:
                close_col = ('Close', stock_data.columns[0][1]) if stock_data.columns[0][1] else list(stock_data.columns)[0]
            else:
                close_col = 'Close'

            if len(stock_data) < 50:
                return {
                    'forecast_recovery_date': None,
                    'days_to_recovery': None,
                    'confidence': 'LOW',
                    'reasoning': 'Insufficient data for recovery pattern analysis',
                    'historical_dip_recoveries': []
                }

            prices = stock_data[close_col]
            daily_returns = prices.pct_change().dropna()

            # Define dip as a decline of at least 5% from recent high
            dip_threshold = -0.05
            recovery_threshold = 0.02  # 2% gain from dip low

            # Find dips and subsequent recoveries
            recovery_patterns = []

            # Rolling 20-day high to identify dips
            rolling_high = prices.rolling(window=20, min_periods=1).max()

            i = 20  # Start after initial rolling window
            while i < len(prices) - 10:  # Leave room for recovery analysis
                current_price = prices.iloc[i]
                recent_high = rolling_high.iloc[i-1]

                # Check if current price represents a dip
                dip_magnitude = (current_price - recent_high) / recent_high

                if dip_magnitude <= dip_threshold:
                    # Found a dip, now look for recovery
                    dip_price = current_price
                    recovery_start_idx = i

                    # Look for recovery in the next 30 days
                    recovery_found = False
                    for j in range(i + 1, min(i + 31, len(prices))):
                        future_price = prices.iloc[j]
                        recovery_magnitude = (future_price - dip_price) / dip_price

                        if recovery_magnitude >= recovery_threshold:
                            # Recovery found
                            days_to_recovery = j - i
                            recovery_patterns.append({
                                'dip_date': prices.index[i],
                                'recovery_date': prices.index[j],
                                'dip_magnitude': dip_magnitude,
                                'recovery_magnitude': recovery_magnitude,
                                'days_to_recovery': days_to_recovery,
                                'dip_price': dip_price,
                                'recovery_price': future_price
                            })
                            recovery_found = True
                            break

                    # Skip ahead to avoid overlapping dips
                    if recovery_found:
                        i = j + 5  # Skip 5 days after recovery
                    else:
                        i += 10  # Skip ahead if no recovery found
                else:
                    i += 1

            if not recovery_patterns:
                return {
                    'forecast_recovery_date': None,
                    'days_to_recovery': None,
                    'confidence': 'LOW',
                    'reasoning': 'No historical dip-recovery patterns found',
                    'historical_dip_recoveries': []
                }

            # Analyze recovery patterns
            recovery_days = [pattern['days_to_recovery'] for pattern in recovery_patterns]
            avg_recovery_days = np.mean(recovery_days)
            median_recovery_days = np.median(recovery_days)

            # Check if currently in a dip
            current_price = prices.iloc[-1]
            recent_high = rolling_high.iloc[-1]
            current_dip_magnitude = (current_price - recent_high) / recent_high

            is_currently_in_dip = current_dip_magnitude <= dip_threshold

            if is_currently_in_dip:
                # Forecast recovery based on historical patterns
                # Use median recovery time as it's more robust to outliers
                forecast_days = int(median_recovery_days)

                # Calculate forecast date
                last_date = stock_data.index[-1]
                if hasattr(last_date, 'date'):
                    last_date = last_date.date()

                forecast_date = last_date + timedelta(days=forecast_days)

                # Determine confidence based on consistency of historical patterns
                recovery_day_std = np.std(recovery_days)
                consistency_ratio = recovery_day_std / avg_recovery_days if avg_recovery_days > 0 else 1

                if len(recovery_patterns) >= 5 and consistency_ratio < 0.5:
                    confidence = 'HIGH'
                elif len(recovery_patterns) >= 3 and consistency_ratio < 0.8:
                    confidence = 'MEDIUM'
                else:
                    confidence = 'LOW'

                reasoning_parts = [
                    f"Currently in dip: {current_dip_magnitude:.1%} from recent high",
                    f"Historical analysis of {len(recovery_patterns)} recovery patterns",
                    f"Average recovery time: {avg_recovery_days:.1f} days",
                    f"Median recovery time: {median_recovery_days:.1f} days"
                ]

                # Additional insights
                successful_recoveries = len(recovery_patterns)
                avg_recovery_magnitude = np.mean([p['recovery_magnitude'] for p in recovery_patterns])
                reasoning_parts.append(f"Historical success rate: {successful_recoveries} recoveries analyzed")
                reasoning_parts.append(f"Average recovery gain: {avg_recovery_magnitude:.1%}")

            else:
                forecast_date = None
                forecast_days = None
                confidence = 'LOW'
                reasoning_parts = [
                    f"Not currently in significant dip ({current_dip_magnitude:.1%} from recent high)",
                    f"Historical analysis shows {len(recovery_patterns)} recovery patterns",
                    f"Average recovery time when dips occur: {avg_recovery_days:.1f} days"
                ]

            return {
                'forecast_recovery_date': forecast_date.strftime('%Y-%m-%d') if forecast_date else None,
                'days_to_recovery': forecast_days,
                'confidence': confidence,
                'reasoning': '; '.join(reasoning_parts),
                'is_currently_in_dip': is_currently_in_dip,
                'current_dip_magnitude': current_dip_magnitude,
                'historical_dip_recoveries': recovery_patterns[-5:],  # Last 5 for summary
                'recovery_statistics': {
                    'average_days': avg_recovery_days,
                    'median_days': median_recovery_days,
                    'total_patterns': len(recovery_patterns),
                    'fastest_recovery': min(recovery_days) if recovery_days else None,
                    'slowest_recovery': max(recovery_days) if recovery_days else None
                }
            }

        except Exception as e:
            return {
                'forecast_recovery_date': None,
                'days_to_recovery': None,
                'confidence': 'LOW',
                'reasoning': f'Error in recovery forecast analysis: {str(e)}',
                'historical_dip_recoveries': []
            }

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
