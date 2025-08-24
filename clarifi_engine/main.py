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
                             include_investment_advice=True, include_seasonal=True):
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
        """
        print(f"🚀 ClariFi: Clarify your Finances")
        print("=======================")
        print(f"🚀 === COMPREHENSIVE MARKET ANALYSIS === 🚀")
        print(f"Tickers: {', '.join(tickers)}")
        print(f"Period: {period}")
        print(f"Analysis Features: Patterns={include_patterns}, Events={include_events}, Advanced Viz={include_advanced_viz}, Options={include_options}, Investment Advice={include_investment_advice}")
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

        # Step 5: Options Analysis and Risk Assessment
        options_results = {}
        if include_options:
            print("\n⚖️ BLACK-SCHOLES OPTIONS ANALYSIS...")
            for ticker in tickers:
                if ticker in stock_data_dict:
                    print(f"  🔍 Analyzing options risk for {ticker}...")
                    risk_analysis = self.options_analyzer.analyze_stock_risk(stock_data_dict[ticker])
                    options_results[ticker] = risk_analysis

                    # Display key metrics
                    current_price = risk_analysis['current_price']
                    current_vol = risk_analysis['current_volatility']
                    risk_level = risk_analysis['risk_assessment']
                    vol_percentile = risk_analysis.get('volatility_percentile', 'N/A')

                    print(f"      💰 Current Price: ${current_price:.2f}")
                    print(f"      📊 Current Volatility: {current_vol:.1%}")
                    print(f"      ⚠️ Risk Level: {risk_level}")
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

        # Step 7: Generate Summary Report
        print("\n📋 GENERATING ANALYSIS SUMMARY...")
        self._generate_summary_report(tickers, correlation_results, volatility_results,
                                    trend_results, event_results, unusual_movements,
                                    options_results, portfolio_advice, seasonal_results)

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
                               options_results=None, portfolio_advice=None, seasonal_results=None):
        """Generate a comprehensive text summary of all analyses."""

        print("\n" + "="*80)
        print("📊 MARKET ANALYSIS SUMMARY REPORT")
        print("="*80)

        print(f"\n🎯 ANALYZED TICKERS: {', '.join(tickers)}")
        print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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

        # Options Analysis Summary
        if options_results:
            print(f"\n⚖️ BLACK-SCHOLES RISK ANALYSIS:")
            for ticker, risk_data in options_results.items():
                risk_level = risk_data['risk_assessment']
                current_vol = risk_data['current_volatility']
                vol_percentile = risk_data.get('volatility_percentile', 'N/A')

                risk_emoji = "🔴" if "High" in risk_level else \
                           "🟡" if "Moderate" in risk_level else "🟢"

                print(f"  {risk_emoji} {ticker}: {risk_level} "
                      f"(Vol: {current_vol:.1%}, Percentile: {vol_percentile if vol_percentile != 'N/A' else 'N/A'})")

                # Show expected moves for 30d and 90d
                for timeframe in ['30d', '90d']:
                    if timeframe in risk_data['risk_metrics']:
                        expected_move = risk_data['risk_metrics'][timeframe]['expected_move']
                        print(f"      📊 {timeframe} expected move: ±{expected_move:.1%}")

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

        # Add options-based insights
        if options_results:
            high_vol_stocks = [ticker for ticker, data in options_results.items()
                             if "High" in data['risk_assessment']]
            if high_vol_stocks:
                insights.append(f"⚠️ High volatility (options opportunity): {', '.join(high_vol_stocks)}")

            low_vol_stocks = [ticker for ticker, data in options_results.items()
                            if "Low" in data['risk_assessment']]
            if low_vol_stocks:
                insights.append(f"💎 Low volatility (stable): {', '.join(low_vol_stocks)}")

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

        if insights:
            for insight in insights:
                print(f"  {insight}")
        else:
            print("  📊 Mixed signals - consider waiting for clearer trends")

        print("="*80)


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

⚖️ OPTIONS & RISK ANALYSIS:
  ./run.sh analyze AAPL MSFT --period 1y  # Full analysis with options
  ./run.sh analyze PLTR --no-options      # Skip options analysis

💰 INVESTMENT SUGGESTIONS:
  ./run.sh analyze AAPL TSLA MSFT         # Get BUY/SELL/HOLD advice
  ./run.sh analyze PLTR --no-investment-advice  # Skip suggestions

💡 TIP: Use quotes for tickers with spaces: "SAAB B"
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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize analysis tools
    try:
        analysis = AdvancedStockAnalysis()
        legacy_analysis = StockAnalysis()  # For backward compatibility
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
                include_seasonal=not args.no_seasonal
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

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
