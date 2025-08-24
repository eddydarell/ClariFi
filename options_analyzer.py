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
            if stock_data is None or stock_data.empty:
                return {
                    'ticker': ticker,
                    'analysis_type': 'basic_options',
                    'message': 'Options analysis requires stock price data',
                    'recommendations': []
                }

            current_price = stock_data['Close'].iloc[-1]
            volatility = stock_data['Close'].pct_change().std() * np.sqrt(252)  # Annualized volatility

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

                    option_data = {
                        'expiration_days': days,
                        'strike': round(strike, 2),
                        'current_price': round(current_price, 2),
                        'call_price': round(call_price, 2),
                        'put_price': round(put_price, 2),
                        'call_delta': round(call_greeks['delta'], 4),
                        'call_gamma': round(call_greeks['gamma'], 4),
                        'call_theta': round(call_greeks['theta'], 4),
                        'put_delta': round(put_greeks['delta'], 4),
                        'put_gamma': round(put_greeks['gamma'], 4),
                        'put_theta': round(put_greeks['theta'], 4),
                        'volatility': round(volatility * 100, 2)  # As percentage
                    }

                    options_analysis.append(option_data)

            # Generate strategy recommendations using comprehensive risk analysis
            risk_analysis = self.comprehensive_risk_analysis(stock_data)
            strategies = self._generate_options_strategies(current_price, volatility, risk_analysis)

            return {
                'ticker': ticker,
                'current_price': round(current_price, 2),
                'implied_volatility': round(volatility * 100, 2),
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
        try:
            if stock_data is None or stock_data.empty or len(stock_data) < 20:
                return {
                    'suggestion': 'HOLD',
                    'confidence': 'LOW',
                    'reasoning': 'Insufficient data for analysis',
                    'risk_level': 'UNKNOWN'
                }

            buy_signals = 0
            sell_signals = 0
            risk_factors = []

            current_price = float(stock_data['Close'].iloc[-1])
            sma_20 = float(stock_data['Close'].rolling(20).mean().iloc[-1])
            sma_50 = float(stock_data['Close'].rolling(50).mean().iloc[-1]) if len(stock_data) >= 50 else sma_20

            if current_price > sma_20:
                buy_signals += 1
            else:
                sell_signals += 1
            if current_price > sma_50:
                buy_signals += 1
            else:
                sell_signals += 1

            returns = stock_data['Close'].pct_change().dropna()
            recent_volatility = float(returns.tail(20).std() * np.sqrt(252)) if len(returns) > 0 else 0.0

            # Enhanced risk analysis processing
            if isinstance(risk_analysis, dict) and risk_analysis:
                risk_level = risk_analysis.get('risk_assessment', 'Moderate Risk')
                vol_percentile = risk_analysis.get('volatility_percentile', 50)

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

            if isinstance(pattern_analysis, dict) and pattern_analysis.get('trend_strength') is not None:
                ts = pattern_analysis.get('trend_strength')
                try:
                    ts = float(ts)
                    if ts > 0.6:
                        buy_signals += 2
                    elif ts < -0.6:
                        sell_signals += 2
                except Exception as e:
                    warnings.warn(f"Warning: Failed to analyze trend strength - {str(e)}")

            if 'Volume' in stock_data.columns:
                avg_volume = float(stock_data['Volume'].tail(20).mean())
                recent_volume = float(stock_data['Volume'].tail(5).mean())
                if recent_volume > avg_volume * 1.5:
                    if current_price > sma_20:
                        buy_signals += 1
                    else:
                        sell_signals += 1

            price_changes = stock_data['Close'].diff().tail(14)
            gains = price_changes.where(price_changes > 0, 0).mean()
            losses = -price_changes.where(price_changes < 0, 0).mean()
            if losses != 0:
                rs = gains / losses
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 50
            if rsi < 30:
                buy_signals += 1
                risk_factors.append("Potentially oversold (RSI < 30)")
            elif rsi > 70:
                sell_signals += 1
                risk_factors.append("Potentially overbought (RSI > 70)")

            total = buy_signals + sell_signals
            if total == 0:
                suggestion = 'HOLD'
                confidence = 'LOW'
            else:
                ratio = buy_signals / total
                if ratio >= 0.7:
                    suggestion = 'BUY'
                    confidence = 'HIGH' if ratio >= 0.8 else 'MEDIUM'
                elif ratio <= 0.3:
                    suggestion = 'SELL'
                    confidence = 'HIGH' if ratio <= 0.2 else 'MEDIUM'
                else:
                    suggestion = 'HOLD'
                    confidence = 'MEDIUM'

            # Enhanced overall risk assessment
            if isinstance(risk_analysis, dict) and risk_analysis:
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

            reasoning = [
                f"Buy signals: {buy_signals}, Sell signals: {sell_signals}",
                f"Current price vs SMA20: {'Above' if current_price > sma_20 else 'Below'}",
                f"Recent volatility: {recent_volatility:.2%}"
            ]
            reasoning.extend(risk_factors)

            result = {
                'suggestion': suggestion,
                'confidence': confidence,
                'reasoning': '; '.join(reasoning),
                'risk_level': overall_risk,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.advice_history.append(result)
            return result
        except Exception as e:
            return {
                'suggestion': 'HOLD',
                'confidence': 'LOW',
                'reasoning': f'Analysis error: {e}',
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
