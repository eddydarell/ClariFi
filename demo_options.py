#!/usr/bin/env python3
"""
Options Analysis Demo
Demonstrates the Black-Scholes implementation and investment suggestions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from options_analyzer import OptionsAnalyzer, InvestmentAdvisor
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_sample_data(ticker, days=252, start_price=100, volatility=0.2):
    """Create sample stock data for demonstration."""
    dates = pd.date_range(start=datetime.now() - timedelta(days=days),
                         end=datetime.now(), freq='D')

    # Generate realistic stock price movements
    returns = np.random.normal(0.0005, volatility/np.sqrt(252), len(dates))

    # Add some trends and patterns
    trend = np.linspace(0, 0.2, len(dates))  # 20% growth over period
    cyclical = 0.1 * np.sin(np.linspace(0, 4*np.pi, len(dates)))

    total_returns = returns + trend/len(dates) + cyclical/len(dates)

    prices = [start_price]
    for ret in total_returns[1:]:
        prices.append(prices[-1] * (1 + ret))

    # Create volume data
    volume = np.random.randint(1000000, 5000000, len(dates))

    data = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Close': prices,
        'Volume': volume
    })

    data.set_index('Date', inplace=True)
    return data

def demo_black_scholes():
    """Demonstrate Black-Scholes calculations."""
    print("🔬 BLACK-SCHOLES OPTIONS PRICING DEMO")
    print("=" * 50)

    analyzer = OptionsAnalyzer()

    # Sample parameters
    S = 150.0  # Current stock price
    K = 150.0  # Strike price (at-the-money)
    T = 0.25   # 3 months to expiration
    r = 0.05   # 5% risk-free rate
    sigma = 0.25  # 25% volatility

    print(f"📊 Parameters:")
    print(f"   Stock Price (S): ${S:.2f}")
    print(f"   Strike Price (K): ${K:.2f}")
    print(f"   Time to Expiration: {T*365:.0f} days")
    print(f"   Risk-free Rate: {r:.1%}")
    print(f"   Volatility: {sigma:.1%}")
    print()

    # Calculate option prices
    call_price = analyzer.black_scholes_call(S, K, T, r, sigma)
    put_price = analyzer.black_scholes_put(S, K, T, r, sigma)

    print(f"💰 Option Prices:")
    print(f"   Call Option: ${call_price:.2f}")
    print(f"   Put Option: ${put_price:.2f}")
    print(f"   Straddle: ${call_price + put_price:.2f}")
    print()

    # Calculate Greeks
    call_greeks = analyzer.calculate_greeks(S, K, T, r, sigma, 'call')
    put_greeks = analyzer.calculate_greeks(S, K, T, r, sigma, 'put')

    print(f"🔢 Greeks (Call/Put):")
    print(f"   Delta: {call_greeks['delta']:.3f} / {put_greeks['delta']:.3f}")
    print(f"   Gamma: {call_greeks['gamma']:.4f} / {put_greeks['gamma']:.4f}")
    print(f"   Theta: ${call_greeks['theta']:.3f} / ${put_greeks['theta']:.3f} (daily)")
    print(f"   Vega: ${call_greeks['vega']:.3f} / ${put_greeks['vega']:.3f} (1% vol change)")
    print(f"   Rho: ${call_greeks['rho']:.3f} / ${put_greeks['rho']:.3f} (1% rate change)")
    print()

def demo_risk_analysis():
    """Demonstrate risk analysis on sample data."""
    print("⚠️ STOCK RISK ANALYSIS DEMO")
    print("=" * 50)

    analyzer = OptionsAnalyzer()

    # Create sample data for different volatility stocks
    stocks = {
        'STABLE': create_sample_data('STABLE', volatility=0.15, start_price=100),
        'MODERATE': create_sample_data('MODERATE', volatility=0.25, start_price=120),
        'VOLATILE': create_sample_data('VOLATILE', volatility=0.40, start_price=80)
    }

    for ticker, data in stocks.items():
        print(f"\n📈 {ticker} STOCK ANALYSIS:")
        risk_analysis = analyzer.analyze_stock_risk(data)

        print(f"   Current Price: ${risk_analysis['current_price']:.2f}")
        print(f"   Current Volatility: {risk_analysis['current_volatility']:.1%}")
        print(f"   Risk Assessment: {risk_analysis['risk_assessment']}")

        if risk_analysis['volatility_percentile'] is not None:
            print(f"   Volatility Percentile: {risk_analysis['volatility_percentile']:.1f}%")

        # Show expected moves
        print(f"   Expected Moves:")
        for timeframe in ['30d', '90d']:
            if timeframe in risk_analysis['risk_metrics']:
                metrics = risk_analysis['risk_metrics'][timeframe]
                print(f"     {timeframe}: ±{metrics['expected_move']:.1%}")

def demo_investment_suggestions():
    """Demonstrate investment suggestion engine."""
    print("\n💡 INVESTMENT SUGGESTION DEMO")
    print("=" * 50)

    advisor = InvestmentAdvisor()
    analyzer = OptionsAnalyzer()

    # Create sample portfolio
    portfolio = {
        'GROWTH': create_sample_data('GROWTH', volatility=0.30, start_price=200),
        'VALUE': create_sample_data('VALUE', volatility=0.20, start_price=50),
        'DEFENSIVE': create_sample_data('DEFENSIVE', volatility=0.15, start_price=80)
    }

    # Analyze each stock
    portfolio_data = {}
    print(f"\n📊 Individual Stock Analysis:")

    for ticker, stock_data in portfolio.items():
        # Get risk analysis
        risk_analysis = analyzer.analyze_stock_risk(stock_data)

        # Get investment suggestion
        suggestion = advisor.generate_investment_suggestion(
            stock_data,
            risk_analysis=risk_analysis
        )

        portfolio_data[ticker] = {
            'stock_data': stock_data,
            'risk_analysis': risk_analysis
        }

        # Display suggestion
        action_emoji = "🟢" if suggestion['suggestion'] == 'BUY' else \
                      "🔴" if suggestion['suggestion'] == 'SELL' else "🟡"

        print(f"   {action_emoji} {ticker}: {suggestion['suggestion']} "
              f"({suggestion['confidence']} confidence)")
        print(f"      Risk: {suggestion['risk_level']}")
        print(f"      Signals: {suggestion['buy_signals']} buy, {suggestion['sell_signals']} sell")

    # Get portfolio-level advice
    print(f"\n🎯 Portfolio-Level Recommendations:")
    portfolio_advice = advisor.get_portfolio_suggestions(portfolio_data)

    summary = portfolio_advice['portfolio_summary']
    print(f"   📊 Summary:")
    print(f"      🟢 BUY recommendations: {summary['buy_recommendations']}")
    print(f"      🔴 SELL recommendations: {summary['sell_recommendations']}")
    print(f"      🟡 HOLD recommendations: {summary['hold_recommendations']}")
    print(f"      ⚠️ High-risk positions: {summary['high_risk_positions']}")
    print(f"      📈 Overall portfolio risk: {portfolio_advice['portfolio_risk']}")
    print(f"      🎯 Diversification: {portfolio_advice['diversification_note']}")

def main():
    """Run all demonstrations."""
    print("🚀 OPTIONS ANALYZER & INVESTMENT ADVISOR DEMO")
    print("=" * 60)
    print()

    try:
        # Demo 1: Black-Scholes calculations
        demo_black_scholes()

        # Demo 2: Risk analysis
        demo_risk_analysis()

        # Demo 3: Investment suggestions
        demo_investment_suggestions()

        print("\n✅ Demo completed successfully!")
        print("\n💡 Integration Notes:")
        print("   • Black-Scholes equation implemented for options pricing")
        print("   • Risk assessment using volatility analysis")
        print("   • Investment suggestions: BUY/SELL/HOLD with confidence levels")
        print("   • Portfolio-level recommendations and diversification analysis")
        print("   • Greeks calculation for risk management")
        print("   • Expected move calculations for different timeframes")

    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
