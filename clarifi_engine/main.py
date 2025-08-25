#!/usr/bin/env python3
"""
ClariFi: Clarify your Finances
Advanced Market Intelligence & Pattern Analysis Tool

Orchestrates stock data downloading and comprehensive financial analysis.
Provides an easy-to-use interface for stock analysis with seasonal patterns,
event correlation, options analysis, and investment suggestions.
"""

import argparse
import os
import sys
import calendar
from datetime import datetime, timedelta

# Add the current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from stock_downloader import StockDownloader
    from stock_visualizer import StockVisualizer
    from pattern_analyzer import PatternAnalyzer
    from event_correlator import EventCorrelator
    from advanced_visualizer import AdvancedVisualizer
    from options_analyzer import OptionsAnalyzer, InvestmentAdvisor
    from seasonal_analyzer import SeasonalAnalyzer
    from live_monitor import LiveStockMonitor
    from stock_screener import StockScreener
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all required packages are installed.")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)


class AdvancedStockAnalysis:
    def __init__(self):
        self.downloader = StockDownloader()
        self.visualizer = StockVisualizer()
        self.pattern_analyzer = PatternAnalyzer()
        self.event_correlator = EventCorrelator()
        self.advanced_visualizer = AdvancedVisualizer()
        self.options_analyzer = OptionsAnalyzer()
        self.investment_advisor = InvestmentAdvisor()
        self.seasonal_analyzer = SeasonalAnalyzer()

    def comprehensive_analysis(self, tickers, period="1y", download=True,
                             include_patterns=True, include_events=True,
                             include_advanced_viz=True, include_options=True,
                             include_investment_advice=True, include_seasonal=True,
                             include_deep=False, deep_chunk_months=3):
        """
        Perform comprehensive market analysis including patterns, events, options, and investment advice.

        Args:
            tickers (list): List of stock tickers
            period (str): Time period for data
            download (bool): Whether to download fresh data
            include_patterns (bool): Whether to include pattern analysis
            include_events (bool): Whether to include event correlation
            include_advanced_viz (bool): Whether to create advanced visualizations
            include_options (bool): Whether to include Black-Scholes options analysis
            include_investment_advice (bool): Whether to generate investment suggestions
            include_seasonal (bool): Whether to include seasonal analysis
            include_deep (bool): Whether to include deep backtesting analysis
            deep_chunk_months (int): Chunk size in months for deep analysis
        """
        print(f"🚀 ClariFi: Clarify your Finances")
        print("=======================")
        print(f"🚀 === COMPREHENSIVE MARKET ANALYSIS === 🚀")
        print(f"Tickers: {', '.join(tickers)}")
        print(f"Period: {period}")
        print(f"Analysis Features: Patterns={include_patterns}, Events={include_events}, Advanced Viz={include_advanced_viz}, Options={include_options}, Investment Advice={include_investment_advice}, Seasonal={include_seasonal}, Deep={include_deep}")
        if include_deep:
            print(f"Deep Analysis: Chunk size = {deep_chunk_months} months")
        print("=" * 60)

        # Step 1: Download data
        stock_data_dict = {}
        if download:
            print("\n📊 DOWNLOADING STOCK DATA...")
            results = self.downloader.download_multiple_stocks(tickers, None, None, period)

            if not results:
                print("❌ No data downloaded. Exiting.")
                return

            print("✅ Data download completed!")

        # Load data into memory
        print("\n📋 LOADING DATA...")
        for ticker in tickers:
            files = self.visualizer.find_stock_files(ticker)
            if files:
                latest_file = max(files, key=os.path.getctime)
                data = self.visualizer.load_stock_data(latest_file)
                if data is not None:
                    stock_data_dict[ticker] = data
                    print(f"  ✓ {ticker}: {len(data)} records loaded")
                else:
                    print(f"  ❌ {ticker}: Failed to load data")

        if not stock_data_dict:
            print("❌ No valid data loaded. Exiting.")
            return

        # Step 2: Pattern Analysis
        correlation_results = None
        volatility_results = None
        trend_results = None

        if include_patterns:
            print("\n🔍 PATTERN ANALYSIS...")

            # Correlation patterns
            print("  📈 Analyzing correlation patterns...")
            correlation_results = self.pattern_analyzer.analyze_correlation_patterns(stock_data_dict)

            # Volatility patterns
            print("  📊 Analyzing volatility patterns...")
            volatility_results = self.pattern_analyzer.detect_volatility_patterns(stock_data_dict)

            # Trend analysis
            print("  📉 Analyzing trend strength...")
            trend_results = self.pattern_analyzer.analyze_trend_strength(stock_data_dict)

            print("✅ Pattern analysis completed!")

        # Step 3: Event Correlation
        event_results = None
        unusual_movements = None

        if include_events:
            print("\n🌍 EVENT CORRELATION ANALYSIS...")

            print("  📰 Correlating with major events...")
            event_results = self.event_correlator.correlate_events_with_movements(stock_data_dict)

            print("  🚨 Identifying unusual movements...")
            unusual_movements = self.event_correlator.identify_unusual_movements(stock_data_dict)

            print("✅ Event correlation completed!")

        # Step 4: Advanced Visualizations
        if include_advanced_viz:
            print("\n🎨 CREATING ADVANCED VISUALIZATIONS...")

            if correlation_results:
                print("  📊 Creating correlation heatmaps...")
                self.advanced_visualizer.plot_correlation_heatmap(correlation_results)
                print("  📈 Creating rolling correlation plots...")
                self.advanced_visualizer.plot_rolling_correlations(correlation_results)

            if volatility_results:
                print("  🌊 Creating volatility clustering plots...")
                self.advanced_visualizer.plot_volatility_clustering(volatility_results)

            if event_results:
                print("  📰 Creating event impact visualizations...")
                self.advanced_visualizer.plot_event_impact_analysis(event_results)

            # Support/Resistance for first ticker
            if tickers:
                print(f"  🎯 Creating support/resistance for {tickers[0]}...")
                sr_data = self.pattern_analyzer.identify_support_resistance(
                    stock_data_dict[tickers[0]], tickers[0])
                self.advanced_visualizer.plot_support_resistance(
                    sr_data, stock_data_dict[tickers[0]])

            print("✅ Advanced visualizations completed!")

        # Step 5: Enhanced Options Analysis and Risk Assessment
        options_results = {}
        if include_options:
            print("\n⚖️ ENHANCED OPTIONS & RISK ANALYSIS...")
            for ticker in tickers:
                if ticker in stock_data_dict:
                    print(f"  🔍 Analyzing comprehensive risk for {ticker}...")
                    risk_analysis = self.options_analyzer.comprehensive_risk_analysis(stock_data_dict[ticker])

                    # Also get the traditional options analysis for pricing data
                    options_analysis = self.options_analyzer.analyze_options(ticker, stock_data_dict[ticker])

                    # Merge the results
                    merged_results = {**risk_analysis, **options_analysis}
                    options_results[ticker] = merged_results

                    # Display key metrics
                    current_price = risk_analysis['current_price']
                    current_vol = risk_analysis['current_volatility']
                    risk_level = risk_analysis['risk_assessment']

                    # Get comprehensive risk metrics
                    advanced_var = risk_analysis.get('advanced_var_measures', {})
                    risk_ratios = risk_analysis.get('risk_ratios', {})
                    var_95_pct = advanced_var.get('var_95_pct', 0)
                    sharpe_ratio = risk_ratios.get('sharpe_ratio', 0)

                    print(f"      💰 Current Price: ${current_price:.2f}")
                    print(f"      📊 Current Volatility: {current_vol:.1%}")
                    print(f"      ⚠️ Risk Level: {risk_level}")
                    print(f"      📊 VaR (95%): {var_95_pct:.1f}% daily")

                    if sharpe_ratio != 0:
                        sharpe_emoji = "🌟" if sharpe_ratio > 1.0 else "📊" if sharpe_ratio > 0.5 else "❌"
                        print(f"      {sharpe_emoji} Sharpe Ratio: {sharpe_ratio:.2f}")

                    vol_percentile = risk_analysis.get('volatility_percentile', 'N/A')
                    if vol_percentile != 'N/A':
                        print(f"      📈 Volatility Percentile: {vol_percentile:.1f}%")

                    # Show expected moves for key timeframes
                    for timeframe in ['30d', '90d']:
                        if timeframe in risk_analysis['risk_metrics']:
                            metrics = risk_analysis['risk_metrics'][timeframe]
                            expected_move = metrics['expected_move']
                            print(f"      🎯 Expected {timeframe} move: ±{expected_move:.1%}")

            print("✅ Options analysis completed!")

        # Step 6: Investment Suggestions
        investment_suggestions = {}
        portfolio_advice = None
        if include_investment_advice:
            print("\n💡 GENERATING INVESTMENT SUGGESTIONS...")

            # Prepare comprehensive data for investment advisor
            portfolio_data = {}
            for ticker in tickers:
                if ticker in stock_data_dict:
                    portfolio_data[ticker] = {
                        'stock_data': stock_data_dict[ticker],
                        'pattern_analysis': trend_results.get(ticker) if trend_results else None,
                        'risk_analysis': options_results.get(ticker) if options_results else None
                    }

            # Generate portfolio-level suggestions
            print("  🎯 Analyzing portfolio recommendations...")
            portfolio_advice = self.investment_advisor.get_portfolio_suggestions(
                portfolio_data, correlation_results
            )

            # Display individual suggestions
            for ticker, suggestion in portfolio_advice['individual_suggestions'].items():
                action_emoji = "🟢" if suggestion['suggestion'] == 'BUY' else \
                              "🔴" if suggestion['suggestion'] == 'SELL' else "🟡"
                confidence_emoji = "🔥" if suggestion['confidence'] == 'HIGH' else \
                                  "👍" if suggestion['confidence'] == 'MEDIUM' else "🤔"

                print(f"  {action_emoji} {ticker}: {suggestion['suggestion']} "
                      f"({suggestion['confidence']} confidence) {confidence_emoji}")
                print(f"      Risk: {suggestion['risk_level']}")
                print(f"      Reasoning: {suggestion['reasoning']}")

                # Display enhanced features: holding period and recovery forecast
                if 'holding_period_analysis' in suggestion:
                    holding = suggestion['holding_period_analysis']
                    print(f"      ⏱️  Suggested Holding Period: {holding['suggested_holding_days']} days ({holding['confidence']} confidence)")

                if 'recovery_forecast' in suggestion:
                    recovery = suggestion['recovery_forecast']
                    if recovery.get('is_currently_in_dip', False) and recovery.get('forecast_recovery_date'):
                        print(f"      🔮 Recovery Forecast: {recovery['forecast_recovery_date']} ({recovery.get('confidence', 'UNKNOWN')} confidence)")
                        print(f"      📉 Currently in dip: {recovery.get('current_dip_magnitude', 0):.1%} from recent high")
                    elif not recovery.get('is_currently_in_dip', True) and recovery.get('recovery_statistics'):
                        stats = recovery['recovery_statistics']
                        print(f"      📈 Historical Recovery Pattern: {stats.get('average_days', 0):.1f} days average")
                print()

            print("✅ Investment suggestions completed!")

        # Step 6.5: Seasonal Analysis
        seasonal_results = {}
        if include_seasonal:
            print("\n🗓️ SEASONAL ANALYSIS...")
            for ticker in tickers:
                if ticker in stock_data_dict:
                    print(f"  📅 Analyzing seasonal patterns for {ticker}...")
                    seasonal_result = self.seasonal_analyzer.analyze(stock_data_dict[ticker])
                    if seasonal_result:
                        seasonal_results[ticker] = seasonal_result

                        # Display key seasonal insights
                        print(f"      🌟 Recommendation: {seasonal_result['recommendation']}")
                        print(f"      📊 Seasonal Bias Score: {seasonal_result['bias_score']:.2f}")
                        print(f"      📈 Best Months: {', '.join(seasonal_result['best_months'])}")
                        print(f"      📉 Worst Months: {', '.join(seasonal_result['worst_months'])}")
                        print(f"      💡 Pattern: {seasonal_result['seasonal_summary']}")
                    else:
                        print(f"      ⚠️ Insufficient data for seasonal analysis")

            if seasonal_results:
                print("✅ Seasonal analysis completed!")
            else:
                print("⚠️ No seasonal patterns detected (insufficient data)")

        # Step 6.6: Deep Analysis (Historical Backtesting)
        deep_results = {}
        if include_deep:
            print("\n🔁 DEEP BACKTESTING ANALYSIS...")
            print(f"   Chunk size: {deep_chunk_months} months")

            # Import the engine for deep analysis functionality
            try:
                from engine import ClariFiEngine
                engine = ClariFiEngine()

                for ticker in tickers:
                    if ticker in stock_data_dict:
                        print(f"  🔍 Running deep analysis for {ticker}...")
                        try:
                            deep_result = engine._run_deep_analysis(
                                ticker,
                                stock_data_dict[ticker].copy(),
                                chunk_months=deep_chunk_months
                            )
                            if deep_result and not deep_result.get('error'):
                                deep_results[ticker] = deep_result
                                summary = deep_result.get('summary', {})
                                precision = summary.get('coefficient_of_precision', 0)
                                chunks_eval = summary.get('chunks_evaluated', 0)
                                print(f"    ✓ Precision coefficient: {precision:.2%}")
                                print(f"    📊 Evaluated {chunks_eval} chunks")
                            else:
                                error_msg = deep_result.get('error', 'Unknown error') if deep_result else 'Failed to execute'
                                print(f"    ❌ Deep analysis failed: {error_msg}")
                        except Exception as e:
                            print(f"    ❌ Deep analysis error for {ticker}: {str(e)}")
                    else:
                        print(f"    ⚠️ No data available for {ticker}")

                if deep_results:
                    print("✅ Deep analysis completed!")
                else:
                    print("⚠️ No deep analysis results generated")

            except ImportError as e:
                print(f"    ❌ Could not import engine for deep analysis: {e}")
                print("    💡 Deep analysis requires the ClariFiEngine module")

        # Step 7: Generate Summary Report
        print("\n📋 GENERATING ANALYSIS SUMMARY...")
        self._generate_summary_report(tickers, correlation_results, volatility_results,
                                    trend_results, event_results, unusual_movements,
                                    options_results, portfolio_advice, seasonal_results, deep_results)

        print("\n🎉 === COMPREHENSIVE ANALYSIS COMPLETED === 🎉")
        print(f"📁 Data files: {self.downloader.data_dir}/")
        print(f"📊 Visualizations: {self.visualizer.output_dir}/")
        print(f"📈 Advanced charts: {self.advanced_visualizer.output_dir}/")

    def seasonal_only(self, tickers, period="5y", download=True):
        """
        Perform seasonal analysis only for the given tickers.

        Args:
            tickers (list): List of stock tickers
            period (str): Time period for data (default 5y for better seasonal patterns)
            download (bool): Whether to download fresh data
        """
        print("� ClariFi: Clarify your Finances")
        print("=======================")
        print("�🗓️ === SEASONAL & HOLIDAY ANALYSIS === 🗓️")
        print(f"Tickers: {', '.join(tickers)}")
        print(f"Period: {period}")
        print("=" * 50)

        # Step 1: Download data if requested
        if download:
            print("\n📊 DOWNLOADING STOCK DATA...")
            results = self.downloader.download_multiple_stocks(tickers, None, None, period)
            if not results:
                print("❌ No data downloaded. Continuing with existing data...")
            else:
                print("✅ Data download completed!")

        # Step 2: Load data
        stock_data_dict = {}
        print("\n📋 LOADING DATA...")
        for ticker in tickers:
            files = self.visualizer.find_stock_files(ticker)
            if files:
                latest_file = max(files, key=os.path.getctime)
                data = self.visualizer.load_stock_data(latest_file)
                if data is not None:
                    stock_data_dict[ticker] = data
                    print(f"  ✓ {ticker}: {len(data)} records loaded")
                else:
                    print(f"  ❌ {ticker}: Failed to load data")
            else:
                print(f"  ❌ {ticker}: No data files found")

        if not stock_data_dict:
            print("❌ No valid data loaded. Exiting.")
            return

        # Step 3: Seasonal Analysis
        print("\n🧮 ANALYZING SEASONAL PATTERNS...")
        seasonal_results = {}

        for ticker in tickers:
            if ticker in stock_data_dict:
                print(f"\n  📅 Analyzing {ticker}...")
                seasonal_result = self.seasonal_analyzer.analyze(stock_data_dict[ticker])
                if seasonal_result:
                    seasonal_results[ticker] = seasonal_result

                    # Display results
                    print(f"    🌟 Seasonal Bias Score: {seasonal_result.bias_score:.2f}")
                    print(f"    📈 Best Months: {', '.join(seasonal_result.best_months)}")
                    print(f"    📉 Worst Months: {', '.join(seasonal_result.worst_months)}")
                    print(f"    💡 Pattern: {seasonal_result.seasonal_summary}")
                    print(f"    🎯 Recommendation: {seasonal_result.recommendation}")
                else:
                    print(f"    ⚠️ Insufficient data for seasonal analysis (need >1 year)")

        if not seasonal_results:
            print("\n❌ No seasonal patterns detected. Need more historical data.")
            return

        # Step 4: Generate Detailed Seasonal Report
        print("\n📊 === DETAILED SEASONAL REPORT ===")

        current_month = calendar.month_name[datetime.now().month]
        print(f"📅 Current Month: {current_month}")

        for ticker, seasonal_data in seasonal_results.items():
            print(f"\n🎯 {ticker} SEASONAL ANALYSIS:")
            print(f"   Bias Score: {seasonal_data.bias_score:.2f} "
                  f"({'Strong' if seasonal_data.bias_score > 0.5 else 'Moderate' if seasonal_data.bias_score > 0.2 else 'Weak'} seasonality)")

            # Monthly breakdown
            print(f"   📈 Top 3 Months:")
            for i, month in enumerate(seasonal_data.best_months, 1):
                stats = seasonal_data.monthly_stats.get(month, {})
                avg_return = stats.get('avg_return', 0) * 100
                win_rate = stats.get('win_rate', 0)
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                print(f"      {emoji} {month}: {avg_return:+.2f}% avg return, {win_rate:.0f}% win rate")

            print(f"   📉 Bottom 3 Months:")
            for i, month in enumerate(seasonal_data.worst_months, 1):
                stats = seasonal_data.monthly_stats.get(month, {})
                avg_return = stats.get('avg_return', 0) * 100
                win_rate = stats.get('win_rate', 0)
                print(f"      📊 {month}: {avg_return:+.2f}% avg return, {win_rate:.0f}% win rate")

            # Holiday effects
            print(f"   🎉 Notable Holiday Effects:")
            significant_holidays = {name: effect for name, effect in seasonal_data.holiday_effects.items()
                                  if abs(effect['avg_total_effect']) > 0.005 and effect['occurrences'] > 0}

            if significant_holidays:
                for holiday, effect in list(significant_holidays.items())[:5]:  # Top 5
                    total_effect = effect['avg_total_effect'] * 100
                    consistency = effect['consistency']
                    emoji = "🎆" if total_effect > 0 else "📉"
                    print(f"      {emoji} {holiday}: {total_effect:+.2f}% avg effect, {consistency:.0f}% positive rate")
            else:
                print(f"      ➡️ No significant holiday effects detected")

            # Current month context
            if current_month in seasonal_data.best_months:
                print(f"   🌟 CURRENT TIMING: FAVORABLE - {current_month} is a strong month")
            elif current_month in seasonal_data.worst_months:
                print(f"   ⚠️ CURRENT TIMING: UNFAVORABLE - {current_month} is typically weak")
            else:
                print(f"   ➡️ CURRENT TIMING: NEUTRAL - {current_month} shows average performance")

        print("\n✅ Seasonal analysis complete!")
        print(f"📁 Data files: {self.downloader.data_dir}/")

    def _generate_summary_report(self, tickers, correlation_results, volatility_results,
                               trend_results, event_results, unusual_movements,
                               options_results=None, portfolio_advice=None, seasonal_results=None, deep_results=None):
        """Generate a comprehensive text summary of all analyses."""

        print("\n" + "="*80)
        print("📊 MARKET ANALYSIS SUMMARY REPORT")
        print("="*80)

        # Enhanced Ticker Summary with Recommendations and Accuracy
        print(f"\n🎯 ANALYZED TICKERS WITH RECOMMENDATIONS:")
        self._display_enhanced_ticker_summary(tickers, portfolio_advice, deep_results)

        print(f"\n📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Trend Analysis Summary
        if trend_results:
            print(f"\n📈 TREND ANALYSIS SUMMARY:")
            for ticker, trend_data in trend_results.items():
                momentum = "🚀" if trend_data['recent_momentum_pct'] > 5 else \
                          "📉" if trend_data['recent_momentum_pct'] < -5 else "➡️"
                print(f"  {momentum} {ticker}: {trend_data['current_trend']} trend, "
                      f"{trend_data['recent_momentum_pct']:.1f}% momentum, "
                      f"strength: {trend_data['trend_strength']:.3f}")

                if trend_data['sma_crossover'] != 'None':
                    print(f"      🔄 {trend_data['sma_crossover']} detected!")

        # Correlation Summary
        if correlation_results and correlation_results.get('pattern_summary'):
            pattern_summary = correlation_results['pattern_summary']

            print(f"\n🔗 CORRELATION PATTERNS:")

            if pattern_summary['highly_correlated_pairs']:
                print("  📈 Highly Correlated Pairs (>0.7):")
                for pair_data in pattern_summary['highly_correlated_pairs'][:5]:
                    print(f"      {pair_data['pair']}: {pair_data['correlation']:.3f} "
                          f"(stability: {pair_data['stability']:.3f})")

            if pattern_summary['negatively_correlated_pairs']:
                print("  📉 Negatively Correlated Pairs (<-0.5):")
                for pair_data in pattern_summary['negatively_correlated_pairs'][:3]:
                    print(f"      {pair_data['pair']}: {pair_data['correlation']:.3f}")

            if pattern_summary['strong_leading_indicators']:
                print("  🎯 Strong Leading Indicators:")
                for indicator in pattern_summary['strong_leading_indicators'][:3]:
                    print(f"      {indicator['pair']}: {indicator['lag_days']} day lag, "
                          f"correlation: {indicator['correlation']:.3f}")

        # Volatility Summary
        if volatility_results:
            print(f"\n🌊 VOLATILITY ANALYSIS:")
            for ticker, vol_data in volatility_results.items():
                clustering_score = vol_data['volatility_clustering_score']
                clustering_desc = "High" if clustering_score > 0.3 else \
                                "Moderate" if clustering_score > 0.1 else "Low"
                print(f"  📊 {ticker}: Avg volatility {vol_data['avg_volatility']:.1f}%, "
                      f"clustering: {clustering_desc} ({clustering_score:.3f})")

        # Event Impact Summary
        if event_results and unusual_movements:
            event_summary = self.event_correlator.generate_event_summary(event_results, unusual_movements)

            print(f"\n📰 EVENT IMPACT ANALYSIS:")

            if event_summary['most_impactful_events']:
                print("  🚨 Most Impactful Events:")
                for event in event_summary['most_impactful_events'][:3]:
                    print(f"      {event['event_date']}: {event['event'][:50]}... "
                          f"(avg impact: {event['avg_impact']:.1f}%)")

            if event_summary['unexplained_movements']:
                print("  ❓ Unexplained Large Movements:")
                for movement in event_summary['unexplained_movements'][:3]:
                    print(f"      {movement['ticker']} on {movement['date']}: "
                          f"{movement['return_pct']:.1f}% ({movement['magnitude']})")

        # Enhanced Options & Risk Analysis Summary
        if options_results:
            print(f"\n⚖️ COMPREHENSIVE RISK ANALYSIS:")
            for ticker, risk_data in options_results.items():
                risk_level = risk_data['risk_assessment']

                # Get comprehensive risk data
                comprehensive_risk = risk_data.get('comprehensive_risk', {})
                var_95 = comprehensive_risk.get('var_95_daily', 'N/A')
                cvar_95 = comprehensive_risk.get('cvar_95_daily', 'N/A')
                sharpe = comprehensive_risk.get('sharpe_ratio', 'N/A')
                sortino = comprehensive_risk.get('sortino_ratio', 'N/A')

                risk_emoji = "🔴" if "High" in risk_level else \
                           "🟡" if "Moderate" in risk_level else "🟢"

                print(f"  {risk_emoji} {ticker}: {risk_level}")

                # Enhanced risk metrics display
                if var_95 != 'N/A' and cvar_95 != 'N/A':
                    print(f"      📊 VaR (95%): {var_95} | CVaR (95%): {cvar_95}")

                if sharpe != 'N/A' and sortino != 'N/A':
                    sharpe_emoji = "🌟" if sharpe > 1.0 else "📊" if sharpe > 0.5 else "❌"
                    print(f"      {sharpe_emoji} Sharpe: {sharpe} | Sortino: {sortino}")

                # Model comparison insights
                model_comparison = comprehensive_risk.get('model_comparison', {})
                merton_premium = model_comparison.get('merton_premium_pct', 0)
                heston_premium = model_comparison.get('heston_premium_pct', 0)

                if abs(merton_premium) > 2 or abs(heston_premium) > 2:
                    print(f"      ⚡ Jump risk premium: {merton_premium:.1f}% | Vol clustering: {heston_premium:.1f}%")

                # Show key risk interpretation (first insight)
                risk_interpretation = comprehensive_risk.get('risk_interpretation', [])
                if risk_interpretation:
                    print(f"      💡 {risk_interpretation[0]}")

                # Traditional expected moves for context
                if 'risk_metrics' in risk_data:
                    for timeframe in ['30d', '90d']:
                        if timeframe in risk_data['risk_metrics']:
                            expected_move = risk_data['risk_metrics'][timeframe]['expected_move']
                            print(f"      � {timeframe} expected move: ±{expected_move:.1%}")

                print()  # Add spacing between tickers

        # Investment Suggestions Summary
        if portfolio_advice:
            print(f"\n💰 INVESTMENT RECOMMENDATIONS:")
            summary = portfolio_advice['portfolio_summary']

            print(f"  📊 Portfolio Overview:")
            print(f"      🟢 BUY recommendations: {summary['buy_recommendations']}")
            print(f"      🔴 SELL recommendations: {summary['sell_recommendations']}")
            print(f"      🟡 HOLD recommendations: {summary['hold_recommendations']}")
            print(f"      ⚠️ High-risk positions: {summary['high_risk_positions']}")
            print(f"      📈 Portfolio risk level: {portfolio_advice['portfolio_risk']}")
            print(f"      🎯 Diversification: {portfolio_advice['diversification_note']}")

            # Highlight top recommendations
            buy_suggestions = [ticker for ticker, suggestion in portfolio_advice['individual_suggestions'].items()
                             if suggestion['suggestion'] == 'BUY' and suggestion['confidence'] in ['HIGH', 'MEDIUM']]

            sell_suggestions = [ticker for ticker, suggestion in portfolio_advice['individual_suggestions'].items()
                              if suggestion['suggestion'] == 'SELL' and suggestion['confidence'] in ['HIGH', 'MEDIUM']]

            if buy_suggestions:
                print(f"  🎯 Strong BUY candidates: {', '.join(buy_suggestions)}")

            if sell_suggestions:
                print(f"  ⚠️ Consider SELLING: {', '.join(sell_suggestions)}")

        # Seasonal Analysis Summary
        if seasonal_results:
            print(f"\n🗓️ SEASONAL PATTERNS:")
            for ticker, seasonal_data in seasonal_results.items():
                seasonal_emoji = "🌟" if "FAVORABLE" in seasonal_data['recommendation'] else \
                               "⚠️" if "UNFAVORABLE" in seasonal_data['recommendation'] else "🔄"

                bias_desc = "Strong" if seasonal_data['bias_score'] > 0.5 else \
                           "Moderate" if seasonal_data['bias_score'] > 0.2 else "Weak"

                print(f"  {seasonal_emoji} {ticker}: {bias_desc} seasonal bias "
                      f"(Score: {seasonal_data['bias_score']:.2f})")
                print(f"      📈 Strong months: {', '.join(seasonal_data['best_months'])}")
                print(f"      📉 Weak months: {', '.join(seasonal_data['worst_months'])}")
                print(f"      💡 Pattern: {seasonal_data['seasonal_summary']}")

                # Current month context
                current_month = calendar.month_name[datetime.now().month]
                if current_month in seasonal_data['best_months']:
                    print(f"      🎯 Current timing: FAVORABLE ({current_month})")
                elif current_month in seasonal_data['worst_months']:
                    print(f"      ⏰ Current timing: UNFAVORABLE ({current_month})")
                else:
                    print(f"      ➡️ Current timing: NEUTRAL ({current_month})")

        # Deep Analysis Summary
        if deep_results:
            print(f"\n🔁 BACKTESTING ACCURACY:")

            # Create table header
            print("┌─────────────┬─────────────┬─────────────┬─────────────┬───────────────┐")
            print("│ Ticker      │ Precision   │ Price Acc   │ Direction   │ Chunks Eval   │")
            print("├─────────────┼─────────────┼─────────────┼─────────────┼───────────────┤")

            overall_precision = []
            for ticker, deep_data in deep_results.items():
                summary = deep_data.get('summary', {})
                precision = summary.get('coefficient_of_precision', 0)
                overall_precision.append(precision)
                chunks_count = summary.get('chunks_evaluated', 0)
                avg_price_acc = summary.get('avg_price_accuracy', 0)
                avg_dir_acc = summary.get('avg_direction_accuracy', 0)

                # Format with emojis based on accuracy
                precision_emoji = "🎯" if precision > 0.7 else "📊" if precision > 0.5 else "📉"

                # Format table fields
                ticker_display = f"{precision_emoji} {ticker}"[:11]
                precision_display = f"{precision:.1%}"[:11]
                price_display = f"{avg_price_acc:.1%}"[:11]
                direction_display = f"{avg_dir_acc:.1%}"[:11]
                chunks_display = f"{chunks_count}"[:13]

                print(f"│ {ticker_display:11} │ {precision_display:11} │ {price_display:11} │ {direction_display:11} │ {chunks_display:13} │")

            print("└─────────────┴─────────────┴─────────────┴─────────────┴───────────────┘")

            if overall_precision:
                avg_precision = sum(overall_precision) / len(overall_precision)
                confidence_emoji = "✅" if avg_precision > 0.7 else "⚠️" if avg_precision > 0.5 else "🚨"
                confidence_desc = "High" if avg_precision > 0.7 else "Moderate" if avg_precision > 0.5 else "Low"

                print(f"\n  📊 Portfolio Average Precision: {confidence_emoji} {avg_precision:.1%} ({confidence_desc} confidence)")

                if avg_precision > 0.7:
                    print(f"      ✅ High confidence in analysis accuracy - Recommendations are reliable")
                elif avg_precision > 0.5:
                    print(f"      ⚠️ Moderate confidence - Consider additional factors before investing")
                else:
                    print(f"      🚨 Low confidence - Use caution with recommendations, seek more data")

        print("\n" + "="*80)
        print("💡 INVESTMENT INSIGHTS:")

        # Generate actionable insights
        insights = []

        if trend_results:
            bullish_stocks = [ticker for ticker, data in trend_results.items()
                            if data['current_trend'] == 'Bullish' and data['recent_momentum_pct'] > 0]
            if bullish_stocks:
                insights.append(f"🚀 Strong bullish momentum: {', '.join(bullish_stocks)}")

            crossover_stocks = [ticker for ticker, data in trend_results.items()
                              if data['sma_crossover'] == 'Golden Cross']
            if crossover_stocks:
                insights.append(f"🔄 Recent golden crosses: {', '.join(crossover_stocks)}")

        if correlation_results and correlation_results.get('pattern_summary'):
            stable_pairs = correlation_results['pattern_summary']['stable_relationships']
            if stable_pairs:
                insights.append(f"🎯 Most stable correlation: {stable_pairs[0]['pair']} "
                              f"({stable_pairs[0]['correlation']:.3f})")

        # Enhanced options-based insights
        if options_results:
            high_vol_stocks = [ticker for ticker, data in options_results.items()
                             if "High" in data['risk_assessment']]
            if high_vol_stocks:
                insights.append(f"⚠️ High volatility (options opportunity): {', '.join(high_vol_stocks)}")

            low_vol_stocks = [ticker for ticker, data in options_results.items()
                            if "Low" in data['risk_assessment']]
            if low_vol_stocks:
                insights.append(f"💎 Low volatility (stable): {', '.join(low_vol_stocks)}")

            # Add VaR-based insights
            high_risk_var = []
            excellent_sharpe = []
            jump_risk_stocks = []

            for ticker, data in options_results.items():
                comprehensive_risk = data.get('comprehensive_risk', {})

                # Check VaR levels
                var_95 = comprehensive_risk.get('var_95_daily', '0%')
                if var_95 != 'N/A' and var_95:
                    var_pct = float(var_95.rstrip('%'))
                    if var_pct > 5:
                        high_risk_var.append(ticker)

                # Check Sharpe ratios
                sharpe = comprehensive_risk.get('sharpe_ratio', 0)
                if sharpe != 'N/A' and sharpe > 1.5:
                    excellent_sharpe.append(ticker)

                # Check jump risk
                model_comparison = comprehensive_risk.get('model_comparison', {})
                merton_premium = model_comparison.get('merton_premium_pct', 0)
                if abs(merton_premium) > 5:
                    jump_risk_stocks.append(ticker)

            if high_risk_var:
                insights.append(f"🚨 High daily risk (VaR >5%): {', '.join(high_risk_var)}")
            if excellent_sharpe:
                insights.append(f"🌟 Excellent risk-adjusted returns: {', '.join(excellent_sharpe)}")
            if jump_risk_stocks:
                insights.append(f"⚡ Significant jump/crash risk: {', '.join(jump_risk_stocks)}")

        # Add investment advisor insights
        if portfolio_advice:
            summary = portfolio_advice['portfolio_summary']
            if summary['buy_recommendations'] > summary['sell_recommendations']:
                insights.append("📈 Overall market sentiment: BULLISH based on analysis")
            elif summary['sell_recommendations'] > summary['buy_recommendations']:
                insights.append("📉 Overall market sentiment: BEARISH based on analysis")
            else:
                insights.append("⚖️ Mixed market signals - exercise caution")

        # Add seasonal insights
        if seasonal_results:
            current_month = calendar.month_name[datetime.now().month]
            favorable_seasonal = [ticker for ticker, data in seasonal_results.items()
                                 if current_month in data['best_months']]
            unfavorable_seasonal = [ticker for ticker, data in seasonal_results.items()
                                   if current_month in data['worst_months']]

            if favorable_seasonal:
                insights.append(f"🌟 Seasonal tailwinds this month: {', '.join(favorable_seasonal)}")
            if unfavorable_seasonal:
                insights.append(f"⚠️ Seasonal headwinds this month: {', '.join(unfavorable_seasonal)}")

            # High seasonal bias stocks
            strong_seasonal = [ticker for ticker, data in seasonal_results.items()
                             if data['bias_score'] > 0.5]
            if strong_seasonal:
                insights.append(f"🗓️ Strong seasonal patterns: {', '.join(strong_seasonal)}")

        # Add deep analysis insights
        if deep_results:
            high_precision_stocks = [ticker for ticker, data in deep_results.items()
                                   if data.get('summary', {}).get('coefficient_of_precision', 0) > 0.7]
            low_precision_stocks = [ticker for ticker, data in deep_results.items()
                                  if data.get('summary', {}).get('coefficient_of_precision', 0) < 0.5]

            if high_precision_stocks:
                insights.append(f"🎯 High prediction accuracy: {', '.join(high_precision_stocks)} "
                              f"(reliable analysis)")
            if low_precision_stocks:
                insights.append(f"⚠️ Low prediction accuracy: {', '.join(low_precision_stocks)} "
                              f"(use caution)")

            # Overall precision insight
            overall_precision = [data.get('summary', {}).get('coefficient_of_precision', 0)
                               for data in deep_results.values()]
            if overall_precision:
                avg_precision = sum(overall_precision) / len(overall_precision)
                if avg_precision > 0.7:
                    insights.append("✅ Portfolio analysis shows high accuracy - confident recommendations")
                elif avg_precision < 0.5:
                    insights.append("🚨 Portfolio analysis shows low accuracy - proceed with caution")

        if insights:
            for insight in insights:
                print(f"  {insight}")
        else:
            print("  📊 Mixed signals - consider waiting for clearer trends")

        # Add highlighted opportunities and risks
        if portfolio_advice or deep_results:
            self._display_highlighted_opportunities(portfolio_advice, deep_results)

        print("="*80)

    def _display_enhanced_ticker_summary(self, tickers, portfolio_advice=None, deep_results=None):
        """Display enhanced ticker summary with recommendations and accuracy highlighting."""

        # Create a comprehensive summary for each ticker
        ticker_summaries = {}

        for ticker in tickers:
            summary = {
                'recommendation': 'HOLD',
                'confidence': 'UNKNOWN',
                'precision': None,
                'risk_level': 'UNKNOWN'
            }

            # Extract recommendation from portfolio advice
            if portfolio_advice and 'individual_suggestions' in portfolio_advice:
                suggestion = portfolio_advice['individual_suggestions'].get(ticker, {})
                summary['recommendation'] = suggestion.get('suggestion', 'HOLD')
                summary['confidence'] = suggestion.get('confidence', 'UNKNOWN')
                summary['risk_level'] = suggestion.get('risk_level', 'UNKNOWN')

            # Extract precision from deep results
            if deep_results and ticker in deep_results:
                deep_data = deep_results[ticker]
                summary_data = deep_data.get('summary', {})
                summary['precision'] = summary_data.get('coefficient_of_precision', None)

            ticker_summaries[ticker] = summary

        # Display table header
        print("┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┐")
        print("│ Ticker      │ Recommend.  │ Confidence  │ Risk Level  │ Accuracy        │")
        print("├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────┤")

        # Display each ticker with appropriate highlighting
        for ticker, summary in ticker_summaries.items():
            # Get recommendation emoji and formatting
            rec = summary['recommendation']
            confidence = summary['confidence']
            risk = summary['risk_level']
            precision = summary['precision']

            # Choose emoji based on recommendation and precision
            if rec == 'BUY':
                if precision and precision > 0.7:
                    emoji = "🟢💎"  # High confidence buy
                elif precision and precision > 0.5:
                    emoji = "🟢📊"  # Moderate confidence buy
                elif precision and precision < 0.5:
                    emoji = "🟡⚠️ "  # Low confidence buy
                else:
                    emoji = "🟢  "  # Buy without precision data
            elif rec == 'SELL':
                if precision and precision > 0.7:
                    emoji = "🔴💎"  # High confidence sell
                elif precision and precision > 0.5:
                    emoji = "🔴📊"  # Moderate confidence sell
                elif precision and precision < 0.5:
                    emoji = "🟡⚠️ "  # Low confidence sell
                else:
                    emoji = "🔴  "  # Sell without precision data
            else:  # HOLD
                if precision and precision > 0.7:
                    emoji = "🟡💎"  # High confidence hold
                elif precision and precision > 0.5:
                    emoji = "🟡📊"  # Moderate confidence hold
                elif precision and precision < 0.5:
                    emoji = "⚪⚠️ "  # Low confidence hold
                else:
                    emoji = "🟡  "  # Hold without precision data

            # Format precision display
            if precision is not None:
                precision_str = f"{precision:.1%}"
                if precision > 0.7:
                    precision_display = f"🎯 {precision_str}"
                elif precision > 0.5:
                    precision_display = f"📊 {precision_str}"
                else:
                    precision_display = f"⚠️  {precision_str}"
            else:
                precision_display = "N/A"

            # Format fields to fit table
            ticker_display = f"{emoji} {ticker}"[:11]
            rec_display = rec[:11]
            conf_display = confidence[:11]
            risk_display = risk[:11]
            precision_display = precision_display[:15]

            print(f"│ {ticker_display:11} │ {rec_display:11} │ {conf_display:11} │ {risk_display:11} │ {precision_display:15} │")

        print("└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┘")

        # Legend
        print("\n📋 LEGEND:")
        print("   🟢💎 High-confidence BUY (>70% accuracy)    🔴💎 High-confidence SELL (>70% accuracy)")
        print("   🟢📊 Moderate BUY (50-70% accuracy)        🔴📊 Moderate SELL (50-70% accuracy)")
        print("   🟡💎 High-confidence HOLD (>70% accuracy)   ⚠️  Low accuracy (<50%) - Use caution")
        print("   🟡📊 Moderate HOLD (50-70% accuracy)       🎯  High prediction accuracy")

    def _display_highlighted_opportunities(self, portfolio_advice=None, deep_results=None):
        """Display highlighted investment opportunities and risks based on combined analysis."""

        best_opportunities = []
        high_risks = []
        moderate_opportunities = []

        # Analyze each ticker's combined score
        if portfolio_advice and 'individual_suggestions' in portfolio_advice:
            for ticker, suggestion in portfolio_advice['individual_suggestions'].items():
                rec = suggestion.get('suggestion', 'HOLD')
                confidence = suggestion.get('confidence', 'UNKNOWN')

                # Get precision if available
                precision = None
                if deep_results and ticker in deep_results:
                    deep_data = deep_results[ticker]
                    summary_data = deep_data.get('summary', {})
                    precision = summary_data.get('coefficient_of_precision', None)

                # Categorize based on recommendation, confidence, and precision
                if rec == 'BUY':
                    if confidence in ['HIGH', 'MEDIUM'] and precision and precision > 0.7:
                        best_opportunities.append((ticker, 'HIGH-CONFIDENCE BUY', precision))
                    elif confidence in ['HIGH', 'MEDIUM'] and (not precision or precision > 0.5):
                        moderate_opportunities.append((ticker, 'MODERATE BUY', precision))
                    elif precision and precision < 0.5:
                        high_risks.append((ticker, 'LOW-ACCURACY BUY', precision))

                elif rec == 'SELL':
                    if confidence in ['HIGH', 'MEDIUM'] and precision and precision > 0.7:
                        high_risks.append((ticker, 'HIGH-CONFIDENCE SELL', precision))
                    elif precision and precision < 0.5:
                        high_risks.append((ticker, 'LOW-ACCURACY SELL', precision))

        # Display results
        if best_opportunities or moderate_opportunities or high_risks:
            print(f"\n🎯 KEY HIGHLIGHTS:")

            if best_opportunities:
                print(f"\n  💎 TOP OPPORTUNITIES (High confidence + High accuracy):")
                for ticker, reason, precision in best_opportunities:
                    precision_str = f" ({precision:.1%} accuracy)" if precision else ""
                    print(f"     🟢💎 {ticker}: {reason}{precision_str}")

            if moderate_opportunities:
                print(f"\n  📊 MODERATE OPPORTUNITIES:")
                for ticker, reason, precision in moderate_opportunities:
                    precision_str = f" ({precision:.1%} accuracy)" if precision else ""
                    print(f"     🟢📊 {ticker}: {reason}{precision_str}")

            if high_risks:
                print(f"\n  ⚠️  HIGH ATTENTION REQUIRED:")
                for ticker, reason, precision in high_risks:
                    precision_str = f" ({precision:.1%} accuracy)" if precision else ""
                    print(f"     🔴⚠️  {ticker}: {reason}{precision_str}")

            print(f"\n  💡 Investment Strategy:")
            if best_opportunities:
                print(f"     ✅ Prioritize: {', '.join([t[0] for t in best_opportunities])}")
            if high_risks:
                print(f"     ⚠️  Exercise caution: {', '.join([t[0] for t in high_risks])}")
            if not best_opportunities and not high_risks:
                print(f"     📊 Consider market timing and additional research")


# Legacy class for backward compatibility
class StockAnalysis(AdvancedStockAnalysis):
    def quick_analysis(self, tickers, period="1y", download=True, visualize=True):
        """Legacy quick analysis method."""
        print(f"=== Quick Stock Analysis ===")
        print("🚀 ClariFi: Clarify your Finances")
        print("=======================")
        print(f"Tickers: {', '.join(tickers)}")
        print(f"Period: {period}")
        print()

        # Download data if requested
        if download:
            print("📊 Downloading stock data...")
            results = self.downloader.download_multiple_stocks(
                tickers, None, None, period
            )

            if not results:
                print("❌ No data downloaded. Exiting.")
                return

            print("✅ Data download completed!")
            print()

        # Create visualizations if requested
        if visualize:
            print("📈 Creating visualizations...")

            # Individual charts for each stock
            for ticker in tickers:
                print(f"  Creating chart for {ticker}...")
                self.visualizer.plot_single_stock(ticker, save=True, show=False)

            # Comparison chart if multiple stocks
            if len(tickers) > 1:
                print(f"  Creating comparison chart...")
                self.visualizer.plot_comparison(tickers, save=True, show=False)

                print(f"  Creating correlation matrix...")
                self.visualizer.create_correlation_matrix(tickers, save=True, show=False)

            print("✅ Visualizations completed!")
            print()

        print("🎉 Analysis completed!")
        print(f"📁 Data files saved in: {self.downloader.data_dir}/")
        print(f"📊 Charts saved in: {self.visualizer.output_dir}/")

    def show_stock_info(self, tickers):
        """Display information about stocks."""
        print("=== Stock Information ===")
        for ticker in tickers:
            info = self.downloader.get_stock_info(ticker)
            if info:
                print(f"\n{ticker.upper()} - {info['longName']}")
                print(f"  Sector: {info['sector']}")
                print(f"  Industry: {info['industry']}")
                print(f"  Market Cap: {info['marketCap']}")
                print(f"  Currency: {info['currency']}")
            else:
                print(f"\n{ticker.upper()} - Unable to fetch information")

    def list_available_data(self):
        """List all available data files."""
        files = self.visualizer.find_stock_files()
        if files:
            print("=== Available Data Files ===")
            for file in sorted(files):
                ticker = self.visualizer.extract_ticker_from_filename(file)
                file_size = os.path.getsize(file) / 1024  # KB
                mod_time = datetime.fromtimestamp(os.path.getmtime(file))
                print(f"  {ticker.upper()}: {os.path.basename(file)} ({file_size:.1f} KB, {mod_time.strftime('%Y-%m-%d %H:%M')})")
        else:
            print("No data files found.")


def main():
    parser = argparse.ArgumentParser(
        description='🚀 ClariFi: Clarify your Finances - Advanced Market Intelligence & Pattern Analysis Tool 🚀',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🎯 ADVANCED MARKET ANALYSIS EXAMPLES:

📊 QUICK ANALYSIS (Basic):
  ./run.sh quick PLTR QBTS
  ./run.sh quick AAPL MSFT --period 6mo

🔬 COMPREHENSIVE ANALYSIS (Advanced):
  ./run.sh analyze PLTR QBTS AAPL --period 1y
  ./run.sh analyze "SAAB B" NANEXA --period 6mo --no-events

🔁 DEEP BACKTESTING ANALYSIS:
  ./run.sh analyze AAPL MSFT --period 5y --include-deep
  ./run.sh analyze PLTR --period 3y --include-deep --deep-chunk-months 6

📈 PATTERN ANALYSIS:
  ./run.sh patterns AAPL MSFT GOOGL --period 2y
  ./run.sh correlations PLTR QBTS --window 30

📰 EVENT CORRELATION:
  ./run.sh events PLTR QBTS --period 1y
  ./run.sh events AAPL --lookback 7 --lookahead 7

🎨 ADVANCED VISUALIZATIONS:
  ./run.sh visualize PLTR --support-resistance
  ./run.sh volatility AAPL MSFT --clustering

📋 DATA MANAGEMENT:
  ./run.sh download PLTR QBTS --period 6mo
  ./run.sh info PLTR QBTS "SAAB B"
  ./run.sh list

📡 LIVE MONITORING:
  ./run.sh live AAPL MSFT TSLA
  ./run.sh live PLTR QBTS --interval 10
  ./run.sh live AAPL --no-graphs --interval 3

📊 MARKET SCREENING:
  ./run.sh screen gainers
  ./run.sh screen losers --limit 10
  ./run.sh screen actives --limit 30
  ./run.sh screen new

🎯 MARKET INTELLIGENCE FEATURES:
  ✅ Correlation pattern detection
  ✅ Leading indicator identification
  ✅ Volatility clustering analysis
  ✅ Support/resistance level detection
  ✅ Event impact correlation
  ✅ Trend strength analysis
  ✅ Unusual movement detection
  ✅ Black-Scholes options analysis
  ✅ Risk assessment and prediction
  ✅ Investment suggestion engine
  ✅ Portfolio-level recommendations
  ✅ Deep backtesting & accuracy analysis
  ✅ Real-time live monitoring with terminal graphs
  ✅ Market screening for gainers, losers, and new listings

⚖️ OPTIONS & RISK ANALYSIS:
  ./run.sh analyze AAPL MSFT --period 1y  # Full analysis with options
  ./run.sh analyze PLTR --no-options      # Skip options analysis

💰 INVESTMENT SUGGESTIONS:
  ./run.sh analyze AAPL TSLA MSFT         # Get BUY/SELL/HOLD advice
  ./run.sh analyze PLTR --no-investment-advice  # Skip suggestions

� PORTFOLIO MANAGEMENT:
    ./run.sh portfolio create --name MyPortfolio --description "Core holdings"
    ./run.sh portfolio list
    ./run.sh portfolio add <portfolio_id> AAPL --quantity 10 --avg-cost 150
    ./run.sh portfolio update-ticker <portfolio_id> AAPL --quantity 15 --avg-cost 175
    ./run.sh portfolio tickers <portfolio_id>
    ./run.sh portfolio analyze <portfolio_id> --period 6mo --summary-only
    ./run.sh portfolio remove <portfolio_id> AAPL
    ./run.sh portfolio history --portfolio-id <portfolio_id> --limit 5
    ./run.sh portfolio accuracy --portfolio-id <portfolio_id>

�💡 TIP: Use quotes for tickers with spaces: "SAAB B"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Analysis Commands')

    # Legacy quick analysis
    quick_parser = subparsers.add_parser('quick', help='🚀 Quick basic analysis (legacy)')
    quick_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    quick_parser.add_argument('--period', '-p', default='1y', help='Time period (default: 1y)')
    quick_parser.add_argument('--no-download', action='store_true', help='Skip downloading')
    quick_parser.add_argument('--no-visualize', action='store_true', help='Skip visualization')

    # NEW: Comprehensive analysis
    analyze_parser = subparsers.add_parser('analyze', help='🔬 Comprehensive market analysis')
    analyze_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    analyze_parser.add_argument('--period', '-p', default='1y', help='Time period (default: 1y)')
    analyze_parser.add_argument('--no-download', action='store_true', help='Skip downloading fresh data')
    analyze_parser.add_argument('--no-patterns', action='store_true', help='Skip pattern analysis')
    analyze_parser.add_argument('--no-events', action='store_true', help='Skip event correlation')
    analyze_parser.add_argument('--no-advanced-viz', action='store_true', help='Skip advanced visualizations')
    analyze_parser.add_argument('--no-options', action='store_true', help='Skip Black-Scholes options analysis')
    analyze_parser.add_argument('--no-investment-advice', action='store_true', help='Skip investment suggestions')
    analyze_parser.add_argument('--no-seasonal', action='store_true', help='Skip seasonal analysis')
    analyze_parser.add_argument('--include-deep', action='store_true', help='Include deep backtesting analysis')
    analyze_parser.add_argument('--deep-chunk-months', type=int, default=3, help='Chunk size in months for deep analysis (default: 3)')

    # Seasonal analysis
    seasonal_parser = subparsers.add_parser('seasonal', help='🗓️ Seasonal & holiday analysis')
    seasonal_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    seasonal_parser.add_argument('--period', '-p', default='5y', help='Time period (default: 5y for better patterns)')
    seasonal_parser.add_argument('--no-download', action='store_true', help='Skip downloading fresh data')

    # Pattern analysis
    patterns_parser = subparsers.add_parser('patterns', help='🔍 Advanced pattern analysis')
    patterns_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    patterns_parser.add_argument('--period', '-p', default='1y', help='Time period')
    patterns_parser.add_argument('--window', '-w', type=int, default=30, help='Rolling window size')

    # Correlation analysis
    corr_parser = subparsers.add_parser('correlations', help='📊 Correlation analysis')
    corr_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols (min 2)')
    corr_parser.add_argument('--period', '-p', default='1y', help='Time period')
    corr_parser.add_argument('--window', '-w', type=int, default=30, help='Rolling window size')

    # Event correlation
    events_parser = subparsers.add_parser('events', help='📰 Event correlation analysis')
    events_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    events_parser.add_argument('--period', '-p', default='1y', help='Time period')
    events_parser.add_argument('--lookback', type=int, default=5, help='Days before event')
    events_parser.add_argument('--lookahead', type=int, default=5, help='Days after event')

    # Volatility analysis
    vol_parser = subparsers.add_parser('volatility', help='🌊 Volatility clustering analysis')
    vol_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    vol_parser.add_argument('--period', '-p', default='1y', help='Time period')
    vol_parser.add_argument('--window', '-w', type=int, default=20, help='Volatility window')
    vol_parser.add_argument('--clustering', action='store_true', help='Create clustering plots')

    # Download command
    download_parser = subparsers.add_parser('download', help='📥 Download stock data')
    download_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    download_parser.add_argument('--start', '-s', help='Start date (YYYY-MM-DD)')
    download_parser.add_argument('--end', '-e', help='End date (YYYY-MM-DD)')
    download_parser.add_argument('--period', '-p', help='Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)')

    # Visualize command
    viz_parser = subparsers.add_parser('visualize', help='🎨 Create visualizations')
    viz_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    viz_parser.add_argument('--single', action='store_true', help='Individual charts only')
    viz_parser.add_argument('--compare', action='store_true', help='Comparison chart')
    viz_parser.add_argument('--correlation', action='store_true', help='Correlation matrix')
    viz_parser.add_argument('--support-resistance', action='store_true', help='Support/resistance levels')
    viz_parser.add_argument('--metric', default='Close', help='Metric to plot (default: Close)')
    viz_parser.add_argument('--show', action='store_true', help='Show plots instead of saving')

    # Info command
    info_parser = subparsers.add_parser('info', help='ℹ️ Show stock information')
    info_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')

    # List command
    list_parser = subparsers.add_parser('list', help='📋 List available data files')

    # Live monitoring command
    live_parser = subparsers.add_parser('live', help='📡 Live real-time stock monitoring')
    live_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols to monitor')
    live_parser.add_argument('--interval', '-i', type=int, default=5, help='Update interval in seconds (default: 5)')
    live_parser.add_argument('--no-graphs', action='store_true', help='Disable terminal graphs')
    live_parser.add_argument('--no-summary', action='store_true', help='Disable summary table')

    # Stock screener command
    screener_parser = subparsers.add_parser('screen', help='📊 Market screening for gainers, losers, and new listings')
    screener_parser.add_argument('category', choices=['gainers', 'losers', 'actives', 'new'],
                                help='Screening category: gainers, losers, actives, or new')
    screener_parser.add_argument('--limit', '-l', type=int, default=20,
                                help='Number of results to return (default: 20)')
    screener_parser.add_argument('--export', '-e', help='Export results to CSV file')

    # Portfolio management (grouped subcommands)
    portfolio_parser = subparsers.add_parser('portfolio', help='📁 Portfolio management commands (create, list, add, update-ticker, update, sync, delete, remove, tickers, analyze)')
    port_sub = portfolio_parser.add_subparsers(dest='portfolio_cmd', help='Portfolio Commands')

    # portfolio create
    p_create = port_sub.add_parser('create', help='Create a new portfolio')
    p_create.add_argument('--name', '-n', required=True, help='Portfolio name (unique)')
    p_create.add_argument('--description', '-d', default='', help='Portfolio description')

    # portfolio list
    p_list = port_sub.add_parser('list', help='List all portfolios')

    # portfolio add ticker
    p_add = port_sub.add_parser('add', help='Add a ticker to a portfolio')
    p_add.add_argument('portfolio_id', help='Portfolio ID')
    p_add.add_argument('ticker', help='Ticker symbol')
    p_add.add_argument('--quantity', '-q', type=float, default=0.0, help='Quantity (default 0)')
    p_add.add_argument('--avg-cost', '-c', type=float, default=0.0, help='Average cost (default 0)')

    # portfolio remove ticker
    p_remove = port_sub.add_parser('remove', help='Remove a ticker from a portfolio')
    p_remove.add_argument('portfolio_id', help='Portfolio ID')
    p_remove.add_argument('ticker', help='Ticker symbol')

    # portfolio tickers
    p_tickers = port_sub.add_parser('tickers', help='List tickers in a portfolio')
    p_tickers.add_argument('portfolio_id', help='Portfolio ID')

    # portfolio update-ticker
    p_update_ticker = port_sub.add_parser('update-ticker', help='Update ticker quantity and/or average cost')
    p_update_ticker.add_argument('portfolio_id', help='Portfolio ID')
    p_update_ticker.add_argument('ticker', help='Ticker symbol')
    p_update_ticker.add_argument('--quantity', '-q', type=float, help='New quantity')
    p_update_ticker.add_argument('--avg-cost', '-c', type=float, help='New average cost')

    # portfolio update
    p_update = port_sub.add_parser('update', help='Update portfolio name and/or description')
    p_update.add_argument('portfolio_id', help='Portfolio ID')
    p_update.add_argument('--name', '-n', help='New portfolio name')
    p_update.add_argument('--description', '-d', help='New portfolio description')

    # portfolio delete
    p_delete = port_sub.add_parser('delete', help='Delete a portfolio (requires confirmation)')
    p_delete.add_argument('portfolio_id', help='Portfolio ID')
    p_delete.add_argument('--confirm-name', required=True, help='Type the exact portfolio name to confirm deletion (case sensitive)')

    # portfolio sync
    p_sync = port_sub.add_parser('sync', help='Sync portfolio by fetching latest prices for all tickers')
    p_sync.add_argument('portfolio_id', help='Portfolio ID')

    # portfolio analyze
    p_analyze = port_sub.add_parser('analyze', help='Run comprehensive analysis on all tickers in a portfolio')
    p_analyze.add_argument('portfolio_id', help='Portfolio ID')
    p_analyze.add_argument('--period', '-p', default='1y', help='Time period (default 1y)')
    p_analyze.add_argument('--no-patterns', action='store_true', help='Skip pattern analysis')
    p_analyze.add_argument('--no-events', action='store_true', help='Skip event correlation')
    p_analyze.add_argument('--no-options', action='store_true', help='Skip options analysis')
    p_analyze.add_argument('--no-seasonal', action='store_true', help='Skip seasonal analysis')
    p_analyze.add_argument('--summary-only', action='store_true', help='Print only summary recommendations')

    # portfolio history (analysis history)
    p_history = port_sub.add_parser('history', help='Show recent analysis history for a portfolio or ticker')
    p_history.add_argument('--portfolio-id', help='Portfolio ID')
    p_history.add_argument('--ticker', help='Ticker symbol')
    p_history.add_argument('--limit', '-l', type=int, default=10, help='Number of records (default 10)')

    # portfolio accuracy trends
    p_accuracy = port_sub.add_parser('accuracy', help='Show accuracy trends for predictions')
    p_accuracy.add_argument('--portfolio-id', help='Portfolio ID')
    p_accuracy.add_argument('--ticker', help='Ticker symbol')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize analysis tools
    try:
        analysis = AdvancedStockAnalysis()
        legacy_analysis = StockAnalysis()  # For backward compatibility
        # Import engine with a fallback to support running as a script (no package context)
        try:
            from clarifi_engine.engine import ClariFiEngine  # when package is recognized
        except Exception:
            # Fallback: adjust sys.path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.append(current_dir)
            try:
                from engine import ClariFiEngine  # local module import
            except ImportError as ie:
                raise ie
        engine = None  # Lazy init
    except Exception as e:
        print(f"❌ Error initializing analysis tools: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        return

    try:
        if args.command == 'quick':
            legacy_analysis.quick_analysis(
                args.tickers,
                args.period,
                download=not args.no_download,
                visualize=not args.no_visualize
            )

        elif args.command == 'analyze':
            analysis.comprehensive_analysis(
                args.tickers,
                args.period,
                download=not args.no_download,
                include_patterns=not args.no_patterns,
                include_events=not args.no_events,
                include_advanced_viz=not args.no_advanced_viz,
                include_options=not args.no_options,
                include_investment_advice=not args.no_investment_advice,
                include_seasonal=not args.no_seasonal,
                include_deep=args.include_deep,
                deep_chunk_months=args.deep_chunk_months
            )

        elif args.command == 'seasonal':
            analysis.seasonal_only(
                args.tickers,
                period=args.period,
                download=not args.no_download
            )

        elif args.command == 'patterns':
            # Load data
            stock_data_dict = {}
            for ticker in args.tickers:
                files = analysis.visualizer.find_stock_files(ticker)
                if not files:
                    print(f"❌ No data found for {ticker}. Download first with: ./run.sh download {ticker}")
                    continue
                latest_file = max(files, key=os.path.getctime)
                data = analysis.visualizer.load_stock_data(latest_file)
                if data is not None:
                    stock_data_dict[ticker] = data

            if stock_data_dict:
                print(f"🔍 PATTERN ANALYSIS: {', '.join(stock_data_dict.keys())}")
                correlation_results = analysis.pattern_analyzer.analyze_correlation_patterns(
                    stock_data_dict, window=args.window)
                trend_results = analysis.pattern_analyzer.analyze_trend_strength(stock_data_dict)

                # Create visualizations
                analysis.advanced_visualizer.plot_correlation_heatmap(correlation_results)
                analysis.advanced_visualizer.plot_rolling_correlations(correlation_results)

                print("✅ Pattern analysis completed!")

        elif args.command == 'correlations':
            if len(args.tickers) < 2:
                print("❌ Need at least 2 tickers for correlation analysis")
                return

            # Load data
            stock_data_dict = {}
            for ticker in args.tickers:
                files = analysis.visualizer.find_stock_files(ticker)
                if not files:
                    print(f"❌ No data found for {ticker}. Download first with: ./run.sh download {ticker}")
                    continue
                latest_file = max(files, key=os.path.getctime)
                data = analysis.visualizer.load_stock_data(latest_file)
                if data is not None:
                    stock_data_dict[ticker] = data

            if len(stock_data_dict) >= 2:
                print(f"📊 CORRELATION ANALYSIS: {', '.join(stock_data_dict.keys())}")
                correlation_results = analysis.pattern_analyzer.analyze_correlation_patterns(
                    stock_data_dict, window=args.window)

                # Create visualizations
                analysis.advanced_visualizer.plot_correlation_heatmap(correlation_results)
                analysis.advanced_visualizer.plot_rolling_correlations(correlation_results)

                print("✅ Correlation analysis completed!")

        elif args.command == 'events':
            # Load data
            stock_data_dict = {}
            for ticker in args.tickers:
                files = analysis.visualizer.find_stock_files(ticker)
                if not files:
                    print(f"❌ No data found for {ticker}. Download first with: ./run.sh download {ticker}")
                    continue
                latest_file = max(files, key=os.path.getctime)
                data = analysis.visualizer.load_stock_data(latest_file)
                if data is not None:
                    stock_data_dict[ticker] = data

            if stock_data_dict:
                print(f"📰 EVENT CORRELATION: {', '.join(stock_data_dict.keys())}")
                event_results = analysis.event_correlator.correlate_events_with_movements(
                    stock_data_dict, args.lookback, args.lookahead)
                unusual_movements = analysis.event_correlator.identify_unusual_movements(stock_data_dict)

                # Create visualizations
                analysis.advanced_visualizer.plot_event_impact_analysis(event_results)

                # Generate summary
                event_summary = analysis.event_correlator.generate_event_summary(event_results, unusual_movements)

                print("✅ Event correlation analysis completed!")

        elif args.command == 'volatility':
            # Load data
            stock_data_dict = {}
            for ticker in args.tickers:
                files = analysis.visualizer.find_stock_files(ticker)
                if not files:
                    print(f"❌ No data found for {ticker}. Download first with: ./run.sh download {ticker}")
                    continue
                latest_file = max(files, key=os.path.getctime)
                data = analysis.visualizer.load_stock_data(latest_file)
                if data is not None:
                    stock_data_dict[ticker] = data

            if stock_data_dict:
                print(f"🌊 VOLATILITY ANALYSIS: {', '.join(stock_data_dict.keys())}")
                volatility_results = analysis.pattern_analyzer.detect_volatility_patterns(
                    stock_data_dict, window=args.window)

                if args.clustering:
                    analysis.advanced_visualizer.plot_volatility_clustering(volatility_results)

                print("✅ Volatility analysis completed!")

        elif args.command == 'download':
            downloader = StockDownloader()
            if args.period:
                results = downloader.download_multiple_stocks(args.tickers, None, None, args.period)
            else:
                start = args.start or (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
                end = args.end or datetime.now().strftime("%Y-%m-%d")
                results = downloader.download_multiple_stocks(args.tickers, start, end)

            print("📥 Download completed:")
            for ticker, filepath in results.items():
                if filepath:
                    print(f"  ✅ {ticker}: {filepath}")

        elif args.command == 'visualize':
            visualizer = StockVisualizer()

            if args.support_resistance:
                for ticker in args.tickers:
                    files = visualizer.find_stock_files(ticker)
                    if files:
                        latest_file = max(files, key=os.path.getctime)
                        data = visualizer.load_stock_data(latest_file)
                        if data is not None:
                            sr_data = analysis.pattern_analyzer.identify_support_resistance(data, ticker)
                            analysis.advanced_visualizer.plot_support_resistance(sr_data, data)

            if args.single or (not args.compare and not args.correlation and not args.support_resistance):
                for ticker in args.tickers:
                    visualizer.plot_single_stock(ticker, save=not args.show, show=args.show)

            if args.compare and len(args.tickers) > 1:
                visualizer.plot_comparison(args.tickers, args.metric, save=not args.show, show=args.show)

            if args.correlation and len(args.tickers) > 1:
                visualizer.create_correlation_matrix(args.tickers, save=not args.show, show=args.show)

        elif args.command == 'info':
            legacy_analysis.show_stock_info(args.tickers)

        elif args.command == 'list':
            legacy_analysis.list_available_data()

        elif args.command == 'live':
            # Initialize live monitor
            monitor = LiveStockMonitor()
            monitor.update_interval = args.interval
            monitor.add_tickers(args.tickers)

            print(f"🚀 Starting live monitoring for: {', '.join(args.tickers)}")
            print(f"📊 Update interval: {args.interval} seconds")
            print(f"📈 Features: Graphs={'enabled' if not args.no_graphs else 'disabled'}, Summary={'enabled' if not args.no_summary else 'disabled'}")
            print()

            # Start monitoring
            monitor.monitor(
                show_graphs=not args.no_graphs,
                show_summary=not args.no_summary
            )

        elif args.command == 'screen':
            # Initialize stock screener
            screener = StockScreener()

            print(f"🔍 Starting market screening for: {args.category}")
            print(f"📊 Limit: {args.limit} results")
            if args.export:
                print(f"📁 Export to: {args.export}")
            print()

            # Perform screening
            screener.screen_market(args.category, args.limit)

            # TODO: Implement CSV export if requested
            if args.export:
                print(f"💾 CSV export functionality coming soon...")

        elif args.command == 'portfolio':
            # Ensure an action is provided
            if not args.portfolio_cmd:
                portfolio_parser.print_help()
                return

            # Lazy initialize engine
            if engine is None:
                engine = ClariFiEngine()

            import json
            from datetime import datetime

            def format_portfolio_table(portfolios):
                """Format portfolios as a clean table"""
                if not portfolios:
                    print("📁 No portfolios found")
                    return

                print("📁 Portfolios:")
                print("┌──────────────────────────────────────┬─────────────────┬───────────────────────────────┐")
                print("│ Portfolio ID                         │ Name            │ Description                   │")
                print("├──────────────────────────────────────┼─────────────────┼───────────────────────────────┤")
                for p in portfolios:
                    portfolio_id = p['id'][:36]  # Full UUID
                    name = p['name'][:15]
                    desc = (p.get('description', '') or '')[:29]
                    print(f"│ {portfolio_id:36} │ {name:15} │ {desc:29} │")
                print("└──────────────────────────────────────┴─────────────────┴───────────────────────────────┘")

            def format_tickers_table(tickers, portfolio_id):
                """Format tickers as a clean table"""
                if not tickers:
                    print(f"📊 No tickers in portfolio {portfolio_id[:8]}...")
                    return

                print(f"📊 Tickers in portfolio {portfolio_id[:8]}...:")
                print("┌─────────┬──────────┬─────────────┬─────────────────┐")
                print("│ Ticker  │ Quantity │ Avg Cost    │ Added Date      │")
                print("├─────────┼──────────┼─────────────┼─────────────────┤")
                for t in tickers:
                    ticker = t['ticker'][:8]
                    qty = f"{t.get('quantity', 0):.2f}"[:9]
                    cost = f"${t.get('avg_cost', 0):.2f}"[:10]
                    added = t.get('added_at', '')[:15]
                    print(f"│ {ticker:7} │ {qty:8} │ {cost:11} │ {added:15} │")
                print("└─────────┴──────────┴─────────────┴─────────────────┘")

            def print_json_minimal(data, show_json=False):
                """Print minimal JSON only when requested"""
                if show_json:
                    try:
                        print("\n🔍 Raw JSON data:")
                        print(json.dumps(data, indent=2))
                    except Exception:
                        print(data)

            cmd = args.portfolio_cmd

            if cmd == 'create':
                result = engine.create_portfolio(args.name, args.description)
                if result.get('success'):
                    portfolio_id = result['portfolio_id']
                    print(f"✅ Created portfolio '{args.name}'")
                    print(f"   ID: {portfolio_id}")
                    print(f"   Description: {args.description or '(none)'}")
                else:
                    print(f"❌ Failed to create portfolio: {result.get('error')}")

            elif cmd == 'list':
                portfolios = engine.get_portfolios()
                format_portfolio_table(portfolios)

            elif cmd == 'add':
                result = engine.add_ticker_to_portfolio(
                    args.portfolio_id, args.ticker,
                    quantity=args.quantity, avg_cost=args.avg_cost
                )
                if result.get('success'):
                    print(f"✅ Added {args.ticker.upper()} to portfolio")
                    if args.quantity > 0:
                        print(f"   Quantity: {args.quantity}")
                    if args.avg_cost > 0:
                        print(f"   Average cost: ${args.avg_cost:.2f}")
                else:
                    print(f"❌ Failed to add ticker: {result.get('error')}")

            elif cmd == 'remove':
                result = engine.remove_ticker_from_portfolio(args.portfolio_id, args.ticker)
                if result.get('success'):
                    print(f"✅ Removed {args.ticker.upper()} from portfolio")
                else:
                    print(f"❌ {result.get('message', 'Failed to remove ticker')}")

            elif cmd == 'tickers':
                tickers = engine.get_portfolio_tickers(args.portfolio_id)
                format_tickers_table(tickers, args.portfolio_id)

            elif cmd == 'update-ticker':
                # Validate that at least one field is provided
                if args.quantity is None and args.avg_cost is None:
                    print("❌ Error: At least one of --quantity or --avg-cost must be provided")
                    return

                result = engine.update_ticker_in_portfolio(
                    args.portfolio_id, args.ticker, args.quantity, args.avg_cost
                )
                if result.get('success'):
                    print(f"✅ Ticker {result.get('ticker')} updated successfully")
                    if args.quantity is not None:
                        print(f"   New quantity: {args.quantity}")
                    if args.avg_cost is not None:
                        print(f"   New average cost: ${args.avg_cost:.2f}")
                else:
                    print(f"❌ Failed to update ticker: {result.get('message')}")

            elif cmd == 'update':
                # Validate that at least one field is provided
                if not args.name and not args.description:
                    print("❌ Error: At least one of --name or --description must be provided")
                    return

                result = engine.update_portfolio(args.portfolio_id, args.name, args.description)
                if result.get('success'):
                    print(f"✅ Portfolio updated successfully")
                    if args.name:
                        print(f"   New name: {args.name}")
                    if args.description:
                        print(f"   New description: {args.description}")
                else:
                    print(f"❌ Failed to update portfolio: {result.get('message')}")

            elif cmd == 'delete':
                # Show warning and get portfolio info first
                portfolio = engine.portfolio_model.get_by_id(args.portfolio_id)
                if not portfolio:
                    print(f"❌ Portfolio not found: {args.portfolio_id}")
                    return

                tickers = engine.get_portfolio_tickers(args.portfolio_id)
                ticker_count = len(tickers)

                print(f"⚠️  WARNING: You are about to delete portfolio '{portfolio['name']}'")
                print(f"   This action is IRREVERSIBLE and will:")
                print(f"   - Delete the portfolio permanently")
                print(f"   - Remove all {ticker_count} associated tickers")
                print(f"   - Remove all analysis history")
                print()

                result = engine.delete_portfolio(args.portfolio_id, args.confirm_name)
                if result.get('success'):
                    print(f"✅ {result.get('message')}")
                    print(f"   Deleted tickers: {result.get('deleted_tickers', 0)}")
                else:
                    print(f"❌ {result.get('message')}")
                    if 'warning' in result:
                        print(f"   {result['warning']}")

            elif cmd == 'sync':
                # Show portfolio info first
                portfolio = engine.portfolio_model.get_by_id(args.portfolio_id)
                if not portfolio:
                    print(f"❌ Portfolio not found: {args.portfolio_id}")
                    return

                print(f"🔄 Syncing prices for portfolio '{portfolio['name']}'...")

                result = engine.sync_portfolio_prices(args.portfolio_id)
                if result.get('success'):
                    print(f"✅ {result.get('message')}")
                    print(f"   Portfolio: {result.get('portfolio_name')}")
                    print(f"   Total tickers: {result.get('total_tickers', 0)}")
                    print(f"   Successful syncs: {result.get('successful_syncs', 0)}")
                    print(f"   Failed syncs: {result.get('failed_syncs', 0)}")
                    print(f"   Execution time: {result.get('execution_time', 0):.2f}s")

                    # Show detailed results in a table
                    sync_results = result.get('sync_results', {})
                    if sync_results:
                        print("\n📊 Price Update Details:")
                        print("┌─────────┬─────────────┬─────────────┬─────────────┬──────────────┐")
                        print("│ Ticker  │ Status      │ New Price   │ Change $    │ Change %     │")
                        print("├─────────┼─────────────┼─────────────┼─────────────┼──────────────┤")

                        for ticker, data in sync_results.items():
                            if data.get('success'):
                                status = "✅ Updated"
                                price = f"${data.get('current_price', 0):.2f}"
                                change_dollar = f"{data.get('price_change', 0):+.2f}"
                                change_percent = f"{data.get('price_change_pct', 0):+.2f}%"
                            else:
                                status = "❌ Failed"
                                price = "N/A"
                                change_dollar = "N/A"
                                change_percent = "N/A"

                            print(f"│ {ticker:7} │ {status:11} │ {price:11} │ {change_dollar:11} │ {change_percent:12} │")

                        print("└─────────┴─────────────┴─────────────┴─────────────┴──────────────┘")
                else:
                    print(f"❌ Failed to sync portfolio: {result.get('message')}")
                    print(f"   Error: {result.get('error', 'Unknown error')}")

            elif cmd == 'analyze':
                # Fetch tickers first
                tickers = engine.get_portfolio_tickers(args.portfolio_id)
                if not tickers:
                    print(f"❌ No tickers in portfolio {args.portfolio_id[:8]}...")
                    return
                ticker_list = [t['ticker'] for t in tickers]
                print(f"🚀 Analyzing portfolio {args.portfolio_id[:8]}...")
                print(f"📊 Tickers: {', '.join(ticker_list)}")
                print(f"📅 Period: {args.period}")

                result = engine.comprehensive_analysis(
                    tickers=ticker_list,
                    portfolio_id=args.portfolio_id,
                    period=args.period,
                    include_patterns=not args.no_patterns,
                    include_events=not args.no_events,
                    include_options=not args.no_options,
                    include_seasonal=not args.no_seasonal
                )
                if result.get('success'):
                    print("\n📋 Portfolio Analysis Summary:")

                    # Check if deep analysis was included
                    has_deep_results = any('deep_analysis' in data for data in result['results'].values())

                    if has_deep_results:
                        print("┌─────────┬──────────────┬────────────┬─────────────┬─────────────────┐")
                        print("│ Ticker  │ Recomm.      │ Confidence │ Risk Level  │ Accuracy        │")
                        print("├─────────┼──────────────┼────────────┼─────────────┼─────────────────┤")
                    else:
                        print("┌─────────┬──────────────┬────────────┬─────────────┐")
                        print("│ Ticker  │ Recomm.      │ Confidence │ Risk Level  │")
                        print("├─────────┼──────────────┼────────────┼─────────────┤")

                    for tk, data in result['results'].items():
                        rec = data.get('overall_recommendation', 'N/A')
                        conf = data.get('confidence_level', 'N/A')
                        risk = data.get('risk_level', 'N/A')

                        # Get precision if available
                        precision = None
                        if 'coefficient_of_precision' in data:
                            precision = data['coefficient_of_precision']
                        elif 'deep_analysis' in data and isinstance(data['deep_analysis'], dict):
                            deep_summary = data['deep_analysis'].get('summary', {})
                            precision = deep_summary.get('coefficient_of_precision')

                        # Add emoji based on recommendation and precision
                        if rec == 'BUY':
                            if precision and precision > 0.7:
                                emoji = "🟢💎"
                            elif precision and precision > 0.5:
                                emoji = "🟢📊"
                            elif precision and precision < 0.5:
                                emoji = "🟡⚠️"
                            else:
                                emoji = "🟢"
                        elif rec == 'SELL':
                            if precision and precision > 0.7:
                                emoji = "🔴💎"
                            elif precision and precision > 0.5:
                                emoji = "🔴📊"
                            elif precision and precision < 0.5:
                                emoji = "🟡⚠️"
                            else:
                                emoji = "🔴"
                        else:  # HOLD or N/A
                            if precision and precision > 0.7:
                                emoji = "🟡💎"
                            elif precision and precision > 0.5:
                                emoji = "🟡📊"
                            elif precision and precision < 0.5:
                                emoji = "⚪⚠️"
                            else:
                                emoji = "🟡"

                        ticker_display = f"{emoji} {tk}"[:7]
                        rec_display = rec[:12]
                        conf_display = conf[:10]
                        risk_display = risk[:11]

                        if has_deep_results:
                            if precision is not None:
                                acc_display = f"{precision:.1%}"[:13]
                            else:
                                acc_display = "N/A"[:13]
                            print(f"│ {ticker_display:7} │ {rec_display:12} │ {conf_display:10} │ {risk_display:11} │ {acc_display:15} │")
                        else:
                            print(f"│ {ticker_display:7} │ {rec_display:12} │ {conf_display:10} │ {risk_display:11} │")

                    if has_deep_results:
                        print("└─────────┴──────────────┴────────────┴─────────────┴─────────────────┘")
                    else:
                        print("└─────────┴──────────────┴────────────┴─────────────┘")

                    # Show execution stats
                    exec_time = result.get('execution_time', 0)
                    analyzed_count = result.get('analyzed_tickers', 0)
                    print(f"\n⏱️  Execution time: {exec_time:.2f}s")
                    print(f"📊 Analyzed {analyzed_count} ticker(s)")
                    print("✅ Portfolio analysis complete")

                    print_json_minimal(result, show_json=not args.summary_only)
                else:
                    print(f"❌ Analysis failed: {result.get('error')}")
                    print_json_minimal(result, show_json=True)

            elif cmd == 'history':
                history = engine.get_analysis_history(
                    ticker=args.ticker, portfolio_id=args.portfolio_id, limit=args.limit
                )
                if history:
                    print("📜 Recent Analysis History:")
                    print("┌─────────────────────┬─────────┬─────────────────┐")
                    print("│ Timestamp           │ Ticker  │ Recommendation  │")
                    print("├─────────────────────┼─────────┼─────────────────┤")
                    for h in history:
                        ts = h.get('created_at', '')[:19]
                        tkr = h.get('ticker', '')[:7]
                        rec = (h.get('recommendation') or
                               h.get('analysis_data', {}).get('overall_recommendation', 'N/A'))[:15]
                        print(f"│ {ts:19} │ {tkr:7} │ {rec:15} │")
                    print("└─────────────────────┴─────────┴─────────────────┘")
                else:
                    print("📜 No analysis history found")

            elif cmd == 'accuracy':
                trends = engine.get_accuracy_trends(
                    ticker=args.ticker, portfolio_id=args.portfolio_id
                )
                if trends:
                    print("📈 Accuracy Trends:")
                    print("┌─────────┬─────────────────┬──────────────────┐")
                    print("│ Ticker  │ Avg Accuracy    │ Total Comparisons│")
                    print("├─────────┼─────────────────┼──────────────────┤")
                    for t in trends:
                        ticker = t.get('ticker', '')[:7]
                        accuracy = f"{t.get('avg_accuracy', 0):.2%}"[:15]
                        total = str(t.get('total_comparisons', 0))[:16]
                        print(f"│ {ticker:7} │ {accuracy:15} │ {total:16} │")
                    print("└─────────┴─────────────────┴─────────────────┘")
                else:
                    print("📈 No accuracy data found")
            else:
                portfolio_parser.print_help()

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
