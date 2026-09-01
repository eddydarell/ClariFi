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
import io
import contextlib
import sqlite3
import numpy as np
from datetime import datetime, timedelta

# Initialize colorama for cross-platform colored output
try:
    import colorama
    colorama.init(autoreset=True)
    from colorama import Fore, Back, Style
    HAS_COLORAMA = True
except ImportError:
    # Fallback if colorama not available
    class Fore:
        GREEN = ''
        RED = ''
        YELLOW = ''
        BLUE = ''
        MAGENTA = ''
        CYAN = ''
        WHITE = ''
        BLACK = ''
    class Back:
        GREEN = ''
        RED = ''
        YELLOW = ''
        BLUE = ''
    class Style:
        BRIGHT = ''
        DIM = ''
        NORMAL = ''
    HAS_COLORAMA = False

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
    from alphavantage_analyzer import AlphaVantageAnalyzer
    from strategy_analyzer import StrategyAnalyzer
    from prediction_tracker import PredictionTracker
    from ticker_suggestion_engine import TickerSuggestionEngine
    # Import ML analyzer with fallback
    try:
        from ml_analyzer import MLAnalyzer
    except Exception:
        MLAnalyzer = None
    # Import RNN analyzer with fallback
    try:
        from rnn_analyzer import RNNAnalyzer
    except Exception:
        RNNAnalyzer = None
    # Import Transformer analyzer with fallback
    try:
        from transformer_analyzer import TransformerAnalyzer
    except Exception:
        TransformerAnalyzer = None
    # Import RL analyzer with fallback
    try:
        from rl_analyzer import RLAnalyzer
    except Exception:
        RLAnalyzer = None
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
        # Initialize ML analyzer if available
        try:
            self.ml_analyzer = MLAnalyzer() if MLAnalyzer else None
        except Exception:
            self.ml_analyzer = None
        # Initialize RNN analyzer if available
        try:
            self.rnn_analyzer = RNNAnalyzer() if RNNAnalyzer else None
        except Exception:
            self.rnn_analyzer = None
        # Initialize Transformer analyzer if available
        try:
            self.transformer_analyzer = TransformerAnalyzer() if TransformerAnalyzer else None
        except Exception:
            self.transformer_analyzer = None
        # Initialize RL analyzer if available
        try:
            self.rl_analyzer = RLAnalyzer() if RLAnalyzer else None
        except Exception:
            self.rl_analyzer = None

    def _persist_prediction_tracking(self, ticker, entry_price, predictions, db_manager=None):
        """Persist strategy predictions to the database for later scoring."""
        try:
            tracker = PredictionTracker(db_manager=db_manager) if db_manager else PredictionTracker()
            return tracker.process_run(
                ticker=ticker,
                entry_price=entry_price,
                predictions=predictions,
            )
        except Exception as exc:
            return {
                "resolved": [],
                "new_prediction_ids": [],
                "confidence": {},
                "error": str(exc),
            }

    def analyze_multi_timeframe(self, ticker, periods=['1mo', '3mo', '6mo', '1y']):
        """
        Analyze ticker across multiple timeframes for trend confirmation.

        Args:
            ticker (str): Stock ticker symbol
            periods (list): List of period strings to analyze

        Returns:
            dict: Multi-timeframe analysis results with consensus
        """
        results = {}

        for period in periods:
            try:
                data = self.downloader.download_stock_data(ticker, None, None, period)
                if data is not None and len(data) > 50:
                    # Calculate returns for this timeframe
                    total_return = (data['Close'].iloc[-1] / data['Close'].iloc[0] - 1) * 100
                    volatility = data['Close'].pct_change().std() * np.sqrt(252) * 100

                    # Simple trend classification using moving averages
                    sma20 = data['Close'].rolling(20).mean().iloc[-1]
                    sma50 = data['Close'].rolling(50).mean().iloc[-1] if len(data) >= 50 else None
                    current = data['Close'].iloc[-1]

                    # Determine trend
                    if sma50 is not None:
                        if current > sma20 > sma50:
                            trend = 'STRONG_BULLISH'
                        elif current > sma20:
                            trend = 'BULLISH'
                        elif current < sma20 < sma50:
                            trend = 'STRONG_BEARISH'
                        elif current < sma20:
                            trend = 'BEARISH'
                        else:
                            trend = 'NEUTRAL'
                    else:
                        trend = 'BULLISH' if current > sma20 else 'BEARISH'

                    results[period] = {
                        'return_pct': float(total_return),
                        'volatility_pct': float(volatility),
                        'trend': trend,
                        'current_price': float(current),
                        'sma20': float(sma20),
                        'sma50': float(sma50) if sma50 is not None else None
                    }
            except Exception as e:
                print(f"⚠️  Could not analyze {period} timeframe: {e}")
                continue

        if not results:
            return {'error': 'No timeframes successfully analyzed'}

        # Calculate consensus
        bullish_count = sum(1 for r in results.values() if 'BULL' in r['trend'])
        bearish_count = sum(1 for r in results.values() if 'BEAR' in r['trend'])
        total_count = len(results)

        if bullish_count >= total_count * 0.6:
            consensus = 'BULLISH'
            confidence = 'HIGH' if bullish_count >= total_count * 0.75 else 'MEDIUM'
        elif bearish_count >= total_count * 0.6:
            consensus = 'BEARISH'
            confidence = 'HIGH' if bearish_count >= total_count * 0.75 else 'MEDIUM'
        else:
            consensus = 'NEUTRAL'
            confidence = 'LOW'

        return {
            'ticker': ticker,
            'timeframes': results,
            'consensus': consensus,
            'confidence': confidence,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'neutral_count': total_count - bullish_count - bearish_count
        }

    def _print_header(self, title, emoji="🚀"):
        """Print a consistent header for all analysis types."""
        print(f"{Fore.CYAN}ClariFi: Clarify your Finances{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'=' * 50}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}=== {title.upper()} ==={Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'=' * 50}{Style.RESET_ALL}")

    def _print_section_header(self, title, emoji="📊"):
        """Print a consistent section header."""
        print(f"\n{Fore.YELLOW}{title.upper()}:{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'-' * 40}{Style.RESET_ALL}")

    def _print_subsection(self, title, emoji="  "):
        """Print a consistent subsection."""
        print(f"{Fore.CYAN}{title}:{Style.RESET_ALL}")

    def _print_success(self, message):
        """Print a success message."""
        print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

    def _print_error(self, message):
        """Print an error message."""
        print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

    def _print_warning(self, message):
        """Print a warning message."""
        print(f"⚠️  {message}")

    def _print_info(self, message):
        """Print an info message."""
        print(f"ℹ️  {message}")

    def _convert_to_json_serializable(self, obj):
        """Convert pandas objects and other non-JSON serializable objects to JSON-compatible formats."""
        if obj is None:
            return None

        # Handle dataclasses (like SeasonalPatternResult)
        if hasattr(obj, '__dataclass_fields__'):
            from dataclasses import asdict
            try:
                return self._convert_to_json_serializable(asdict(obj))
            except:
                return str(obj)

        # Handle pandas DataFrame
        if hasattr(obj, 'to_dict'):
            try:
                # Convert DataFrame to dict, ensuring datetime indices are converted
                df_dict = obj.to_dict()
                # Convert any Timestamp keys to strings
                if hasattr(obj, 'index') and hasattr(obj.index, 'dtype'):
                    if 'datetime' in str(obj.index.dtype).lower():
                        # If index is datetime, convert to string keys
                        return {str(k): v for k, v in df_dict.items()}
                return df_dict
            except:
                return str(obj)

        # Handle pandas Series
        if hasattr(obj, 'to_list'):
            try:
                return obj.to_list()
            except:
                return str(obj)

        # Handle dictionaries recursively
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                # Convert Timestamp keys to strings
                if hasattr(key, 'isoformat'):
                    key = key.isoformat()
                elif hasattr(key, 'strftime'):
                    key = key.strftime('%Y-%m-%d')
                else:
                    key = str(key)
                result[key] = self._convert_to_json_serializable(value)
            return result

        # Handle lists/tuples recursively
        if isinstance(obj, (list, tuple)):
            return [self._convert_to_json_serializable(item) for item in obj]

        # Handle numpy types
        if hasattr(obj, 'item'):
            try:
                return obj.item()
            except:
                return str(obj)

        # Handle datetime objects
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()

        # Handle pandas Timestamp
        if hasattr(obj, 'to_pydatetime'):
            try:
                return obj.to_pydatetime().isoformat()
            except:
                return str(obj)

        # For other objects, try to convert to string
        try:
            # Check if it's a basic type
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            else:
                return str(obj)
        except:
            return str(obj)

    def comprehensive_analysis(self, tickers, period="1y", download=True,
                             include_patterns=True, include_events=True,
                             include_advanced_viz=True, include_options=True,
                             include_investment_advice=True, include_seasonal=True,
                             include_deep=False, deep_chunk_months=3, include_ml=False, json_output=False):
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
            include_ml (bool): Whether to include machine learning analysis
            json_output (bool): Whether to return structured data instead of printing
        """
        if not json_output:
            self._print_header("COMPREHENSIVE MARKET ANALYSIS")
            print(f"📈 Tickers: {', '.join(tickers)}")
            print(f"⏰ Period: {period}")
            features = []
            if include_patterns: features.append("Patterns")
            if include_events: features.append("Events")
            if include_advanced_viz: features.append("Advanced Viz")
            if include_options: features.append("Options")
            if include_investment_advice: features.append("Investment Advice")
            if include_seasonal: features.append("Seasonal")
            if include_deep: features.append("Deep Analysis")
            if include_ml: features.append("ML Analysis")
            print(f"🔧 Analysis Features: {', '.join(features)}")
            if include_deep:
                print(f"🔬 Deep Analysis: Chunk size = {deep_chunk_months} months")
            print()

        # Initialize result structure for JSON output
        result = {
            "command": "analyze",
            "tickers": tickers,
            "period": period,
            "features": [],
            "data": {},
            "analyses": {},
            "recommendations": {},
            "errors": []
        }

        if include_patterns: result["features"].append("patterns")
        if include_events: result["features"].append("events")
        if include_advanced_viz: result["features"].append("advanced_visualizations")
        if include_options: result["features"].append("options")
        if include_investment_advice: result["features"].append("investment_advice")
        if include_seasonal: result["features"].append("seasonal")
        if include_deep: result["features"].append("deep_analysis")
        if include_ml: result["features"].append("ml_analysis")

        # Step 1: Download data
        stock_data_dict = {}
        if download:
            if not json_output:
                self._print_section_header("DOWNLOADING STOCK DATA")
            results = self.downloader.download_multiple_stocks(tickers, None, None, period)

            if not results:
                error_msg = "No data downloaded. Exiting."
                if json_output:
                    result["errors"].append(error_msg)
                    return result
                else:
                    self._print_error(error_msg)
                    return

            if not json_output:
                self._print_success("Data download completed!")

        # Load data into memory
        if not json_output:
            self._print_section_header("LOADING DATA")
        for ticker in tickers:
            files = self.visualizer.find_stock_files(ticker)
            if files:
                latest_file = files[0] if len(files) == 1 and str(files[0]).startswith("db://") else max(files, key=os.path.getctime)
                data = self.visualizer.load_stock_data(latest_file)
                if data is not None:
                    stock_data_dict[ticker] = data
                    result["data"][ticker] = {
                        "records": len(data),
                        "date_range": {
                            "start": str(data.index.min()) if not data.empty else None,
                            "end": str(data.index.max()) if not data.empty else None
                        }
                    }
                    if not json_output:
                        print(f"  ✓ {ticker}: {len(data)} records loaded")
                else:
                    error_msg = f"Failed to load data for {ticker}"
                    result["errors"].append(error_msg)
                    if not json_output:
                        print(f"  ❌ {ticker}: {error_msg}")
            else:
                error_msg = f"No data files found for {ticker}"
                result["errors"].append(error_msg)
                if not json_output:
                    print(f"  ❌ {ticker}: {error_msg}")

        if not stock_data_dict:
            error_msg = "No valid data loaded. Exiting."
            if json_output:
                result["errors"].append(error_msg)
                return result
            else:
                self._print_error(error_msg)
                return
        # Step 2: Pattern Analysis
        correlation_results = None
        volatility_results = None
        trend_results = None
        technical_results = {}

        if include_patterns:
            if not json_output:
                self._print_section_header("PATTERN ANALYSIS")
                self._print_subsection("Analyzing correlation patterns")
            correlation_results = self.pattern_analyzer.analyze_correlation_patterns(stock_data_dict)

            if not json_output:
                self._print_subsection("Analyzing volatility patterns")
            volatility_results = self.pattern_analyzer.detect_volatility_patterns(stock_data_dict)

            if not json_output:
                self._print_subsection("Analyzing trend strength")
            trend_results = self.pattern_analyzer.analyze_trend_strength(stock_data_dict)

            if not json_output:
                self._print_subsection("Adding technical indicators")
            for ticker, data in stock_data_dict.items():
                self.pattern_analyzer.add_technical_indicators(data)
                # Capture last available indicator values for reporting
                try:
                    technical_results[ticker] = {
                        'ADX': float(data['ADX'].iloc[-1]) if 'ADX' in data.columns and not data['ADX'].isna().iloc[-1] else None,
                        'ATR': float(data['ATR'].iloc[-1]) if 'ATR' in data.columns and not data['ATR'].isna().iloc[-1] else None,
                        'CCI': float(data['CCI'].iloc[-1]) if 'CCI' in data.columns and not data['CCI'].isna().iloc[-1] else None,
                        'Williams_%R': float(data['Williams_%R'].iloc[-1]) if 'Williams_%R' in data.columns and not data['Williams_%R'].isna().iloc[-1] else None,
                        'OBV': float(data['OBV'].iloc[-1]) if 'OBV' in data.columns and not data['OBV'].isna().iloc[-1] else None,
                        'Parabolic_SAR': float(data['Parabolic_SAR'].iloc[-1]) if 'Parabolic_SAR' in data.columns and not data['Parabolic_SAR'].isna().iloc[-1] else None,
                        'RSI_14': float(data['RSI_14'].iloc[-1]) if 'RSI_14' in data.columns and not data['RSI_14'].isna().iloc[-1] else None,
                        'RSI_30': float(data['RSI_30'].iloc[-1]) if 'RSI_30' in data.columns and not data['RSI_30'].isna().iloc[-1] else None,
                        'MACD': float(data['MACD'].iloc[-1]) if 'MACD' in data.columns and not data['MACD'].isna().iloc[-1] else None,
                        'MACD_Signal': float(data['MACD_Signal'].iloc[-1]) if 'MACD_Signal' in data.columns and not data['MACD_Signal'].isna().iloc[-1] else None,
                        'BB_Width': float(data['BB_Width'].iloc[-1]) if 'BB_Width' in data.columns and not data['BB_Width'].isna().iloc[-1] else None,
                        'current_price': float(data['Close'].iloc[-1])
                    }

                    # Add risk metrics
                    risk_metrics = self.pattern_analyzer.calculate_risk_metrics(data)
                    technical_results[ticker]['risk_metrics'] = risk_metrics

                    # Add market regime detection
                    regime = self.pattern_analyzer.detect_market_regime(data)
                    technical_results[ticker]['market_regime'] = regime

                except Exception as e:
                    technical_results[ticker] = {'error': str(e)}

            result["analyses"]["patterns"] = {
                "correlation": self._convert_to_json_serializable(correlation_results) if json_output else correlation_results,
                "volatility": self._convert_to_json_serializable(volatility_results) if json_output else volatility_results,
                "trend_strength": self._convert_to_json_serializable(trend_results) if json_output else trend_results,
                "technical_indicators": technical_results
            }

            if not json_output:
                self._print_success("Pattern analysis completed!")

        # Step 3: Event Correlation
        event_results = None
        unusual_movements = None

        if include_events:
            if not json_output:
                self._print_section_header("EVENT CORRELATION ANALYSIS")
                self._print_subsection("Correlating with major events")
            event_results = self.event_correlator.correlate_events_with_movements(stock_data_dict)

            if not json_output:
                self._print_subsection("Identifying unusual movements")
            unusual_movements = self.event_correlator.identify_unusual_movements(stock_data_dict)

            result["analyses"]["events"] = {
                "correlations": self._convert_to_json_serializable(event_results) if json_output else event_results,
                "unusual_movements": self._convert_to_json_serializable(unusual_movements) if json_output else unusual_movements
            }

            if not json_output:
                self._print_success("Event correlation completed!")

        # Step 4: Advanced Visualizations
        if include_advanced_viz:
            if not json_output:
                self._print_section_header("CREATING ADVANCED VISUALIZATIONS")

            if correlation_results:
                if not json_output:
                    self._print_subsection("Creating correlation heatmaps")
                self.advanced_visualizer.plot_correlation_heatmap(correlation_results)
                if not json_output:
                    self._print_subsection("Creating rolling correlation plots")
                self.advanced_visualizer.plot_rolling_correlations(correlation_results)

            if volatility_results:
                if not json_output:
                    self._print_subsection("Creating volatility clustering plots")
                self.advanced_visualizer.plot_volatility_clustering(volatility_results)

            if event_results:
                if not json_output:
                    self._print_subsection("Creating event impact visualizations")
                self.advanced_visualizer.plot_event_impact_analysis(event_results)

            # Support/Resistance for first available ticker
            if stock_data_dict:
                first_ticker = list(stock_data_dict.keys())[0]
                if not json_output:
                    self._print_subsection(f"Creating support/resistance for {first_ticker}")
                sr_data = self.pattern_analyzer.identify_support_resistance(
                    stock_data_dict[first_ticker], first_ticker)
                self.advanced_visualizer.plot_support_resistance(
                    sr_data, stock_data_dict[first_ticker])

            if not json_output:
                self._print_success("Advanced visualizations completed!")

        # Step 5: Enhanced Options Analysis and Risk Assessment
        options_results = {}
        if include_options:
            if not json_output:
                self._print_section_header("ENHANCED OPTIONS & RISK ANALYSIS")
            for ticker in tickers:
                if ticker in stock_data_dict:
                    if not json_output:
                        self._print_subsection(f"Analyzing comprehensive risk for {ticker}")
                    risk_analysis = self.options_analyzer.comprehensive_risk_analysis(stock_data_dict[ticker])

                    # Also get the traditional options analysis for pricing data
                    options_analysis = self.options_analyzer.analyze_options(ticker, stock_data_dict[ticker])

                    # Merge the results
                    merged_results = {**risk_analysis, **options_analysis}
                    options_results[ticker] = merged_results

                    if not json_output:
                        # Display key metrics
                        current_price = risk_analysis['current_price']
                        current_vol = risk_analysis['current_volatility']
                        risk_level = risk_analysis['risk_assessment']

                        # Get comprehensive risk metrics
                        advanced_var = risk_analysis.get('advanced_var_measures', {})
                        risk_ratios = risk_analysis.get('risk_ratios', {})
                        var_95_pct = advanced_var.get('var_95_pct', 0)
                        sharpe_ratio = risk_ratios.get('sharpe_ratio', 0)

                        print(f"    💰 Current Price: ${current_price:.2f}")
                        print(f"    📊 Current Volatility: {current_vol:.1%}")
                        print(f"    ⚠️  Risk Level: {risk_level}")
                        print(f"    📊 VaR (95%): {var_95_pct:.1f}% daily")

                        if sharpe_ratio != 0:
                            sharpe_emoji = "🌟" if sharpe_ratio > 1.0 else "📊" if sharpe_ratio > 0.5 else "❌"
                            print(f"    {sharpe_emoji} Sharpe Ratio: {sharpe_ratio:.2f}")

                        vol_percentile = risk_analysis.get('volatility_percentile', 'N/A')
                        if vol_percentile != 'N/A':
                            print(f"    📈 Volatility Percentile: {vol_percentile:.1f}%")

                        # Show expected moves for key timeframes
                        for timeframe in ['30d', '90d']:
                            if timeframe in risk_analysis['risk_metrics']:
                                metrics = risk_analysis['risk_metrics'][timeframe]
                                expected_move = metrics['expected_move']
                                print(f"    🎯 Expected {timeframe} move: ±{expected_move:.1%}")

            result["analyses"]["options"] = self._convert_to_json_serializable(options_results) if json_output else options_results

            if not json_output:
                self._print_success("Options analysis completed!")

        # Step 6: Investment Suggestions
        investment_suggestions = {}
        portfolio_advice = None
        if include_investment_advice:
            if not json_output:
                self._print_section_header("GENERATING INVESTMENT SUGGESTIONS")

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
            if not json_output:
                self._print_subsection("Analyzing portfolio recommendations")
            portfolio_advice = self.investment_advisor.get_portfolio_suggestions(
                portfolio_data, correlation_results
            )

            # Display individual suggestions
            if not json_output:
                for ticker, suggestion in portfolio_advice['individual_suggestions'].items():
                    action_emoji = "🟢" if suggestion['suggestion'] == 'BUY' else \
                                  "🔴" if suggestion['suggestion'] == 'SELL' else "🟡"
                    confidence_emoji = "🔥" if suggestion['confidence'] == 'HIGH' else \
                                      "👍" if suggestion['confidence'] == 'MEDIUM' else "🤔"

                    print(f"  {action_emoji} {ticker}: {suggestion['suggestion']} "
                          f"({suggestion['confidence']} confidence) {confidence_emoji}")
                    print(f"    Risk: {suggestion['risk_level']}")
                    print(f"    Reasoning: {suggestion['reasoning']}")

                    # Display enhanced features: holding period and recovery forecast
                    if 'holding_period_analysis' in suggestion:
                        holding = suggestion['holding_period_analysis']
                        print(f"    ⏱️  Suggested Holding Period: {holding['suggested_holding_days']} days ({holding['confidence']} confidence)")

                    if 'recovery_forecast' in suggestion:
                        recovery = suggestion['recovery_forecast']
                        if recovery.get('is_currently_in_dip', False) and recovery.get('forecast_recovery_date'):
                            print(f"    🔮 Recovery Forecast: {recovery['forecast_recovery_date']} ({recovery.get('confidence', 'UNKNOWN')} confidence)")
                            print(f"    📉 Currently in dip: {recovery.get('current_dip_magnitude', 0):.1%} from recent high")
                        elif not recovery.get('is_currently_in_dip', True) and recovery.get('recovery_statistics'):
                            stats = recovery['recovery_statistics']
                            print(f"    📈 Historical Recovery Pattern: {stats.get('average_days', 0):.1f} days average")
                    print()

            result["analyses"]["investment_advice"] = self._convert_to_json_serializable(portfolio_advice) if json_output else portfolio_advice

            if not json_output:
                self._print_success("Investment suggestions completed!")

        # Step 6.5: Seasonal Analysis
        seasonal_results = {}
        if include_seasonal:
            if not json_output:
                self._print_section_header("SEASONAL ANALYSIS")
            for ticker in tickers:
                if ticker in stock_data_dict:
                    if not json_output:
                        self._print_subsection(f"Analyzing seasonal patterns for {ticker}")
                    seasonal_result = self.seasonal_analyzer.analyze(stock_data_dict[ticker])
                    if seasonal_result:
                        seasonal_results[ticker] = seasonal_result

                        if not json_output:
                            # Display key seasonal insights
                            print(f"    🌟 Recommendation: {seasonal_result.recommendation}")
                            print(f"    📊 Seasonal Bias Score: {seasonal_result.bias_score:.2f}")
                            print(f"    📈 Best Months: {', '.join(seasonal_result.best_months)}")
                            print(f"    📉 Worst Months: {', '.join(seasonal_result.worst_months)}")
                            print(f"    💡 Pattern: {seasonal_result.seasonal_summary}")
                    else:
                        if not json_output:
                            self._print_warning(f"Insufficient data for seasonal analysis")

            result["analyses"]["seasonal"] = self._convert_to_json_serializable(seasonal_results) if json_output else seasonal_results

            if not json_output:
                if seasonal_results:
                    self._print_success("Seasonal analysis completed!")
                else:
                    self._print_warning("No seasonal patterns detected (insufficient data)")

        # Step 6.6: ML Analysis
        ml_results = {}
        if include_ml:
            if not json_output:
                self._print_section_header("MACHINE LEARNING ANALYSIS")

            if self.ml_analyzer is None:
                error_msg = "ML analyzer not available. Please install required packages: pip install scikit-learn xgboost lightgbm"
                if json_output:
                    result["errors"].append(error_msg)
                else:
                    self._print_error(error_msg)
            else:
                for ticker in tickers:
                    if ticker in stock_data_dict:
                        if not json_output:
                            self._print_subsection(f"Running ML analysis for {ticker}")
                        try:
                            ml_result = self.ml_analyzer.analyze(stock_data_dict[ticker], ticker, prediction_horizon=5)
                            if ml_result:
                                ml_results[ticker] = ml_result

                                if not json_output:
                                    # Display key ML insights
                                    rec = ml_result.recommendation
                                    print(f"    🎯 Recommendation: {rec.action} (Confidence: {rec.confidence:.1f})")
                                    print(f"    📈 Predicted Return: {rec.predicted_return_pct:.1f}%")
                                    print(f"    🧠 Best Model: {ml_result.best_model}")
                                    print(f"    💡 Reasoning: {rec.reasoning}")

                                    # Show top features if available
                                    if ml_result.feature_analysis:
                                        top_features = list(ml_result.feature_analysis.items())[:3]
                                        feature_str = ", ".join([f"{feat}: {imp:.3f}" for feat, imp in top_features])
                                        print(f"    🔍 Top Features: {feature_str}")
                            else:
                                if not json_output:
                                    self._print_warning(f"ML analysis failed for {ticker}")
                        except Exception as e:
                            error_msg = f"ML analysis error for {ticker}: {str(e)}"
                            if json_output:
                                result["errors"].append(error_msg)
                            else:
                                self._print_error(error_msg)

            result["analyses"]["ml_analysis"] = self._convert_to_json_serializable(ml_results) if json_output else ml_results

            if not json_output:
                if ml_results:
                    self._print_success("ML analysis completed!")
                else:
                    self._print_warning("ML analysis completed with no results")

        # Step 6.7: Deep Analysis (Historical Backtesting)
        deep_results = {}
        if include_deep:
            if not json_output:
                self._print_section_header("DEEP BACKTESTING ANALYSIS")
                print(f"   🔬 Chunk size: {deep_chunk_months} months")

            # Import the engine for deep analysis functionality
            try:
                from engine import ClariFiEngine
                engine = ClariFiEngine()

                for ticker in tickers:
                    if ticker in stock_data_dict:
                        if not json_output:
                            self._print_subsection(f"Running deep analysis for {ticker}")
                        try:
                            deep_result = engine._run_deep_analysis(
                                ticker,
                                stock_data_dict[ticker].copy(),
                                chunk_months=deep_chunk_months
                            )
                            if deep_result and not deep_result.get('error'):
                                deep_results[ticker] = deep_result
                                if not json_output:
                                    summary = deep_result.get('summary', {})
                                    precision = summary.get('coefficient_of_precision', 0)
                                    chunks_eval = summary.get('chunks_evaluated', 0)
                                    print(f"    ✓ Precision coefficient: {precision:.2%}")
                                    print(f"    📊 Evaluated {chunks_eval} chunks")
                            else:
                                error_msg = deep_result.get('error', 'Unknown error') if deep_result else 'Failed to execute'
                                if not json_output:
                                    print(f"    ❌ Deep analysis failed: {error_msg}")
                                result["errors"].append(f"Deep analysis failed for {ticker}: {error_msg}")
                        except Exception as e:
                            error_msg = str(e)
                            if not json_output:
                                print(f"    ❌ Deep analysis error for {ticker}: {error_msg}")
                            result["errors"].append(f"Deep analysis error for {ticker}: {error_msg}")
                    else:
                        if not json_output:
                            print(f"    ⚠️  No data available for {ticker}")

                result["analyses"]["deep"] = self._convert_to_json_serializable(deep_results) if json_output else deep_results

                if not json_output:
                    if deep_results:
                        self._print_success("Deep analysis completed!")
                    else:
                        self._print_warning("No deep analysis results generated")

            except ImportError as e:
                error_msg = f"Could not import engine for deep analysis: {e}"
                if not json_output:
                    print(f"    ❌ {error_msg}")
                    self._print_warning("Deep analysis requires the ClariFiEngine module")
                result["errors"].append(error_msg)

        # Step 7: Generate strategy recommendations and persist their predictions.
        result["analyses"]["strategy"] = {}
        if not json_output:
            self._print_section_header("STRATEGY TIMING & HOLD FORECASTS")
        for ticker in tickers:
            if ticker not in stock_data_dict:
                continue
            try:
                strategy_analyzer = StrategyAnalyzer()
                strategy = strategy_analyzer.generate_strategy(
                    ticker=ticker,
                    data=stock_data_dict[ticker],
                    period=period,
                    seasonal_analysis=seasonal_results.get(ticker) if isinstance(seasonal_results, dict) else None,
                    deep_analysis=deep_results.get(ticker) if isinstance(deep_results, dict) else None,
                    technical_indicators=technical_results.get(ticker),
                    find_optimum=True,
                )
                result["analyses"]["strategy"][ticker] = self._convert_to_json_serializable(strategy)
                if not json_output:
                    print(f"  {ticker}: {strategy.action} ({strategy.timeframe}, {strategy.confidence} confidence)")
                    for timeframe in ('short_term', 'mid_term', 'long_term'):
                        prediction = strategy.predictions.get(timeframe)
                        if prediction:
                            print(
                                f"    {timeframe}: ${prediction.predicted_price:.2f} "
                                f"(${prediction.price_lower_bound:.2f}-${prediction.price_upper_bound:.2f})"
                            )
                    for action in ('buy', 'sell'):
                        moment = strategy.optimal_moments.get(action)
                        if moment:
                            print(f"    {moment.action}: {moment.optimal_date} ({moment.days_from_now} days)")
                tracking_result = self._persist_prediction_tracking(
                    ticker=ticker,
                    entry_price=strategy.entry_price,
                    predictions=strategy.predictions,
                )
                if tracking_result.get('new_prediction_ids'):
                    result.setdefault('prediction_tracking', {})[ticker] = {
                        'stored_prediction_ids': tracking_result['new_prediction_ids'],
                        'confidence': tracking_result.get('confidence', {}),
                    }
            except Exception as exc:
                result["analyses"]["strategy"][ticker] = {'error': str(exc)}
                result.setdefault('errors', []).append(f"Prediction tracking failed for {ticker}: {str(exc)}")

        # Step 8: Generate Summary Report
        if not json_output:
            self._print_section_header("GENERATING ANALYSIS SUMMARY")
            self._generate_summary_report(tickers, correlation_results, volatility_results,
                    trend_results, event_results, unusual_movements,
                    options_results, portfolio_advice, seasonal_results, deep_results,
                    technical_results=technical_results)

            print("\n" + "=" * 60)
            self._print_success("COMPREHENSIVE ANALYSIS COMPLETED!")
            print(f"📁 Data files: {self.downloader.data_dir}/")
            print(f"📊 Visualizations: {self.visualizer.output_dir}/")
            print(f"📈 Advanced charts: {self.advanced_visualizer.output_dir}/")

        # Return structured result if JSON output requested
        if json_output:
            return result

    def seasonal_only(self, tickers, period="5y", download=True, json_output=False):
        """
        Perform seasonal analysis only for the given tickers.

        Args:
            tickers (list): List of stock tickers
            period (str): Time period for data (default 5y for better seasonal patterns)
            download (bool): Whether to download fresh data
            json_output (bool): Whether to return structured data instead of printing
        """
        if not json_output:
            self._print_header("SEASONAL & HOLIDAY ANALYSIS", "🗓️")
            print(f"📈 Tickers: {', '.join(tickers)}")
            print(f"⏰ Period: {period}")
            print()

        result = {
            "command": "seasonal",
            "tickers": tickers,
            "period": period,
            "data": {},
            "analyses": {},
            "errors": []
        }

        # Step 1: Download data if requested
        if download and not json_output:
            self._print_section_header("DOWNLOADING STOCK DATA")
            results = self.downloader.download_multiple_stocks(tickers, None, None, period)
            if not results:
                self._print_warning("No data downloaded. Continuing with existing data...")
            else:
                self._print_success("Data download completed!")

        # Step 2: Load data
        stock_data_dict = {}
        if not json_output:
            self._print_section_header("LOADING DATA")
        for ticker in tickers:
            files = self.visualizer.find_stock_files(ticker)
            if files:
                latest_file = max(files, key=os.path.getctime)
                data = self.visualizer.load_stock_data(latest_file)
                if data is not None:
                    stock_data_dict[ticker] = data
                    result["data"][ticker] = {
                        "records": len(data),
                        "date_range": {
                            "start": str(data.index.min()) if not data.empty else None,
                            "end": str(data.index.max()) if not data.empty else None
                        }
                    }
                    if not json_output:
                        print(f"  ✓ {ticker}: {len(data)} records loaded")
                else:
                    error_msg = f"Failed to load data for {ticker}"
                    result["errors"].append(error_msg)
                    if not json_output:
                        print(f"  ❌ {ticker}: {error_msg}")
            else:
                error_msg = f"No data files found for {ticker}"
                result["errors"].append(error_msg)
                if not json_output:
                    print(f"  ❌ {ticker}: {error_msg}")

        if not stock_data_dict:
            error_msg = "No valid data loaded. Exiting."
            if json_output:
                result["errors"].append(error_msg)
                return result
            else:
                self._print_error(error_msg)
                return

        # Step 3: Seasonal Analysis
        seasonal_results = {}
        if not json_output:
            self._print_section_header("ANALYZING SEASONAL PATTERNS")

        for ticker in tickers:
            if ticker in stock_data_dict:
                if not json_output:
                    self._print_subsection(f"Analyzing {ticker}")
                seasonal_result = self.seasonal_analyzer.analyze(stock_data_dict[ticker])
                if seasonal_result:
                    seasonal_results[ticker] = seasonal_result
                    if not json_output:
                        # Display results
                        print(f"    🌟 Seasonal Bias Score: {seasonal_result.bias_score:.2f}")
                        print(f"    📈 Best Months: {', '.join(seasonal_result.best_months)}")
                        print(f"    📉 Worst Months: {', '.join(seasonal_result.worst_months)}")
                        print(f"    💡 Pattern: {seasonal_result.seasonal_summary}")
                        print(f"    🎯 Recommendation: {seasonal_result.recommendation}")
                else:
                    error_msg = "Insufficient data for seasonal analysis (need >1 year)"
                    result["errors"].append(f"{ticker}: {error_msg}")
                    if not json_output:
                        self._print_warning(error_msg)

        result["analyses"]["seasonal"] = seasonal_results

        if not seasonal_results:
            error_msg = "No seasonal patterns detected. Need more historical data."
            if json_output:
                result["errors"].append(error_msg)
                return result
            else:
                self._print_error(error_msg)
                return

        # Step 4: Generate Detailed Seasonal Report
        if not json_output:
            self._print_section_header("DETAILED SEASONAL REPORT")

            current_month = calendar.month_name[datetime.now().month]
            print(f"📅 Current Month: {current_month}")

            for ticker, seasonal_data in seasonal_results.items():
                print(f"\n🎯 {ticker} SEASONAL ANALYSIS:")
                print(f"   Bias Score: {seasonal_data.bias_score:.2f} "
                      f"({'Strong' if seasonal_data.bias_score > 0.5 else 'Moderate' if seasonal_data.bias_score > 0.2 else 'Weak'} seasonality)")

        if json_output:
            return result

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
                print(f"   ⚠️  CURRENT TIMING: UNFAVORABLE - {current_month} is typically weak")
            else:
                print(f"   ➡️ CURRENT TIMING: NEUTRAL - {current_month} shows average performance")

        self._print_success("Seasonal analysis complete!")
        print(f"📁 Data files: {self.downloader.data_dir}/")

    def prune_data(self):
        """Interactive data pruning to save disk space."""
        import shutil
        from pathlib import Path

        self._print_header("DATA PRUNING UTILITY", "🗑️")
        print("This tool helps you clean up old data, graphs, and models to save disk space.")
        print()

        # Define directories to clean
        data_dir = Path("data")
        graphs_dir = Path("graphs")
        models_dir = Path("models")

        # Get file counts and sizes
        def get_dir_stats(directory):
            if not directory.exists():
                return 0, 0, []
            files = list(directory.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            return len(files), total_size, files

        data_count, data_size, data_files = get_dir_stats(data_dir)
        graphs_count, graphs_size, graphs_files = get_dir_stats(graphs_dir)
        models_count, models_size, models_files = get_dir_stats(models_dir)

        def format_size(bytes_size):
            """Format bytes to human readable format."""
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_size < 1024.0:
                    return f"{bytes_size:.1f}{unit}"
                bytes_size /= 1024.0
            return f"{bytes_size:.1f}TB"

        print("📊 CURRENT STORAGE USAGE:")
        print(f"  📁 Data files: {data_count} files ({format_size(data_size)})")
        print(f"  📊 Graphs: {graphs_count} files ({format_size(graphs_size)})")
        print(f"  🤖 Models: {models_count} files ({format_size(models_size)})")
        total_size = data_size + graphs_size + models_size
        total_files = data_count + graphs_count + models_count
        print(f"  💾 Total: {total_files} files ({format_size(total_size)})")
        print()

        # Interactive menu
        while True:
            print("🗑️  PRUNING OPTIONS:")
            print("  1. Prune CSV data files")
            print("  2. Prune graph files")
            print("  3. Prune model files")
            print("  4. Prune all (data + graphs + models)")
            print("  5. Show detailed file list")
            print("  6. Exit")
            print()

            try:
                choice = input("Select option (1-6): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n❌ Operation cancelled.")
                return

            if choice == '6':
                print("👋 Exiting prune utility.")
                return

            elif choice == '5':
                # Show detailed file list
                print("\n📋 DETAILED FILE LIST:")
                if data_files:
                    print(f"📁 Data files ({len(data_files)}):")
                    for f in sorted(data_files)[:10]:  # Show first 10
                        print(f"  📄 {f.name} ({format_size(f.stat().st_size)})")
                    if len(data_files) > 10:
                        print(f"  ... and {len(data_files) - 10} more files")
                else:
                    print("📁 No data files found.")

                if graphs_files:
                    print(f"\n📊 Graph files ({len(graphs_files)}):")
                    for f in sorted(graphs_files)[:10]:
                        print(f"  📈 {f.name} ({format_size(f.stat().st_size)})")
                    if len(graphs_files) > 10:
                        print(f"  ... and {len(graphs_files) - 10} more files")
                else:
                    print("\n📊 No graph files found.")

                if models_files:
                    print(f"\n🤖 Model files ({len(models_files)}):")
                    for f in sorted(models_files)[:10]:
                        print(f"  🧠 {f.name} ({format_size(f.stat().st_size)})")
                    if len(models_files) > 10:
                        print(f"  ... and {len(models_files) - 10} more files")
                else:
                    print("\n🤖 No model files found.")
                print()

            elif choice in ['1', '2', '3', '4']:
                # Determine what to prune
                if choice == '1':
                    target_dirs = [('data', data_dir, data_files)]
                    target_name = "CSV data files"
                elif choice == '2':
                    target_dirs = [('graphs', graphs_dir, graphs_files)]
                    target_name = "graph files"
                elif choice == '3':
                    target_dirs = [('models', models_dir, models_files)]
                    target_name = "model files"
                elif choice == '4':
                    target_dirs = [('data', data_dir, data_files), ('graphs', graphs_dir, graphs_files), ('models', models_dir, models_files)]
                    target_name = "all files (data, graphs, models)"

                # Calculate total files to delete
                total_to_delete = sum(len(files) for _, _, files in target_dirs)

                if total_to_delete == 0:
                    print(f"ℹ️  No {target_name} found to prune.")
                    continue

                print(f"\n⚠️  WARNING: This will permanently delete {total_to_delete} {target_name}!")
                print("This action cannot be undone.")

                # Show what will be deleted
                for dir_name, dir_path, files in target_dirs:
                    if files:
                        print(f"\n📁 {dir_name.upper()} directory ({len(files)} files):")
                        for f in sorted(files)[:5]:  # Show first 5
                            print(f"  🗑️  {f.name}")
                        if len(files) > 5:
                            print(f"  ... and {len(files) - 5} more files")

                # Confirm deletion
                while True:
                    try:
                        confirm = input(f"\n🔴 Type 'DELETE' to confirm deletion of {total_to_delete} files: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print("\n❌ Operation cancelled.")
                        return

                    if confirm.upper() == 'DELETE':
                        break
                    elif confirm.upper() == 'CANCEL':
                        print("❌ Operation cancelled.")
                        return
                    else:
                        print("❌ Please type 'DELETE' to confirm or 'CANCEL' to abort.")

                # Perform deletion
                deleted_count = 0
                for dir_name, dir_path, files in target_dirs:
                    for file_path in files:
                        try:
                            if file_path.exists():
                                file_path.unlink()
                                deleted_count += 1
                                print(f"🗑️  Deleted: {file_path.name}")
                        except Exception as e:
                            print(f"❌ Error deleting {file_path.name}: {e}")

                self._print_success(f"Successfully deleted {deleted_count} files!")
                print(f"💾 Space saved: ~{format_size(sum(f.stat().st_size for _, _, files in target_dirs for f in files if f.exists()))}")

                # Ask if user wants to continue
                try:
                    continue_choice = input("\n🔄 Continue pruning? (y/N): ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    print("\n👋 Exiting prune utility.")
                    return

                if continue_choice not in ['y', 'yes']:
                    print("👋 Exiting prune utility.")
                    return

            else:
                print("❌ Invalid option. Please select 1-6.")
                continue

    def _generate_summary_report(self, tickers, correlation_results, volatility_results,
                               trend_results, event_results, unusual_movements,
                               options_results=None, portfolio_advice=None, seasonal_results=None, deep_results=None,
                               technical_results=None):
        """Generate a comprehensive text summary of all analyses.

        Accepts `technical_results` (dict) previously collected during pattern analysis.
        """

        print("\n" + "="*80)
        print("📊 MARKET ANALYSIS SUMMARY REPORT")
        print("="*80)

        # Enhanced Ticker Summary with Recommendations and Accuracy
        self._print_section_header("ANALYZED TICKERS WITH RECOMMENDATIONS")
        self._display_enhanced_ticker_summary(tickers, portfolio_advice, deep_results, technical_results)

        # Prepare to capture technical indicator insights for later aggregation
        tech_insights = []

        print(f"\n📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Trend Analysis Summary
        if trend_results:
            self._print_section_header("TREND ANALYSIS SUMMARY")
            for ticker, trend_data in trend_results.items():
                momentum = "🚀" if trend_data['recent_momentum_pct'] > 5 else \
                          "📉" if trend_data['recent_momentum_pct'] < -5 else "➡️"
                print(f"  {momentum} {ticker}: {trend_data['current_trend']} trend, "
                      f"{trend_data['recent_momentum_pct']:.1f}% momentum, "
                      f"strength: {trend_data['trend_strength']:.3f}")

                if trend_data['sma_crossover'] != 'None':
                    print(f"      🔄 {trend_data['sma_crossover']} detected!")

        # Technical Indicators Summary (use latest values produced earlier)
        if technical_results:
            self._print_section_header("TECHNICAL INDICATORS SUMMARY")
            for ticker, ind in technical_results.items():
                if 'error' in ind:
                    print(f"  ⚠️  {ticker}: {ind['error']}")
                    continue

                print(f"\n  📈 {ticker}:")

                # Basic indicators
                rsi_14 = ind.get('RSI_14')
                rsi_30 = ind.get('RSI_30')
                adx = ind.get('ADX')
                macd = ind.get('MACD')
                macd_signal = ind.get('MACD_Signal')
                bb_width = ind.get('BB_Width')

                if rsi_14:
                    rsi_signal = "Overbought" if rsi_14 > 70 else "Oversold" if rsi_14 < 30 else "Neutral"
                    print(f"     RSI(14): {rsi_14:.1f} ({rsi_signal})")
                if rsi_30:
                    print(f"     RSI(30): {rsi_30:.1f}")
                if adx:
                    trend_str = "Strong trend" if adx > 25 else "Weak/No trend" if adx < 20 else "Moderate trend"
                    print(f"     ADX: {adx:.1f} ({trend_str})")
                if macd and macd_signal:
                    macd_cross = "Bullish" if macd > macd_signal else "Bearish"
                    print(f"     MACD: {macd:.3f} vs Signal: {macd_signal:.3f} ({macd_cross})")
                if bb_width:
                    vol_regime = "High volatility" if bb_width > 5 else "Low volatility" if bb_width < 2 else "Normal"
                    print(f"     BB Width: {bb_width:.2f}% ({vol_regime})")

                # Risk Metrics
                risk = ind.get('risk_metrics', {})
                if risk and 'error' not in risk:
                    print(f"     Risk Metrics:")
                    sharpe = risk.get('sharpe_ratio', 0)
                    sortino = risk.get('sortino_ratio', 0)
                    max_dd = risk.get('max_drawdown_pct', 0)
                    print(f"       Sharpe Ratio: {sharpe:.2f}")
                    print(f"       Sortino Ratio: {sortino:.2f}")
                    print(f"       Max Drawdown: {max_dd:.2f}%")
                    print(f"       Annual Volatility: {risk.get('annual_volatility_pct', 0):.2f}%")

                # Market Regime
                regime = ind.get('market_regime', {})
                if regime and 'error' not in regime:
                    regime_type = regime.get('regime', 'UNKNOWN')
                    confidence = regime.get('confidence', 'LOW')
                    recommendation = regime.get('recommendation', 'N/A')

                    regime_emoji = "📊" if regime_type == 'TRENDING' else "↔️" if regime_type == 'RANGING' else "⚡" if regime_type == 'VOLATILE' else "❓"
                    print(f"     {regime_emoji} Market Regime: {regime_type} (Confidence: {confidence})")
                    print(f"       → {recommendation}")

        # Correlation Summary
        if correlation_results and correlation_results.get('pattern_summary'):
            pattern_summary = correlation_results['pattern_summary']

            self._print_section_header("CORRELATION PATTERNS")

            if pattern_summary['highly_correlated_pairs']:
                self._print_subsection("Highly Correlated Pairs (>0.7)")
                for pair_data in pattern_summary['highly_correlated_pairs'][:5]:
                    print(f"      {pair_data['pair']}: {pair_data['correlation']:.3f} "
                          f"(stability: {pair_data['stability']:.3f})")

            if pattern_summary['negatively_correlated_pairs']:
                self._print_subsection("Negatively Correlated Pairs (<-0.5)")
                for pair_data in pattern_summary['negatively_correlated_pairs'][:3]:
                    print(f"      {pair_data['pair']}: {pair_data['correlation']:.3f}")

            if pattern_summary['strong_leading_indicators']:
                self._print_subsection("Strong Leading Indicators")
                for indicator in pattern_summary['strong_leading_indicators'][:3]:
                    print(f"      {indicator['pair']}: {indicator['lag_days']} day lag, "
                          f"correlation: {indicator['correlation']:.3f}")

        # Volatility Summary
        if volatility_results:
            self._print_section_header("VOLATILITY ANALYSIS")
            for ticker, vol_data in volatility_results.items():
                clustering_score = vol_data['volatility_clustering_score']
                clustering_desc = "High" if clustering_score > 0.3 else \
                                "Moderate" if clustering_score > 0.1 else "Low"
                print(f"  📊 {ticker}: Avg volatility {vol_data['avg_volatility']:.1f}%, "
                      f"clustering: {clustering_desc} ({clustering_score:.3f})")

        # Event Impact Summary
        if event_results and unusual_movements:
            event_summary = self.event_correlator.generate_event_summary(event_results, unusual_movements)

            self._print_section_header("EVENT IMPACT ANALYSIS")

            if event_summary['most_impactful_events']:
                self._print_subsection("Most Impactful Events")
                for event in event_summary['most_impactful_events'][:3]:
                    print(f"      {event['event_date']}: {event['event'][:50]}... "
                          f"(avg impact: {event['avg_impact']:.1f}%)")

            if event_summary['unexplained_movements']:
                self._print_subsection("Unexplained Large Movements")
                for movement in event_summary['unexplained_movements'][:3]:
                    print(f"      {movement['ticker']} on {movement['date']}: "
                          f"{movement['return_pct']:.1f}% ({movement['magnitude']})")

        # Enhanced Options & Risk Analysis Summary
        if options_results:
            self._print_section_header("COMPREHENSIVE RISK ANALYSIS")
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
            self._print_section_header("INVESTMENT RECOMMENDATIONS")
            summary = portfolio_advice['portfolio_summary']

            self._print_subsection("Portfolio Overview")
            print(f"  🟢 BUY recommendations: {summary['buy_recommendations']}")
            print(f"  🔴 SELL recommendations: {summary['sell_recommendations']}")
            print(f"  🟡 HOLD recommendations: {summary['hold_recommendations']}")
            print(f"  ⚠️ High-risk positions: {summary['high_risk_positions']}")
            print(f"  📈 Portfolio risk level: {portfolio_advice['portfolio_risk']}")
            print(f"  🎯 Diversification: {portfolio_advice['diversification_note']}")

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
            self._print_section_header("SEASONAL PATTERNS")
            for ticker, seasonal_data in seasonal_results.items():
                seasonal_emoji = "🌟" if "FAVORABLE" in seasonal_data.recommendation else \
                               "⚠️" if "UNFAVORABLE" in seasonal_data.recommendation else "🔄"

                bias_desc = "Strong" if seasonal_data.bias_score > 0.5 else \
                           "Moderate" if seasonal_data.bias_score > 0.2 else "Weak"

                print(f"  {seasonal_emoji} {ticker}: {bias_desc} seasonal bias "
                      f"(Score: {seasonal_data.bias_score:.2f})")
                print(f"    📈 Strong months: {', '.join(seasonal_data.best_months)}")
                print(f"    📉 Weak months: {', '.join(seasonal_data.worst_months)}")
                print(f"    💡 Pattern: {seasonal_data.seasonal_summary}")

                # Current month context
                current_month = calendar.month_name[datetime.now().month]
                if current_month in seasonal_data.best_months:
                    print(f"    🎯 Current timing: FAVORABLE ({current_month})")
                elif current_month in seasonal_data.worst_months:
                    print(f"    ⏰ Current timing: UNFAVORABLE ({current_month})")
                else:
                    print(f"    ➡️ Current timing: NEUTRAL ({current_month})")

        # Deep Analysis Summary
        if deep_results:
            self._print_section_header("BACKTESTING ACCURACY")

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
                    print(f"    ✅ High confidence in analysis accuracy - Recommendations are reliable")
                elif avg_precision > 0.5:
                    print(f"    ⚠️ Moderate confidence - Consider additional factors before investing")
                else:
                    print(f"    🚨 Low confidence - Use caution with recommendations, seek more data")

        print("\n" + "="*80)
        self._print_section_header("INVESTMENT INSIGHTS")

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
                                 if current_month in data.best_months]
            unfavorable_seasonal = [ticker for ticker, data in seasonal_results.items()
                                   if current_month in data.worst_months]

            if favorable_seasonal:
                insights.append(f"🌟 Seasonal tailwinds this month: {', '.join(favorable_seasonal)}")
            if unfavorable_seasonal:
                insights.append(f"⚠️ Seasonal headwinds this month: {', '.join(unfavorable_seasonal)}")

            # High seasonal bias stocks
            strong_seasonal = [ticker for ticker, data in seasonal_results.items()
                             if data.bias_score > 0.5]
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

    def _display_enhanced_ticker_summary(self, tickers, portfolio_advice=None, deep_results=None, technical_results=None):
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

            # Attach recent technical indicator snapshot if available
            tech_snapshot = None
            tech_signal = None
            if technical_results and ticker in technical_results:
                tech_snapshot = technical_results.get(ticker, {})
                # derive compact tech signal
                try:
                    adx = tech_snapshot.get('ADX')
                    cci = tech_snapshot.get('CCI')
                    willr = tech_snapshot.get('Williams_%R')
                    if adx is not None and adx > 25 and cci is not None and cci > 100 and willr is not None and willr > -20:
                        tech_signal = 'Bull'
                    elif adx is not None and adx > 25 and cci is not None and cci < -100 and willr is not None and willr < -80:
                        tech_signal = 'Bear'
                    elif adx is not None and adx < 20:
                        tech_signal = 'NoTrend'
                    else:
                        tech_signal = 'Neutral'
                except Exception:
                    tech_signal = None

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

            # Save tech snapshot into summary for optional use
            if tech_snapshot:
                summary['tech_snapshot'] = tech_snapshot
                summary['tech_signal'] = tech_signal

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
            tech_symbol = ''
            if summary.get('tech_signal') == 'Bull':
                tech_symbol = '↑'
            elif summary.get('tech_signal') == 'Bear':
                tech_symbol = '↓'
            elif summary.get('tech_signal') == 'NoTrend':
                tech_symbol = '↔'
            elif summary.get('tech_signal') == 'Neutral':
                tech_symbol = '•'

            ticker_display = f"{emoji} {ticker} {tech_symbol}"[:11]
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

    def full_analysis(self, ticker, period="1y", verbose=False, json_output=False):
        """
        Run all available analysis commands sequentially for a single ticker
        and return a consensus recommendation (BUY, SELL, or HOLD).

        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period for analysis
            verbose (bool): Output individual analysis results
            json_output (bool): Return results as JSON

        Returns:
            dict: Full analysis results with consensus recommendation
        """
        if not json_output:
            self._print_header(f"FULL ANALYSIS FOR {ticker}", "🎯")
            print(f"Running all available analysis commands...")
            print(f"Period: {period}")
            print()

        results = {
            'ticker': ticker,
            'period': period,
            'timestamp': datetime.now().isoformat(),
            'analyses': {},
            'consensus': None,
            'recommendations': {},
            'errors': []
        }

        total_steps = 6

        # 1. Download data first
        if not json_output:
            print(f"📥 [1/{total_steps}] Downloading data...")
        try:
            download_result = self.downloader.download_multiple_stocks([ticker], None, None, period)
            if download_result and download_result.get(ticker):
                results['analyses']['download'] = {'status': 'success'}
                if verbose and not json_output:
                    print("    ✅ Data download completed")
            else:
                results['errors'].append('Data download failed')
                if not json_output:
                    print("    ❌ Data download failed")
        except Exception as e:
            results['errors'].append(f'Download error: {str(e)}')
            if not json_output:
                print(f"    ❌ Download error: {str(e)}")

        # 2. Comprehensive Analysis
        if not json_output:
            print(f"\n🔬 [2/{total_steps}] Comprehensive analysis...")
        try:
            comp_result = self.comprehensive_analysis(
                [ticker], period, download=False,
                include_patterns=True, include_events=True,
                include_advanced_viz=False, include_options=True,
                include_investment_advice=True, include_seasonal=True,
                json_output=True
            )
            results['analyses']['comprehensive'] = comp_result

            # Extract recommendation
            if comp_result and isinstance(comp_result, dict):
                recs = comp_result.get('recommendations', {})
                if ticker in recs:
                    rec_data = recs[ticker]
                    if isinstance(rec_data, dict):
                        rec = rec_data.get('overall_recommendation', 'UNKNOWN')
                    else:
                        rec = rec_data
                    results['recommendations']['comprehensive'] = rec
                    if verbose and not json_output:
                        print(f"    ✅ Recommendation: {rec}")
                        if isinstance(rec_data, dict):
                            conf = rec_data.get('confidence_level', 'N/A')
                            print(f"       Confidence: {conf}")
        except Exception as e:
            results['errors'].append(f'Comprehensive analysis error: {str(e)}')
            if verbose and not json_output:
                print(f"    ⚠️  Comprehensive analysis error: {str(e)}")

        # 3. Seasonal Analysis
        if not json_output:
            print(f"\n🗓️  [3/{total_steps}] Seasonal analysis...")
        try:
            seasonal_result = self.seasonal_only([ticker], period="5y", download=False, json_output=True)
            results['analyses']['seasonal'] = seasonal_result

            # Extract recommendation from seasonal
            if seasonal_result and isinstance(seasonal_result, dict):
                seasonal_recs = seasonal_result.get('recommendations', {})
                if ticker in seasonal_recs:
                    results['recommendations']['seasonal'] = seasonal_recs[ticker]
                    if verbose and not json_output:
                        print(f"    ✅ Recommendation: {seasonal_recs[ticker]}")
        except Exception as e:
            results['errors'].append(f'Seasonal analysis error: {str(e)}')
            if verbose and not json_output:
                print(f"    ⚠️  Seasonal analysis error: {str(e)}")

        # 4. Multi-timeframe Analysis
        if not json_output:
            print(f"\n📊 [4/{total_steps}] Multi-timeframe analysis...")
        try:
            mtf_result = self.analyze_multi_timeframe(ticker)
            results['analyses']['multi_timeframe'] = mtf_result

            if mtf_result and 'consensus' in mtf_result:
                consensus = mtf_result['consensus']
                results['recommendations']['multi_timeframe'] = consensus
                if verbose and not json_output:
                    print(f"    ✅ Consensus: {consensus}")
                    print(f"       Confidence: {mtf_result.get('confidence', 'N/A')}")
        except Exception as e:
            results['errors'].append(f'Multi-timeframe analysis error: {str(e)}')
            if verbose and not json_output:
                print(f"    ⚠️  Multi-timeframe analysis error: {str(e)}")

        # 5. RNN Analysis (if available)
        if not json_output:
            print(f"\n� [5/{total_steps}] RNN analysis...")
        if self.rnn_analyzer:
            try:
                files = self.visualizer.find_stock_files(ticker)
                if files:
                    latest_file = max(files, key=os.path.getctime)
                    data = self.visualizer.load_stock_data(latest_file)
                    if data is not None and len(data) >= 100:
                        rnn_result = self.rnn_analyzer.analyze(data, ticker)
                        if rnn_result:
                            results['analyses']['rnn'] = {
                                'recommendation': rnn_result.recommendation.action,
                                'confidence': rnn_result.recommendation.confidence,
                                'predicted_return': rnn_result.recommendation.predicted_return_pct
                            }
                            results['recommendations']['rnn'] = rnn_result.recommendation.action
                            if verbose and not json_output:
                                print(f"    ✅ Recommendation: {rnn_result.recommendation.action}")
                                print(f"       Confidence: {rnn_result.recommendation.confidence:.1f}")
                    else:
                        if verbose and not json_output:
                            print("    ⚠️  Insufficient data for RNN analysis")
            except Exception as e:
                results['errors'].append(f'RNN analysis error: {str(e)}')
                if verbose and not json_output:
                    print(f"    ⚠️  RNN analysis error: {str(e)}")
        else:
            if verbose and not json_output:
                print("    ⚠️  RNN analyzer not available")

        # 6. Options Analysis
        if not json_output:
            print(f"\n📈 [6/{total_steps}] Options analysis...")
        try:
            options_result = self.options_analyzer.analyze_options_with_greeks(ticker)
            if options_result:
                results['analyses']['options'] = options_result
                if verbose and not json_output:
                    print(f"    ✅ Options data retrieved")
        except Exception as e:
            results['errors'].append(f'Options analysis error: {str(e)}')
            if verbose and not json_output:
                print(f"    ⚠️  Options analysis error: {str(e)}")

        # Calculate consensus recommendation
        if not json_output:
            print(f"\n🎯 Calculating consensus recommendation...")

        recommendations = results['recommendations']
        buy_count = 0
        sell_count = 0
        hold_count = 0

        for analysis_type, rec in recommendations.items():
            rec_upper = str(rec).upper()
            if 'BUY' in rec_upper or 'BULLISH' in rec_upper:
                buy_count += 1
            elif 'SELL' in rec_upper or 'BEARISH' in rec_upper:
                sell_count += 1
            elif 'HOLD' in rec_upper or 'NEUTRAL' in rec_upper:
                hold_count += 1

        total_recs = buy_count + sell_count + hold_count

        if total_recs == 0:
            consensus = 'INSUFFICIENT_DATA'
            confidence = 0
        else:
            # Determine consensus
            max_count = max(buy_count, sell_count, hold_count)
            consensus_pct = (max_count / total_recs) * 100

            if buy_count == max_count:
                consensus = 'BUY'
            elif sell_count == max_count:
                consensus = 'SELL'
            else:
                consensus = 'HOLD'

            # Determine confidence
            if consensus_pct >= 75:
                confidence = 'HIGH'
            elif consensus_pct >= 60:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'

        results['consensus'] = {
            'recommendation': consensus,
            'confidence': confidence,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'hold_count': hold_count,
            'total_analyses': total_recs,
            'agreement_pct': round((max_count / total_recs * 100) if total_recs > 0 else 0, 1)
        }

        # Output results
        if json_output:
            return results
        else:
            # Format sub-recommendations for display
            sub_recs = []
            for analysis_type, rec in sorted(recommendations.items()):
                sub_recs.append(f"{analysis_type}: {rec}")
            sub_recs_str = ", ".join(sub_recs)

            print("\n" + "=" * 70)
            self._print_header(f"CONSENSUS RECOMMENDATION FOR {ticker}", "🎯")
            print(f"\n{consensus} ({sub_recs_str})")
            print(f"\nConfidence: {confidence} ({results['consensus']['agreement_pct']:.1f}% agreement)")
            print(f"Summary: {buy_count} BUY, {sell_count} SELL, {hold_count} HOLD")

            if results['errors']:
                print("\n⚠️  Warnings/Errors:")
                for error in results['errors']:
                    print(f"  - {error}")

            print("=" * 70)
            self._print_success(f"Full analysis completed for {ticker}!")

            return results


# Legacy class for backward compatibility
class StockAnalysis(AdvancedStockAnalysis):
    def quick_analysis(self, tickers, period="1y", download=True, visualize=True, json_output=False):
        """Legacy quick analysis method."""
        result = {
            "command": "quick",
            "tickers": [ticker.upper() for ticker in tickers],
            "period": period,
            "download": download,
            "visualize": visualize,
            "download_results": {},
            "visualizations": {
                "single_charts": {},
                "comparison_chart": None,
                "correlation_matrix": None,
            },
            "errors": [],
        }

        if not json_output:
            self._print_header("QUICK STOCK ANALYSIS")
            print(f"📈 Tickers: {', '.join(tickers)}")
            print(f"⏰ Period: {period}")
            print()

        # Download data if requested
        if download:
            if not json_output:
                self._print_section_header("DOWNLOADING STOCK DATA")
                download_results = self.downloader.download_multiple_stocks(
                    tickers, None, None, period
                )
            else:
                with contextlib.redirect_stdout(io.StringIO()):
                    download_results = self.downloader.download_multiple_stocks(
                        tickers, None, None, period
                    )
            result["download_results"] = download_results or {}

            if not download_results:
                error_message = "No data downloaded. Exiting."
                result["errors"].append(error_message)
                if json_output:
                    return result
                self._print_error(error_message)
                return

            if not json_output:
                self._print_success("Data download completed!")

        # Create visualizations if requested
        if visualize:
            if not json_output:
                self._print_section_header("CREATING VISUALIZATIONS")

            # Individual charts for each stock
            for ticker in tickers:
                if not json_output:
                    print(f"  Creating chart for {ticker}...")
                    chart_path = self.visualizer.plot_single_stock(ticker, save=True, show=False)
                else:
                    with contextlib.redirect_stdout(io.StringIO()):
                        chart_path = self.visualizer.plot_single_stock(ticker, save=True, show=False)
                result["visualizations"]["single_charts"][ticker.upper()] = chart_path

            # Comparison chart if multiple stocks
            if len(tickers) > 1:
                if not json_output:
                    print(f"  Creating comparison chart...")
                    comparison_path = self.visualizer.plot_comparison(tickers, save=True, show=False)
                    print(f"  Creating correlation matrix...")
                    correlation_path = self.visualizer.create_correlation_matrix(tickers, save=True, show=False)
                else:
                    with contextlib.redirect_stdout(io.StringIO()):
                        comparison_path = self.visualizer.plot_comparison(tickers, save=True, show=False)
                        correlation_path = self.visualizer.create_correlation_matrix(tickers, save=True, show=False)
                result["visualizations"]["comparison_chart"] = comparison_path
                result["visualizations"]["correlation_matrix"] = correlation_path

            if not json_output:
                self._print_success("Visualizations completed!")

        result["data_dir"] = f"{self.downloader.data_dir}/"
        result["graphs_dir"] = f"{self.visualizer.output_dir}/"
        result["status"] = "error" if result["errors"] else "ok"

        if json_output:
            return result

        self._print_success("Analysis completed!")
        print(f"📁 Data files: {self.downloader.data_dir}/")
        print(f"📊 Charts: {self.visualizer.output_dir}/")

    def show_stock_info(self, tickers, json_output=False):
        """Display information about stocks."""
        result = {"command": "info", "tickers": tickers, "info": {}}

        for ticker in tickers:
            info = self.downloader.get_stock_info(ticker)
            if info:
                result["info"][ticker.upper()] = info
            else:
                result["info"][ticker.upper()] = None

        if json_output:
            return result
        else:
            self._print_header("STOCK INFORMATION")
            for ticker in tickers:
                info = result["info"][ticker.upper()]
                if info:
                    print(f"\n{ticker.upper()} - {info['longName']}")
                    print(f"  Sector: {info['sector']}")
                    print(f"  Industry: {info['industry']}")
                    print(f"  Market Cap: {info['marketCap']}")
                    print(f"  Currency: {info['currency']}")
                else:
                    self._print_error(f"Unable to fetch information for {ticker.upper()}")

    def list_available_data(self, json_output=False):
        """List all available data files."""
        files = self.visualizer.find_stock_files()
        if json_output:
            result = []
            if files:
                for file in sorted(files):
                    ticker = self.visualizer.extract_ticker_from_filename(file)
                    file_size = os.path.getsize(file) / 1024  # KB
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file))
                    result.append({
                        "ticker": ticker.upper(),
                        "filename": os.path.basename(file),
                        "size_kb": round(file_size, 1),
                        "modified": mod_time.strftime('%Y-%m-%d %H:%M')
                    })
            return result
        else:
            self._print_header("AVAILABLE DATA FILES")
            if files:
                for file in sorted(files):
                    ticker = self.visualizer.extract_ticker_from_filename(file)
                    file_size = os.path.getsize(file) / 1024  # KB
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file))
                    print(f"  {ticker.upper()}: {os.path.basename(file)} ({file_size:.1f} KB, {mod_time.strftime('%Y-%m-%d %H:%M')})")
            else:
                self._print_warning("No data files found.")

    def full_analysis(self, ticker, period="1y", verbose=False, json_output=False):
        """
        Run all available analysis commands sequentially for a single ticker
        and return a consensus recommendation (BUY, SELL, or HOLD).

        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period for analysis
            verbose (bool): Output individual analysis results
            json_output (bool): Return results as JSON

        Returns:
            dict: Full analysis results with consensus recommendation
        """
        if not json_output:
            self._print_header(f"FULL ANALYSIS FOR {ticker}", "🎯")
            print(f"Running all available analysis commands...")
            print(f"Period: {period}")
            print(f"Verbose: {verbose}")
            print()

        results = {
            'ticker': ticker,
            'period': period,
            'timestamp': datetime.now().isoformat(),
            'analyses': {},
            'consensus': None,
            'recommendations': {},
            'errors': []
        }

        # 1. Download data first
        if not json_output:
            print("📥 Step 1/8: Downloading data...")
        try:
            download_result = self.downloader.download_multiple_stocks([ticker], None, None, period)
            if download_result and download_result.get(ticker):
                results['analyses']['download'] = {'status': 'success'}
                if verbose and not json_output:
                    print("✅ Data download completed")
            else:
                results['errors'].append('Data download failed')
                if not json_output:
                    self._print_error("Data download failed")
        except Exception as e:
            results['errors'].append(f'Download error: {str(e)}')
            if not json_output:
                self._print_error(f"Download error: {str(e)}")

        # 2. Comprehensive Analysis
        if not json_output:
            print("\n🔬 Step 2/8: Running comprehensive analysis...")
        try:
            comp_result = self.comprehensive_analysis(
                [ticker], period, download=False,
                include_patterns=True, include_events=True,
                include_advanced_viz=False, include_options=True,
                include_investment_advice=True, include_seasonal=True,
                json_output=True
            )
            results['analyses']['comprehensive'] = comp_result

            # Extract recommendation
            if comp_result and isinstance(comp_result, dict):
                recs = comp_result.get('recommendations', {})
                if ticker in recs:
                    rec_data = recs[ticker]
                    if isinstance(rec_data, dict):
                        rec = rec_data.get('overall_recommendation', 'UNKNOWN')
                    else:
                        rec = rec_data
                    results['recommendations']['comprehensive'] = rec
                    if verbose and not json_output:
                        print(f"  Recommendation: {rec}")
                        if isinstance(rec_data, dict):
                            conf = rec_data.get('confidence_level', 'N/A')
                            print(f"  Confidence: {conf}")
        except Exception as e:
            results['errors'].append(f'Comprehensive analysis error: {str(e)}')
            if verbose and not json_output:
                self._print_warning(f"Comprehensive analysis error: {str(e)}")

        # 3. Seasonal Analysis
        if not json_output:
            print("\n🗓️ Step 3/8: Running seasonal analysis...")
        try:
            seasonal_result = self.seasonal_only([ticker], period="5y", download=False, json_output=True)
            results['analyses']['seasonal'] = seasonal_result

            # Extract recommendation from seasonal
            if seasonal_result and isinstance(seasonal_result, dict):
                seasonal_recs = seasonal_result.get('recommendations', {})
                if ticker in seasonal_recs:
                    results['recommendations']['seasonal'] = seasonal_recs[ticker]
                    if verbose and not json_output:
                        print(f"  Recommendation: {seasonal_recs[ticker]}")
        except Exception as e:
            results['errors'].append(f'Seasonal analysis error: {str(e)}')
            if verbose and not json_output:
                self._print_warning(f"Seasonal analysis error: {str(e)}")

        # 4. Pattern Analysis
        if not json_output:
            print("\n🔍 Step 4/8: Running pattern analysis...")
        try:
            files = self.visualizer.find_stock_files(ticker)
            if files:
                latest_file = max(files, key=os.path.getctime)
                data = self.visualizer.load_stock_data(latest_file)
                if data is not None:
                    pattern_result = self.pattern_analyzer.detect_patterns({ticker: data})
                    results['analyses']['patterns'] = pattern_result
                    if verbose and not json_output:
                        if pattern_result and ticker in pattern_result:
                            patterns = pattern_result[ticker]
                            print(f"  Patterns detected: {len(patterns)} patterns")
        except Exception as e:
            results['errors'].append(f'Pattern analysis error: {str(e)}')
            if verbose and not json_output:
                self._print_warning(f"Pattern analysis error: {str(e)}")

        # 5. Multi-timeframe Analysis
        if not json_output:
            print("\n📊 Step 5/8: Running multi-timeframe analysis...")
        try:
            mtf_result = self.analyze_multi_timeframe(ticker)
            results['analyses']['multi_timeframe'] = mtf_result

            if mtf_result and 'consensus' in mtf_result:
                consensus = mtf_result['consensus']
                results['recommendations']['multi_timeframe'] = consensus
                if verbose and not json_output:
                    print(f"  Consensus: {consensus}")
                    print(f"  Confidence: {mtf_result.get('confidence', 'N/A')}")
        except Exception as e:
            results['errors'].append(f'Multi-timeframe analysis error: {str(e)}')
            if verbose and not json_output:
                self._print_warning(f"Multi-timeframe analysis error: {str(e)}")

        # 6. ML Analysis (if available)
        if not json_output:
            print("\n🤖 Step 6/8: Running ML analysis...")
        if self.ml_analyzer:
            try:
                files = self.visualizer.find_stock_files(ticker)
                if files:
                    latest_file = max(files, key=os.path.getctime)
                    data = self.visualizer.load_stock_data(latest_file)
                    if data is not None and len(data) >= 100:
                        ml_result = self.ml_analyzer.analyze(data, ticker)
                        if ml_result:
                            results['analyses']['ml'] = {
                                'recommendation': ml_result.recommendation.action,
                                'confidence': ml_result.recommendation.confidence,
                                'predicted_return': ml_result.recommendation.predicted_return_pct,
                                'risk_score': ml_result.recommendation.risk_score
                            }
                            results['recommendations']['ml'] = ml_result.recommendation.action
                            if verbose and not json_output:
                                print(f"  Recommendation: {ml_result.recommendation.action}")
                                print(f"  Confidence: {ml_result.recommendation.confidence:.1f}")
                    else:
                        if verbose and not json_output:
                            print("  Insufficient data for ML analysis")
            except Exception as e:
                results['errors'].append(f'ML analysis error: {str(e)}')
                if verbose and not json_output:
                    self._print_warning(f"ML analysis error: {str(e)}")
        else:
            if verbose and not json_output:
                print("  ML analyzer not available")

        # 7. RNN Analysis (if available)
        if not json_output:
            print("\n🧠 Step 7/8: Running RNN analysis...")
        if self.rnn_analyzer:
            try:
                files = self.visualizer.find_stock_files(ticker)
                if files:
                    latest_file = max(files, key=os.path.getctime)
                    data = self.visualizer.load_stock_data(latest_file)
                    if data is not None and len(data) >= 100:
                        rnn_result = self.rnn_analyzer.analyze(data, ticker)
                        if rnn_result:
                            results['analyses']['rnn'] = {
                                'recommendation': rnn_result.recommendation.action,
                                'confidence': rnn_result.recommendation.confidence,
                                'predicted_return': rnn_result.recommendation.predicted_return_pct
                            }
                            results['recommendations']['rnn'] = rnn_result.recommendation.action
                            if verbose and not json_output:
                                print(f"  Recommendation: {rnn_result.recommendation.action}")
                                print(f"  Confidence: {rnn_result.recommendation.confidence:.1f}")
                    else:
                        if verbose and not json_output:
                            print("  Insufficient data for RNN analysis")
            except Exception as e:
                results['errors'].append(f'RNN analysis error: {str(e)}')
                if verbose and not json_output:
                    self._print_warning(f"RNN analysis error: {str(e)}")
        else:
            if verbose and not json_output:
                print("  RNN analyzer not available")

        # 8. Options Analysis
        if not json_output:
            print("\n📈 Step 8/8: Running options analysis...")
        try:
            options_result = self.options_analyzer.analyze_options_with_greeks(ticker)
            if options_result:
                results['analyses']['options'] = options_result
                if verbose and not json_output:
                    print(f"  Options data retrieved")
        except Exception as e:
            results['errors'].append(f'Options analysis error: {str(e)}')
            if verbose and not json_output:
                self._print_warning(f"Options analysis error: {str(e)}")

        # Calculate consensus recommendation
        if not json_output:
            print("\n🎯 Calculating consensus recommendation...")

        recommendations = results['recommendations']
        buy_count = 0
        sell_count = 0
        hold_count = 0

        for analysis_type, rec in recommendations.items():
            rec_upper = str(rec).upper()
            if 'BUY' in rec_upper or 'BULLISH' in rec_upper:
                buy_count += 1
            elif 'SELL' in rec_upper or 'BEARISH' in rec_upper:
                sell_count += 1
            elif 'HOLD' in rec_upper or 'NEUTRAL' in rec_upper:
                hold_count += 1

        total_recs = buy_count + sell_count + hold_count

        if total_recs == 0:
            consensus = 'INSUFFICIENT_DATA'
            confidence = 0
        else:
            # Determine consensus
            max_count = max(buy_count, sell_count, hold_count)
            consensus_pct = (max_count / total_recs) * 100

            if buy_count == max_count:
                consensus = 'BUY'
            elif sell_count == max_count:
                consensus = 'SELL'
            else:
                consensus = 'HOLD'

            # Determine confidence
            if consensus_pct >= 75:
                confidence = 'HIGH'
            elif consensus_pct >= 60:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'

        results['consensus'] = {
            'recommendation': consensus,
            'confidence': confidence,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'hold_count': hold_count,
            'total_analyses': total_recs,
            'agreement_pct': round((max_count / total_recs * 100) if total_recs > 0 else 0, 1)
        }

        # Output results
        if json_output:
            return results
        else:
            print("\n" + "=" * 60)
            self._print_header(f"CONSENSUS RECOMMENDATION FOR {ticker}", "🎯")
            print(f"{'Recommendation:':<20} {consensus}")
            print(f"{'Confidence:':<20} {confidence}")
            print(f"{'Agreement:':<20} {results['consensus']['agreement_pct']:.1f}%")
            print()
            print(f"{'Analysis Type':<25} {'Recommendation':<15}")
            print("-" * 50)
            for analysis_type, rec in recommendations.items():
                print(f"{analysis_type.capitalize():<25} {rec:<15}")
            print()
            print(f"Summary: {buy_count} BUY, {sell_count} SELL, {hold_count} HOLD")

            if results['errors']:
                print("\n⚠️  Warnings/Errors:")
                for error in results['errors']:
                    print(f"  - {error}")

            print("\n" + "=" * 60)
            self._print_success(f"Full analysis completed for {ticker}!")

            return results


def main():
    parser = argparse.ArgumentParser(
        description=f'{Fore.CYAN}ClariFi: Clarify your Finances{Style.RESET_ALL}\n'
                   f'{Fore.GREEN}Advanced Market Intelligence & Pattern Analysis Tool{Style.RESET_ALL}\n\n'
                   f'Orchestrates stock data downloading and comprehensive financial analysis.\n'
                   f'Provides an easy-to-use interface for stock analysis with seasonal patterns,\n'
                   f'event correlation, options analysis, and investment suggestions.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Fore.YELLOW}EXAMPLES:{Style.RESET_ALL}

{Fore.GREEN}QUICK ANALYSIS:{Style.RESET_ALL}
  ./clarifi.sh quick PLTR QBTS
  ./clarifi.sh quick AAPL MSFT --period 6mo

{Fore.GREEN}FULL ANALYSIS:{Style.RESET_ALL}
  ./clarifi.sh full AAPL
  ./clarifi.sh full AAPL --period 6mo --verbose

{Fore.GREEN}COMPREHENSIVE ANALYSIS:{Style.RESET_ALL}
  ./clarifi.sh analyze PLTR QBTS AAPL --period 1y
  ./clarifi.sh analyze "SAAB B" NANEXA --period 6mo --no-events
  ./clarifi.sh analyze AAPL --no-patterns --no-advanced-viz

{Fore.GREEN}PATTERN ANALYSIS:{Style.RESET_ALL}
  ./clarifi.sh patterns AAPL MSFT GOOGL --period 2y

{Fore.GREEN}EVENT CORRELATION:{Style.RESET_ALL}
  ./clarifi.sh events PLTR QBTS --period 1y

{Fore.GREEN}LIVE MONITORING:{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}(Experimental){Style.RESET_ALL}
  ./clarifi.sh live AAPL MSFT TSLA
  ./clarifi.sh live PLTR --interval 10

{Fore.GREEN}MARKET SCREENING:{Style.RESET_ALL}
  ./clarifi.sh screen gainers
  ./clarifi.sh screen losers --limit 10

{Fore.GREEN}SEASONAL ANALYSIS:{Style.RESET_ALL}
  ./clarifi.sh seasonal AAPL MSFT --period 5y

{Fore.GREEN}AI ANALYSIS:{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}(Requires Ollama or compatible LLM){Style.RESET_ALL}
  ./clarifi.sh ai AAPL MSFT --period 6mo
  ./clarifi.sh ai PLTR --show-prompt

{Fore.GREEN}PORTFOLIO MANAGEMENT:{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}(Optional feature){Style.RESET_ALL}
  ./clarifi.sh portfolio create --name MyPortfolio
  ./clarifi.sh portfolio list
  ./clarifi.sh portfolio add <portfolio_id> AAPL --quantity 10

{Fore.BLUE}TIP:{Style.RESET_ALL} Use quotes for tickers with spaces: "SAAB B"

{Fore.RED}DISCLAIMER:{Style.RESET_ALL} This tool is for educational and research purposes only and does NOT constitute financial advice.
        """
    )

    # Global --json flag
    parser.add_argument('--json', action='store_true', help='Output results in JSON format only')

    subparsers = parser.add_subparsers(dest='command', help='Analysis Commands')

    # Legacy quick analysis
    quick_parser = subparsers.add_parser('quick', help='Quick basic analysis (legacy)')
    quick_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    quick_parser.add_argument('--period', '-p', default='1y', help='Time period (default: 1y)')
    quick_parser.add_argument('--no-download', action='store_true', help='Skip downloading')
    quick_parser.add_argument('--no-visualize', action='store_true', help='Skip visualization')

    # NEW: Full analysis with consensus recommendation
    full_parser = subparsers.add_parser('full', help='Run all analyses and generate consensus recommendation')
    full_parser.add_argument('ticker', help='Stock ticker symbol (single ticker only)')
    full_parser.add_argument('--period', '-p', default='1y', help='Time period (default: 1y)')
    full_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output from each analysis')

    # NEW: Comprehensive analysis
    analyze_parser = subparsers.add_parser('analyze', help='Comprehensive market analysis')
    analyze_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols or portfolio ID')
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
    analyze_parser.add_argument('--include-ml', action='store_true', help='Include machine learning analysis')
    analyze_parser.add_argument('--summary-only', action='store_true', help='Print only summary recommendations')

    # AI analysis (LLM powered)
    ai_parser = subparsers.add_parser(
        'ai',
        help='AI-driven quantitative + LLM recommendations (BUY/SELL/HOLD)',
        description='Run quantitative factor extraction + optional local LLM synthesis to produce BUY/SELL/HOLD signals.',
        epilog=(
            "Examples:\n"
            "  ./clarifi.sh ai AAPL MSFT --period 6mo\n"
            "  ./clarifi.sh ai AAPL --show-prompt\n"
            "  ./clarifi.sh ai PLTR TSLA --no-llm (quant metrics only)\n"
            "  ./clarifi.sh ai <portfolio_id> --period 1y\n\n"
            "Metrics included: avg daily return, annualized vol, max drawdown, SMA(50/200) relationship, RSI(14), simple SMA crossover backtest (strategy vs buy&hold), 30‑day trend slope classification.\n"
            "LLM Prompt: A compact JSON-oriented instruction asking model to emit structured recommendations."
        )
    )
    ai_parser.add_argument('tickers', nargs='+', help='One or more stock tickers or a single portfolio ID')
    ai_parser.add_argument('--period', '-p', default='1y', help='Historical period to fetch (default: 1y)')
    ai_parser.add_argument('--no-llm', action='store_true', help='Skip calling the LLM (quant metrics only)')
    ai_parser.add_argument('--show-prompt', action='store_true', help='Print the generated LLM prompt for transparency')
    ai_parser.add_argument('--raw-json', action='store_true', help='Print raw JSON response from AI and final prompt')
    ai_parser.add_argument('--combined', action='store_true', help='Run comprehensive analysis first and combine with AI recommendations')
    ai_parser.add_argument('--summary-only', action='store_true', help='Only print condensed BUY/SELL/HOLD table')
    ai_parser.add_argument('--model', default='qwen3:latest', help='Ollama model name (default: qwen3:latest)')

    # Seasonal analysis
    seasonal_parser = subparsers.add_parser('seasonal', help='🗓️ Seasonal & holiday analysis')
    seasonal_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    seasonal_parser.add_argument('--period', '-p', default='5y', help='Time period (default: 5y for better patterns)')
    seasonal_parser.add_argument('--no-download', action='store_true', help='Skip downloading fresh data')

    # Strategy recommendation
    strategy_parser = subparsers.add_parser(
        'strategy',
        help='🎯 Generate time-sensitive investment strategy',
        description='Analyze a ticker using multiple timeframes, seasonal patterns, backtesting, and technical indicators to suggest actionable strategies like "BUY now and SELL in 2 days" or "HOLD for 2 months".',
        epilog=(
            "Examples:\n"
            "  ./clarifi.sh strategy AAPL --period 1y\n"
            "  ./clarifi.sh strategy TSLA --period 2y --include-deep\n"
            "  ./clarifi.sh strategy MSFT --period 6mo --no-download\n\n"
            "The strategy command runs comprehensive analysis including:\n"
            "  - Multi-timeframe trend analysis (short/medium/long-term)\n"
            "  - Seasonal patterns and holiday effects\n"
            "  - Deep backtesting with multiple periods (if --include-deep)\n"
            "  - Technical indicators (RSI, MACD, Moving Averages)\n"
            "  - Risk metrics (volatility, drawdown, Sharpe ratio)\n"
            "  - Optimal timeframe determination based on historical performance\n"
        )
    )
    strategy_parser.add_argument('ticker', help='Stock ticker symbol (single ticker only)')
    strategy_parser.add_argument('--period', '-p', default='1y', help='Time period for analysis (default: 1y, recommended: 2y+)')
    strategy_parser.add_argument('--no-download', action='store_true', help='Skip downloading fresh data')
    strategy_parser.add_argument('--include-deep', action='store_true', help='Include deep backtesting analysis for higher confidence')
    strategy_parser.add_argument('--deep-chunk-months', type=int, default=3, help='Chunk size in months for deep analysis (default: 3)')
    strategy_parser.add_argument('--optimum', action='store_true', help='Find optimal buy/sell moment based on all analysis data')

    suggest_parser = subparsers.add_parser(
        'suggest',
        help='📈 Suggest short-term ticker candidates using free market signals',
        description='Scan a ticker universe and rank candidates using momentum, volume checks, and analyst bias.',
    )
    suggest_parser.add_argument('tickers', nargs='*', help='Optional explicit ticker list; otherwise uses the built-in universe')
    suggest_parser.add_argument('--limit', type=int, default=10, help='Maximum number of suggestions to show (default: 10)')
    suggest_parser.add_argument('--min-score', type=float, default=55.0, help='Minimum composite score threshold (default: 55.0)')

    # ML analysis
    ml_parser = subparsers.add_parser('ml_analyze', help='Machine Learning analysis with Random Forest, XGBoost, LightGBM')
    ml_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    ml_parser.add_argument('--period', '-p', default='2y', help='Time period (default: 2y for ML training)')
    ml_parser.add_argument('--horizon', type=int, default=5, help='Prediction horizon in days (default: 5)')
    ml_parser.add_argument('--no-download', action='store_true', help='Skip downloading fresh data')
    ml_parser.add_argument('--models', nargs='+', choices=['random_forest', 'xgboost', 'lightgbm'],
                          default=['random_forest', 'xgboost', 'lightgbm'], help='ML models to use')

    # RNN analysis
    rnn_parser = subparsers.add_parser('rnn', help='Recurrent Neural Network analysis with LSTM/GRU')
    rnn_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    rnn_parser.add_argument('--period', '-p', default='2y', help='Time period (default: 2y for RNN training)')
    rnn_parser.add_argument('--horizon', type=int, default=5, help='Prediction horizon in days (default: 5)')
    rnn_parser.add_argument('--no-download', action='store_true', help='Skip downloading fresh data')
    rnn_parser.add_argument('--models', nargs='+', choices=['lstm', 'gru', 'bidirectional_lstm', 'bidirectional_gru'],
                           default=['lstm', 'gru'], help='RNN models to use')

    # Transformer analysis
    transformer_parser = subparsers.add_parser('transformer', help='Transformer-based analysis with TFT and attention mechanisms')
    transformer_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    transformer_parser.add_argument('--period', '-p', default='2y', help='Time period (default: 2y for transformer training)')
    transformer_parser.add_argument('--horizon', type=int, default=5, help='Prediction horizon in days (default: 5)')
    transformer_parser.add_argument('--no-download', action='store_true', help='Skip downloading fresh data')
    transformer_parser.add_argument('--models', nargs='+', choices=['tft', 'transformer_encoder', 'conv_transformer'],
                                   default=['tft'], help='Transformer models to use')

    # RL analysis
    rl_parser = subparsers.add_parser('rl', help='Reinforcement Learning analysis with Q-Learning and PPO')
    rl_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    rl_parser.add_argument('--period', '-p', default='2y', help='Time period (default: 2y for RL training)')
    rl_parser.add_argument('--no-download', action='store_true', help='Skip downloading fresh data')
    rl_parser.add_argument('--models', nargs='+', choices=['q_learning', 'ppo', 'dqn'],
                          default=['ppo'], help='RL algorithms to use')
    rl_parser.add_argument('--episodes', type=int, default=1000, help='Number of training episodes (default: 1000)')
    rl_parser.add_argument('--backtest', action='store_true', help='Run backtesting after training')

    # Pattern analysis
    patterns_parser = subparsers.add_parser('patterns', help='Advanced pattern analysis')
    patterns_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    patterns_parser.add_argument('--period', '-p', default='1y', help='Time period')
    patterns_parser.add_argument('--window', '-w', type=int, default=30, help='Rolling window size')

    # Correlation analysis
    corr_parser = subparsers.add_parser('correlations', help='Correlation analysis')
    corr_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols (min 2)')
    corr_parser.add_argument('--period', '-p', default='1y', help='Time period')
    corr_parser.add_argument('--window', '-w', type=int, default=30, help='Rolling window size')

    # Event correlation
    events_parser = subparsers.add_parser('events', help='Event correlation analysis')
    events_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    events_parser.add_argument('--period', '-p', default='1y', help='Time period')
    events_parser.add_argument('--lookback', type=int, default=5, help='Days before event')
    events_parser.add_argument('--lookahead', type=int, default=5, help='Days after event')

    # Volatility analysis
    vol_parser = subparsers.add_parser('volatility', help='Volatility clustering analysis')
    vol_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    vol_parser.add_argument('--period', '-p', default='1y', help='Time period')
    vol_parser.add_argument('--window', '-w', type=int, default=20, help='Volatility window')
    vol_parser.add_argument('--clustering', action='store_true', help='Create clustering plots')

    # Download command
    download_parser = subparsers.add_parser('download', help='Download stock data')
    download_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    download_parser.add_argument('--start', '-s', help='Start date (YYYY-MM-DD)')
    download_parser.add_argument('--end', '-e', help='End date (YYYY-MM-DD)')
    download_parser.add_argument('--period', '-p', help='Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)')

    # Visualize command
    viz_parser = subparsers.add_parser('visualize', help='Create visualizations')
    viz_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    viz_parser.add_argument('--single', action='store_true', help='Individual charts only')
    viz_parser.add_argument('--compare', action='store_true', help='Comparison chart')
    viz_parser.add_argument('--correlation', action='store_true', help='Correlation matrix')
    viz_parser.add_argument('--support-resistance', action='store_true', help='Support/resistance levels')
    viz_parser.add_argument('--metric', default='Close', help='Metric to plot (default: Close)')
    viz_parser.add_argument('--show', action='store_true', help='Show plots instead of saving')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show stock information')
    info_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')

    # List command
    list_parser = subparsers.add_parser('list', help='List available data files')

    # Live monitoring command
    live_parser = subparsers.add_parser('live', help='Live real-time stock monitoring')
    live_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols to monitor')
    live_parser.add_argument('--interval', '-i', type=int, default=5, help='Update interval in seconds (default: 5)')
    live_parser.add_argument('--no-graphs', action='store_true', help='Disable terminal graphs')
    live_parser.add_argument('--no-summary', action='store_true', help='Disable summary table')

    # Stock screener command
    screener_parser = subparsers.add_parser('screen', help='Market screening for gainers, losers, and new listings')
    screener_parser.add_argument('category', choices=['gainers', 'losers', 'actives', 'new'],
                                help='Screening category: gainers, losers, actives, or new')
    screener_parser.add_argument('--limit', '-l', type=int, default=20,
                                help='Number of results to return (default: 20)')
    screener_parser.add_argument('--export', '-e', help='Export results to CSV file')

    # Prune command
    prune_parser = subparsers.add_parser('prune', help='🗑️ Interactive cleanup of data, graphs, and models to save space')

    # Portfolio management (grouped subcommands)
    portfolio_parser = subparsers.add_parser('portfolio', help='Portfolio management commands (create, list, info, add, update-ticker, update, sync, delete, remove, tickers, analyze)')
    port_sub = portfolio_parser.add_subparsers(dest='portfolio_cmd', help='Portfolio Commands')

    # portfolio create
    p_create = port_sub.add_parser('create', help='Create a new portfolio')
    p_create.add_argument('--name', '-n', required=True, help='Portfolio name (unique)')
    p_create.add_argument('--description', '-d', default='', help='Portfolio description')

    # portfolio list
    p_list = port_sub.add_parser('list', help='List all portfolios')

    # portfolio info
    p_info = port_sub.add_parser('info', help='Get comprehensive portfolio information with current prices and analytics')
    p_info.add_argument('portfolio_id', help='Portfolio ID or name')
    p_info.add_argument('--analytics', action='store_true', help='Include advanced analytics and insights')

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
    p_analyze.add_argument('--include-deep', action='store_true', help='Include deep backtesting analysis')
    p_analyze.add_argument('--deep-chunk-months', type=int, default=3, help='Chunk size in months for deep analysis (default: 3)')
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

    # Alpha Vantage API commands
    av_parser = subparsers.add_parser('av', help='📡 Alpha Vantage API integration for financial data and news sentiment')
    av_sub = av_parser.add_subparsers(dest='av_command', help='Alpha Vantage Commands')

    # av news-sentiment
    av_news = av_sub.add_parser('news-sentiment', help='📰 Get news sentiment analysis from Alpha Vantage')
    av_news.add_argument('tickers', nargs='*', help='Stock ticker symbols to filter news (optional)')
    av_news.add_argument('--topics', '-t', nargs='+', help='Topics to filter news (e.g., technology, finance)')
    av_news.add_argument('--time-from', help='Start date in YYYYMMDDTHHMM format')
    av_news.add_argument('--time-to', help='End date in YYYYMMDDTHHMM format')
    av_news.add_argument('--sort', choices=['LATEST', 'EARLIEST', 'RELEVANCE'], default='LATEST', help='Sort order (default: LATEST)')
    av_news.add_argument('--limit', type=int, default=50, help='Maximum number of news items (default: 50)')
    av_news.add_argument('--analyze', action='store_true', help='Include sentiment trend analysis')

    # av overview
    av_overview = av_sub.add_parser('overview', help='📊 Get company overview data')
    av_overview.add_argument('symbol', help='Stock ticker symbol')

    # av quote
    av_quote = av_sub.add_parser('quote', help='💰 Get real-time quote data')
    av_quote.add_argument('symbol', help='Stock ticker symbol')

    # av income-statement
    av_income = av_sub.add_parser('income-statement', help='💼 Get income statement data')
    av_income.add_argument('symbol', help='Stock ticker symbol')
    av_income.add_argument('--annual', action='store_true', help='Get annual data (default)')
    av_income.add_argument('--quarterly', action='store_true', help='Get quarterly data')

    # av balance-sheet
    av_balance = av_sub.add_parser('balance-sheet', help='🏦 Get balance sheet data')
    av_balance.add_argument('symbol', help='Stock ticker symbol')
    av_balance.add_argument('--annual', action='store_true', help='Get annual data (default)')
    av_balance.add_argument('--quarterly', action='store_true', help='Get quarterly data')

    # av cash-flow
    av_cashflow = av_sub.add_parser('cash-flow', help='💵 Get cash flow statement data')
    av_cashflow.add_argument('symbol', help='Stock ticker symbol')
    av_cashflow.add_argument('--annual', action='store_true', help='Get annual data (default)')
    av_cashflow.add_argument('--quarterly', action='store_true', help='Get quarterly data')

    # av earnings
    av_earnings = av_sub.add_parser('earnings', help='📈 Get earnings data')
    av_earnings.add_argument('symbol', help='Stock ticker symbol')

    # av top-gainers-losers
    av_gainers_losers = av_sub.add_parser('top-gainers-losers', help='📊 Get top gainers, losers, and most actively traded tickers')
    av_gainers_losers.add_argument('--format', choices=['table', 'json'], default='table', help='Output format (default: table)')

    # Event ingestion command
    ingest_parser = subparsers.add_parser('ingest', help='📥 Ingest event data from JSON files')
    ingest_parser.add_argument('--file', '-f', help='Path to a specific JSON file to import')
    ingest_parser.add_argument('--ingest-dir', '-i', default='ingest', help='Directory containing JSON files (default: ingest)')
    ingest_parser.add_argument('--ingested-dir', '-o', default='ingested', help='Directory for processed files (default: ingested)')
    ingest_parser.add_argument('--process', action='store_true', help='Process all files in ingest folder once')
    ingest_parser.add_argument('--monitor', action='store_true', help='Monitor ingest folder continuously')
    ingest_parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds (default: 60)')
    ingest_parser.add_argument('--no-skip-duplicates', action='store_true', help='Do not skip duplicate events')

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
            from core.engine import ClariFiEngine  # when package is recognized
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
    except sqlite3.DatabaseError as e:
        db_path = os.environ.get("CLARIFI_DB_PATH", "clarifi.db")
        print(f"❌ Error initializing analysis tools: {e}")
        print(f"💡 SQLite database '{db_path}' is corrupted. Run these commands from the project root:")
        print(f"   cp -p '{db_path}' '{db_path}.corrupt.$(date +%Y%m%d-%H%M%S)'")
        print(f"   sqlite3 '{db_path}' '.recover' | sqlite3 '{db_path}.recovered'")
        print(f"   sqlite3 '{db_path}.recovered' 'PRAGMA integrity_check;'")
        print(f"   mv '{db_path}' '{db_path}.broken' && mv '{db_path}.recovered' '{db_path}'")
        print("   Re-run this command after the recovered database reports 'ok'.")
        return
    except Exception as e:
        print(f"❌ Error initializing analysis tools: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        return

    try:
        if args.command == 'quick':
            result = legacy_analysis.quick_analysis(
                args.tickers,
                args.period,
                download=not args.no_download,
                visualize=not args.no_visualize,
                json_output=getattr(args, 'json', False)
            )
            if getattr(args, 'json', False):
                import json
                print(json.dumps(result, indent=2))

        elif args.command == 'full':
            # Full analysis with consensus recommendation
            result = analysis.full_analysis(
                args.ticker,
                period=args.period,
                verbose=args.verbose,
                json_output=getattr(args, 'json', False)
            )
            if getattr(args, 'json', False):
                import json
                print(json.dumps(result, indent=2))

        elif args.command == 'analyze':
            # Lazy initialize engine if needed for portfolio lookup
            if engine is None:
                try:
                    from core.engine import ClariFiEngine  # when package is recognized
                except ImportError:
                    try:
                        from engine import ClariFiEngine  # local module import
                    except ImportError:
                        print("❌ ClariFiEngine not available. Running legacy analysis instead.")
                        # Fallback to legacy analysis
                        result = analysis.comprehensive_analysis(
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
                            deep_chunk_months=args.deep_chunk_months,
                            json_output=getattr(args, 'json', False)
                        )
                        if getattr(args, 'json', False):
                            import json
                            print(json.dumps(result, indent=2))
                        return

                engine = ClariFiEngine()

            # Check if the first argument is a portfolio ID (UUID format)
            first_arg = args.tickers[0]
            is_portfolio_id = False
            portfolio_tickers = None

            # Check if it looks like a UUID (36 chars with hyphens)
            if len(first_arg) == 36 and first_arg.count('-') == 4:
                try:
                    # Try to get portfolio by ID
                    portfolio = engine.portfolio_model.get_by_id(first_arg)
                    if portfolio:
                        is_portfolio_id = True
                        portfolio_id = first_arg
                        tickers_data = engine.get_portfolio_tickers(portfolio_id)
                        portfolio_tickers = [t['ticker'] for t in tickers_data]
                        if not portfolio_tickers:
                            print(f"❌ No tickers in portfolio {portfolio_id[:8]}...")
                            return
                        print(f"🚀 Analyzing portfolio {portfolio_id[:8]}...")
                        print(f"📊 Tickers: {', '.join(portfolio_tickers)}")
                        print(f"📅 Period: {args.period}")
                except Exception:
                    # Not a valid portfolio ID, treat as ticker
                    pass

            # If not a portfolio ID, try to find by name
            if not is_portfolio_id and len(args.tickers) == 1:
                try:
                    portfolio = engine.portfolio_model.get_by_name(first_arg)
                    if portfolio:
                        is_portfolio_id = True
                        portfolio_id = portfolio['id']
                        tickers_data = engine.get_portfolio_tickers(portfolio_id)
                        portfolio_tickers = [t['ticker'] for t in tickers_data]
                        if not portfolio_tickers:
                            print(f"❌ No tickers in portfolio '{first_arg}'")
                            return
                        print(f"🚀 Analyzing portfolio '{first_arg}' ({portfolio_id[:8]}...)")
                        print(f"📊 Tickers: {', '.join(portfolio_tickers)}")
                        print(f"📅 Period: {args.period}")
                except Exception:
                    # Not a valid portfolio name, treat as ticker
                    pass

            if is_portfolio_id:
                # Portfolio analysis using engine
                result = engine.comprehensive_analysis(
                    tickers=portfolio_tickers,
                    portfolio_id=portfolio_id,
                    period=args.period,
                    include_patterns=not args.no_patterns,
                    include_events=not args.no_events,
                    include_options=not args.no_options,
                    include_seasonal=not args.no_seasonal,
                    include_ml=getattr(args, 'include_ml', False),
                    include_deep=args.include_deep,
                    deep_chunk_months=args.deep_chunk_months
                )

                if result.get('success'):
                    if args.summary_only:
                        print("\n📋 Portfolio Analysis Summary:")
                    else:
                        print("\n📋 Portfolio Analysis Complete:")

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
                            else:
                                emoji = "🟢"
                        elif rec == 'SELL':
                            emoji = "🔴"
                        elif rec == 'HOLD':
                            emoji = "🟡"
                        else:
                            emoji = "⚪"

                        if has_deep_results:
                            precision_str = f"{precision:.1%}" if precision is not None else "N/A"
                            print(f"│ {tk:7} │ {emoji} {rec:9} │ {conf:10} │ {risk:11} │ {precision_str:15} │")
                        else:
                            print(f"│ {tk:7} │ {emoji} {rec:9} │ {conf:10} │ {risk:11} │")

                    if has_deep_results:
                        print("└─────────┴──────────────┴────────────┴─────────────┴─────────────────┘")
                    else:
                        print("└─────────┴──────────────┴────────────┴─────────────┘")

                    if not args.summary_only and not getattr(args, 'json', False):
                        print("\n🎯 Strategy Timing & Hold Forecasts:")
                        for tk, data in result['results'].items():
                            strategy = data.get('strategy', {})
                            if not strategy or strategy.get('error'):
                                continue
                            print(f"  {tk}: {strategy.get('action', 'HOLD')} ({strategy.get('timeframe', 'N/A')})")
                            for timeframe in ('short_term', 'mid_term', 'long_term'):
                                prediction = strategy.get('predictions', {}).get(timeframe)
                                if prediction:
                                    print(
                                        f"    {timeframe}: ${prediction['predicted_price']:.2f} "
                                        f"(${prediction['price_lower_bound']:.2f}-${prediction['price_upper_bound']:.2f})"
                                    )
                            for action in ('buy', 'sell'):
                                moment = strategy.get('optimal_moments', {}).get(action)
                                if moment:
                                    print(f"    {moment['action']}: {moment['optimal_date']} ({moment['days_from_now']} days)")

                    if not args.summary_only and not getattr(args, 'json', False):
                        import json
                        print("\n🔍 Raw JSON data:")
                        print(json.dumps(result, indent=2))
                else:
                    print(f"❌ Analysis failed: {result.get('error')}")

                if getattr(args, 'json', False):
                    import json
                    print(json.dumps(result, indent=2))
            else:
                # Regular ticker analysis using legacy system
                result = analysis.comprehensive_analysis(
                    args.tickers,
                    args.period,
                    download=not args.no_download,
                    include_patterns=not args.no_patterns,
                    include_events=not args.no_events,
                    include_advanced_viz=not args.no_advanced_viz,
                    include_options=not args.no_options,
                    include_investment_advice=not args.no_investment_advice,
                    include_seasonal=not args.no_seasonal,
                    include_ml=getattr(args, 'include_ml', False),
                    include_deep=args.include_deep,
                    deep_chunk_months=args.deep_chunk_months,
                    json_output=getattr(args, 'json', False)
                )
                if getattr(args, 'json', False):
                    import json
                    print(json.dumps(result, indent=2))

        elif args.command == 'seasonal':
            result = analysis.seasonal_only(
                args.tickers,
                period=args.period,
                download=not args.no_download,
                json_output=getattr(args, 'json', False)
            )
            if getattr(args, 'json', False):
                import json
                print(json.dumps(result, indent=2))

        elif args.command == 'strategy':
            # Generate investment strategy for a single ticker
            ticker = args.ticker.upper()
            if getattr(args, 'json', False):
                import json
                try:
                    if not args.no_download:
                        downloader = StockDownloader()
                        download_result = downloader.download_multiple_stocks([ticker], None, None, args.period)
                        if not download_result or not download_result.get(ticker):
                            print(json.dumps({
                                "command": "strategy",
                                "ticker": ticker,
                                "period": args.period,
                                "errors": [f"Failed to download data for {ticker}"]
                            }, indent=2))
                            return

                    files = analysis.visualizer.find_stock_files(ticker)
                    if not files:
                        print(json.dumps({
                            "command": "strategy",
                            "ticker": ticker,
                            "period": args.period,
                            "errors": [f"No data found for {ticker}"]
                        }, indent=2))
                        return

                    latest_file = files[0] if len(files) == 1 and str(files[0]).startswith("db://") else max(files, key=os.path.getctime)
                    data = analysis.visualizer.load_stock_data(latest_file)
                    if data is None or len(data) < 60:
                        print(json.dumps({
                            "command": "strategy",
                            "ticker": ticker,
                            "period": args.period,
                            "errors": [f"Insufficient data for {ticker} (need 60+ points, got {len(data) if data is not None else 0})"]
                        }, indent=2))
                        return

                    seasonal_analyzer = SeasonalAnalyzer()
                    seasonal_result = seasonal_analyzer.analyze(data)

                    pattern_analyzer = PatternAnalyzer()
                    pattern_analyzer.add_technical_indicators(data)
                    technical_indicators = {
                        'ADX': float(data['ADX'].iloc[-1]) if 'ADX' in data.columns and not data['ADX'].isna().iloc[-1] else None,
                        'RSI_14': float(data['RSI_14'].iloc[-1]) if 'RSI_14' in data.columns and not data['RSI_14'].isna().iloc[-1] else None,
                        'MACD': float(data['MACD'].iloc[-1]) if 'MACD' in data.columns and not data['MACD'].isna().iloc[-1] else None,
                        'MACD_Signal': float(data['MACD_Signal'].iloc[-1]) if 'MACD_Signal' in data.columns and not data['MACD_Signal'].isna().iloc[-1] else None,
                        'Williams_%R': float(data['Williams_%R'].iloc[-1]) if 'Williams_%R' in data.columns and not data['Williams_%R'].isna().iloc[-1] else None,
                    }
                    technical_indicators['risk_metrics'] = pattern_analyzer.calculate_risk_metrics(data)
                    technical_indicators['market_regime'] = pattern_analyzer.detect_market_regime(data)

                    deep_result = None
                    if args.include_deep:
                        try:
                            from engine import ClariFiEngine
                            engine = ClariFiEngine()
                            deep_result = engine._run_deep_analysis(
                                ticker,
                                data.copy(),
                                chunk_months=args.deep_chunk_months
                            )
                            if deep_result and deep_result.get('error'):
                                deep_result = None
                        except Exception:
                            deep_result = None

                    strategy_analyzer = StrategyAnalyzer()
                    strategy = strategy_analyzer.generate_strategy(
                        ticker=ticker,
                        data=data,
                        period=args.period,
                        seasonal_analysis=seasonal_result,
                        deep_analysis=deep_result,
                        technical_indicators=technical_indicators,
                        find_optimum=args.optimum,
                    )

                    try:
                        prediction_tracking = analysis._persist_prediction_tracking(
                            ticker=ticker,
                            entry_price=strategy.entry_price,
                            predictions=strategy.predictions,
                        )
                        if prediction_tracking.get('new_prediction_ids'):
                            print(f"✓ Stored {len(prediction_tracking['new_prediction_ids'])} prediction rows")
                        elif prediction_tracking.get('error'):
                            print(f"⚠️  Prediction tracking failed: {prediction_tracking['error']}")
                    except Exception:
                        prediction_tracking = None

                    result = {
                        "command": "strategy",
                        "ticker": ticker,
                        "period": args.period,
                        "include_deep": args.include_deep,
                        "deep_chunk_months": args.deep_chunk_months,
                        "optimum": args.optimum,
                        "strategy": analysis._convert_to_json_serializable(strategy),
                        "seasonal_analysis": analysis._convert_to_json_serializable(seasonal_result),
                        "deep_analysis": analysis._convert_to_json_serializable(deep_result),
                        "prediction_tracking": analysis._convert_to_json_serializable(prediction_tracking),
                        "data_points": len(data),
                    }
                    print(json.dumps(result, indent=2))
                    return
                except Exception as e:
                    print(json.dumps({
                        "command": "strategy",
                        "ticker": ticker,
                        "period": args.period,
                        "errors": [str(e)]
                    }, indent=2))
                    return

            analysis._print_header(f"INVESTMENT STRATEGY FOR {ticker}", "🎯")
            print(f"📅 Analysis Period: {args.period}")
            if args.include_deep:
                print(f"🔬 Deep Analysis: Enabled (chunk size: {args.deep_chunk_months} months)")
            print()

            # Step 1: Download or load data
            if not args.no_download:
                analysis._print_section_header("DOWNLOADING DATA")
                downloader = StockDownloader()
                download_result = downloader.download_multiple_stocks([ticker], None, None, args.period)
                if not download_result or not download_result.get(ticker):
                    analysis._print_error(f"Failed to download data for {ticker}")
                    return
                analysis._print_success("Data downloaded successfully")

            # Load data
            files = analysis.visualizer.find_stock_files(ticker)
            if not files:
                analysis._print_error(f"No data found for {ticker}. Download first with: ./clarifi.sh download {ticker}")
                return

            latest_file = max(files, key=os.path.getctime)
            data = analysis.visualizer.load_stock_data(latest_file)
            if data is None or len(data) < 60:
                analysis._print_error(f"Insufficient data for {ticker} (need 60+ points, got {len(data) if data is not None else 0})")
                return

            print(f"✓ Loaded {len(data)} data points from {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
            print()

            # Step 2: Run seasonal analysis
            analysis._print_section_header("SEASONAL ANALYSIS")
            seasonal_analyzer = SeasonalAnalyzer()
            seasonal_result = seasonal_analyzer.analyze(data)
            if seasonal_result:
                print(f"✓ Seasonal patterns analyzed")
                print(f"  Best months: {', '.join(seasonal_result.best_months)}")
                print(f"  Worst months: {', '.join(seasonal_result.worst_months)}")
                print(f"  Seasonal bias score: {seasonal_result.bias_score:.2f}")
            else:
                seasonal_result = None
                print("⚠️  Insufficient data for seasonal analysis")
            print()

            # Step 3: Calculate technical indicators
            analysis._print_section_header("TECHNICAL INDICATORS")
            pattern_analyzer = PatternAnalyzer()
            pattern_analyzer.add_technical_indicators(data)

            # Capture technical indicators
            technical_indicators = {
                'ADX': float(data['ADX'].iloc[-1]) if 'ADX' in data.columns and not data['ADX'].isna().iloc[-1] else None,
                'RSI_14': float(data['RSI_14'].iloc[-1]) if 'RSI_14' in data.columns and not data['RSI_14'].isna().iloc[-1] else None,
                'MACD': float(data['MACD'].iloc[-1]) if 'MACD' in data.columns and not data['MACD'].isna().iloc[-1] else None,
                'MACD_Signal': float(data['MACD_Signal'].iloc[-1]) if 'MACD_Signal' in data.columns and not data['MACD_Signal'].isna().iloc[-1] else None,
                'Williams_%R': float(data['Williams_%R'].iloc[-1]) if 'Williams_%R' in data.columns and not data['Williams_%R'].isna().iloc[-1] else None,
            }

            # Add risk metrics
            risk_metrics = pattern_analyzer.calculate_risk_metrics(data)
            technical_indicators['risk_metrics'] = risk_metrics

            # Add market regime
            regime = pattern_analyzer.detect_market_regime(data)
            technical_indicators['market_regime'] = regime

            print(f"✓ Technical indicators calculated")
            if technical_indicators['RSI_14']:
                print(f"  RSI(14): {technical_indicators['RSI_14']:.2f}")
            if technical_indicators['ADX']:
                print(f"  ADX: {technical_indicators['ADX']:.2f}")
            print(f"  Market Regime: {regime.get('regime', 'UNKNOWN')}")
            print()

            # Step 4: Run deep backtesting if requested
            deep_result = None
            if args.include_deep:
                analysis._print_section_header("DEEP BACKTESTING ANALYSIS")
                try:
                    from engine import ClariFiEngine
                    engine = ClariFiEngine()
                    deep_result = engine._run_deep_analysis(
                        ticker,
                        data.copy(),
                        chunk_months=args.deep_chunk_months
                    )
                    if deep_result and not deep_result.get('error'):
                        summary = deep_result.get('summary', {})
                        precision = summary.get('coefficient_of_precision', 0)
                        chunks_eval = summary.get('chunks_evaluated', 0)
                        print(f"✓ Deep backtesting completed")
                        print(f"  Precision coefficient: {precision:.2%}")
                        print(f"  Chunks evaluated: {chunks_eval}")
                    else:
                        print(f"⚠️  Deep analysis failed: {deep_result.get('error', 'Unknown error') if deep_result else 'Execution failed'}")
                        deep_result = None
                except ImportError:
                    print("⚠️  ClariFiEngine not available for deep analysis")
                    deep_result = None
                except Exception as e:
                    print(f"⚠️  Deep analysis error: {str(e)}")
                    deep_result = None
                print()

            # Step 5: Generate strategy
            analysis._print_section_header("GENERATING STRATEGY")
            if args.optimum:
                print("🎯 Finding optimal buy/sell moment...")
            strategy_analyzer = StrategyAnalyzer()
            strategy = strategy_analyzer.generate_strategy(
                ticker=ticker,
                data=data,
                period=args.period,
                seasonal_analysis=seasonal_result,
                deep_analysis=deep_result,
                technical_indicators=technical_indicators,
                find_optimum=args.optimum,
            )

            try:
                prediction_tracking = self._persist_prediction_tracking(
                    ticker=ticker,
                    entry_price=strategy.entry_price,
                    predictions=strategy.predictions,
                )
                if prediction_tracking.get('new_prediction_ids'):
                    print(f"✓ Stored {len(prediction_tracking['new_prediction_ids'])} prediction rows")
                elif prediction_tracking.get('error'):
                    print(f"⚠️  Prediction tracking failed: {prediction_tracking['error']}")
            except Exception as e:
                prediction_tracking = None
                print(f"⚠️  Prediction tracking failed: {e}")

            # Display strategy
            print()
            print("=" * 70)
            analysis._print_header("INVESTMENT STRATEGY RECOMMENDATION", "💡")
            print("=" * 70)
            print()
            print(f"📊 Ticker: {strategy.ticker}")
            print(f"💰 Current Price: ${strategy.entry_price:.2f}")
            print()

            # Action with emoji
            action_emoji = "🟢" if strategy.action == "BUY" else "🔴" if strategy.action == "SELL" else "🟡"
            print(f"{action_emoji} ACTION: {strategy.action}")
            print(f"⏱️  TIMEFRAME: {strategy.timeframe}")
            print(f"📅 TARGET DATE: {strategy.target_date}")
            print(f"🎯 CONFIDENCE: {strategy.confidence}")
            print(f"⚠️  RISK LEVEL: {strategy.risk_level}")

            if strategy.expected_return_pct is not None:
                sign = "+" if strategy.expected_return_pct >= 0 else ""
                print(f"📈 EXPECTED RETURN: {sign}{strategy.expected_return_pct:.2f}%")
            print()

            print("💭 RATIONALE:")
            for i, reason in enumerate(strategy.rationale, 1):
                print(f"  {i}. {reason}")
            print()

            # Additional metrics
            if strategy.key_metrics:
                print("📊 KEY METRICS:")
                if 'overall_score' in strategy.key_metrics:
                    print(f"  Overall Score: {strategy.key_metrics['overall_score']}/100")

                if 'risk_metrics' in strategy.key_metrics:
                    rm = strategy.key_metrics['risk_metrics']
                    print(f"  Max Drawdown: {rm.get('max_drawdown', 0):.2f}%")
                    print(f"  Sharpe Ratio: {rm.get('sharpe_ratio', 0):.2f}")
                    print(f"  VaR (95%): {rm.get('var_95', 0):.2f}%")

                if 'trend' in strategy.key_metrics:
                    trend = strategy.key_metrics['trend']
                    print(f"  Short-term Trend: {trend.get('short_term', 'N/A')}")
                    print(f"  Medium-term Trend: {trend.get('medium_term', 'N/A')}")
                    if trend.get('long_term'):
                        print(f"  Long-term Trend: {trend['long_term']}")

            print()

            # Display price predictions
            if strategy.predictions:
                print("🔮 FUTURE PRICE PREDICTIONS:")
                print()

                # Short-term
                if 'short_term' in strategy.predictions:
                    st = strategy.predictions['short_term']
                    change_sign = "+" if st.predicted_change_pct >= 0 else ""
                    change_emoji = "📈" if st.predicted_change_pct >= 0 else "📉"
                    print(f"  📅 SHORT-TERM ({st.horizon_days} days):")
                    print(f"     Target Date: {st.target_date}")
                    print(f"     {change_emoji} Predicted Price: ${st.predicted_price:.2f} ({change_sign}{st.predicted_change_pct:.2f}%)")
                    print(f"     🎯 Confidence: {st.confidence}")
                    if st.reasoning:
                        print(f"     💡 Key Factors: {', '.join(st.reasoning)}")
                    print()

                # Mid-term
                if 'mid_term' in strategy.predictions:
                    mt = strategy.predictions['mid_term']
                    change_sign = "+" if mt.predicted_change_pct >= 0 else ""
                    change_emoji = "📈" if mt.predicted_change_pct >= 0 else "📉"
                    print(f"  📅 MID-TERM ({mt.horizon_days} days / ~1 month):")
                    print(f"     Target Date: {mt.target_date}")
                    print(f"     {change_emoji} Predicted Price: ${mt.predicted_price:.2f} ({change_sign}{mt.predicted_change_pct:.2f}%)")
                    print(f"     🎯 Confidence: {mt.confidence}")
                    if mt.reasoning:
                        print(f"     💡 Key Factors: {', '.join(mt.reasoning)}")
                    print()

                # Long-term
                if 'long_term' in strategy.predictions:
                    lt = strategy.predictions['long_term']
                    change_sign = "+" if lt.predicted_change_pct >= 0 else ""
                    change_emoji = "📈" if lt.predicted_change_pct >= 0 else "📉"
                    print(f"  📅 LONG-TERM ({lt.horizon_days} days / ~3 months):")
                    print(f"     Target Date: {lt.target_date}")
                    print(f"     {change_emoji} Predicted Price: ${lt.predicted_price:.2f} ({change_sign}{lt.predicted_change_pct:.2f}%)")
                    print(f"     🎯 Confidence: {lt.confidence}")
                    if lt.reasoning:
                        print(f"     💡 Key Factors: {', '.join(lt.reasoning)}")
                    print()

            # Display prediction tracking / confidence indicators
            if prediction_tracking:
                confidence = prediction_tracking.get("confidence") or {}
                resolved = prediction_tracking.get("resolved") or []
                print("📈 PREDICTION TRACK RECORD:")
                if resolved:
                    print(f"  ✓ Resolved {len(resolved)} past prediction(s) this run:")
                    for r in resolved:
                        mark = "✅" if r.get("accurate") else "❌"
                        print(f"     {mark} {r['horizon']}: predicted {r.get('predicted_trend', '?')}, "
                              f"actual {r['actual_trend']} (${r['actual_price']:.2f})")
                overall_rate = confidence.get("overall_accuracy_rate")
                rate_str = f"{overall_rate:.0%}" if overall_rate is not None else "N/A"
                print(f"  🎯 Confidence Score: {confidence.get('confidence_score', 0)} "
                      f"({confidence.get('resolved_count', 0)} resolved, {rate_str} accurate, "
                      f"{confidence.get('pending_count', 0)} pending)")
                print()

            # Display optimal moment if requested
            if args.optimum and strategy.optimal_moment:
                opt = strategy.optimal_moment
                print("🎯 OPTIMAL BUY/SELL MOMENT:")
                print()

                # Action with emoji
                action_emoji = "🟢" if opt.action == "BUY" else "🔴" if opt.action == "SELL" else "🟡"
                print(f"  {action_emoji} RECOMMENDED ACTION: {opt.action}")
                print(f"  📅 OPTIMAL DATE: {opt.optimal_date}")

                if opt.days_from_now == 0:
                    print(f"  ⏰ TIMING: NOW (Immediate action recommended)")
                else:
                    print(f"  ⏰ TIMING: {opt.days_from_now} days from now")

                print(f"  💰 EXPECTED PRICE: ${opt.expected_price:.2f}")

                if opt.expected_return_pct != 0:
                    return_sign = "+" if opt.expected_return_pct > 0 else ""
                    return_emoji = "📈" if opt.expected_return_pct > 0 else "📉"
                    print(f"  {return_emoji} EXPECTED RETURN: {return_sign}{opt.expected_return_pct:.2f}%")

                print(f"  🎯 CONFIDENCE: {opt.confidence}")
                print(f"  ⚖️  RISK/REWARD RATIO: {opt.risk_reward_ratio:.2f}")
                print()

                print("  💭 KEY REASONING:")
                for i, reason in enumerate(opt.reasoning, 1):
                    print(f"     {i}. {reason}")
                print()

                # Supporting signals
                if opt.supporting_signals:
                    print("  📊 SUPPORTING ANALYSIS:")
                    sig = opt.supporting_signals

                    if 'candidate_type' in sig:
                        type_map = {
                            'seasonal_buy': 'Seasonal Pattern (Best Month)',
                            'seasonal_sell': 'Seasonal Pattern (Worst Month)',
                            'technical_buy_oversold': 'Technical Indicator (Oversold)',
                            'technical_sell_overbought': 'Technical Indicator (Overbought)',
                            'pattern_buy': 'Historical Pattern',
                            'support_buy': 'Support Level',
                            'resistance_sell': 'Resistance Level',
                            'backtest_buy': 'Backtesting Performance',
                            'backtest_sell': 'Backtesting Performance',
                        }
                        print(f"     Signal Type: {type_map.get(sig['candidate_type'], sig['candidate_type'])}")

                    if 'target_month' in sig:
                        print(f"     Target Month: {sig['target_month']}")

                    if 'optimal_hold_period' in sig:
                        print(f"     Suggested Hold Period: {sig['optimal_hold_period']} days")

                    if 'win_rate' in sig:
                        print(f"     Historical Win Rate: {sig['win_rate']:.0f}%")

                    if 'trend_alignment' in sig:
                        alignment = "✓ Aligned" if sig['trend_alignment'] else "⚠ Contrarian"
                        print(f"     Trend Alignment: {alignment}")

                    print()

            print("=" * 70)
            print("⚠️  DISCLAIMER: This is not financial advice. Always do your own research.")
            print("=" * 70)

        elif args.command == 'suggest':
            engine = TickerSuggestionEngine(min_score=getattr(args, 'min_score', 55.0))
            universe = [ticker.upper() for ticker in args.tickers] if args.tickers else None
            results = engine.discover_suggestions(universe=universe, limit=args.limit)
            payload = {
                "command": "suggest",
                "limit": args.limit,
                "min_score": args.min_score,
                "results": [
                    {
                        "symbol": item.symbol,
                        "score": round(item.score, 2),
                        "expected_7d_return": round(item.expected_7d_return, 2),
                        "momentum": round(item.momentum, 2),
                        "volume_signal": round(item.volume_signal, 2),
                        "analyst_bias": round(item.analyst_bias, 2),
                        "risk_flag": item.risk_flag,
                        "reason": item.reason,
                    }
                    for item in results
                ],
            }
            if getattr(args, 'json', False):
                import json
                print(json.dumps(payload, indent=2))
                return

            if not results:
                print(f"No ticker suggestions met the {args.min_score} score threshold.")
                return

            print(f"\nTop suggestions (min score {args.min_score}):")
            for item in results:
                print(f"  {item.symbol}: score={item.score:.2f}, expected_7d_return={item.expected_7d_return:.2f}%, momentum={item.momentum:.2f}%, volume_signal={item.volume_signal:.2f}%, analyst_bias={item.analyst_bias:.2f}, risk={item.risk_flag} | {item.reason}")

        elif args.command == 'ml_analyze':
            # Check if ML dependencies are available
            try:
                from core.ml_analyzer import MLAnalyzer
                ml_analyzer = MLAnalyzer()
                available_models = ml_analyzer.get_available_models()
                enabled_models = [m for m in args.models if available_models.get(m, False)]

                if not enabled_models:
                    analysis._print_error("No ML models available. Please install required dependencies:")
                    analysis._print_error("pip install scikit-learn xgboost lightgbm")
                    return

                if enabled_models != args.models:
                    missing = [m for m in args.models if m not in enabled_models]
                    print(f"⚠️  Warning: Models {missing} not available, using {enabled_models}")

                # Load data and run ML analysis
                results = {}
                for ticker in args.tickers:
                    if not getattr(args, 'json', False):
                        analysis._print_header(f"ML ANALYSIS FOR {ticker}", "🤖")

                    # Download or load data
                    if not args.no_download:
                        print(f"📥 Downloading data for {ticker}...")
                        downloader = StockDownloader()
                        download_result = downloader.download_multiple_stocks([ticker], None, None, args.period)
                        if not download_result or not download_result.get(ticker):
                            analysis._print_error(f"Failed to download data for {ticker}")
                            continue

                    files = analysis.visualizer.find_stock_files(ticker)
                    if not files:
                        analysis._print_error(f"No data found for {ticker}. Download first with: ./clarifi.sh download {ticker}")
                        continue

                    latest_file = max(files, key=os.path.getctime)
                    data = analysis.visualizer.load_stock_data(latest_file)
                    if data is None or len(data) < 100:
                        analysis._print_error(f"Insufficient data for {ticker} (need 100+ points, got {len(data) if data is not None else 0})")
                        continue

                    # Run ML analysis
                    ml_result = ml_analyzer.analyze(data, ticker, prediction_horizon=args.horizon)

                    if ml_result:
                        results[ticker] = ml_result

                        if not getattr(args, 'json', False):
                            # Display results
                            rec = ml_result.recommendation
                            print(f"🎯 Recommendation: {rec.action} (Confidence: {rec.confidence:.1f})")
                            print(f"📈 Predicted Return: {rec.predicted_return_pct:.1f}%")
                            print(f"⚠️  Risk Score: {rec.risk_score:.2f}")
                            print(f"🧠 Best Model: {ml_result.best_model}")
                            print(f"💡 Reasoning: {rec.reasoning}")

                            # Show top features
                            if ml_result.feature_analysis:
                                print("\n🔍 Top Features:")
                                for feat, imp in list(ml_result.feature_analysis.items())[:5]:
                                    print(f"  {feat}: {imp:.3f}")

                            print(f"\n📊 Models Trained: {len(ml_result.models_trained)}")
                            for model in ml_result.models_trained:
                                if model.mse is not None:
                                    print(f"  {model.model_name}: MSE={model.mse:.4f}, MAE={model.mae:.4f}")
                    else:
                        analysis._print_error(f"ML analysis failed for {ticker}")

                result = {
                    "command": "ml_analyze",
                    "tickers": args.tickers,
                    "period": args.period,
                    "horizon": args.horizon,
                    "models_used": enabled_models,
                    "results": results
                }

                if getattr(args, 'json', False):
                    import json
                    print(json.dumps(result, indent=2))

            except ImportError as e:
                analysis._print_error(f"ML analysis not available: {e}")

        elif args.command == 'rnn':
            # Check if RNN dependencies are available
            try:
                from core.rnn_analyzer import RNNAnalyzer
                rnn_analyzer = RNNAnalyzer()
                available_models = rnn_analyzer.get_available_models()
                enabled_models = [m for m in args.models if m in available_models]

                if not enabled_models:
                    analysis._print_error("No RNN models available. Please install required dependencies:")
                    analysis._print_error("pip install tensorflow>=2.13.0")
                    return

                if enabled_models != args.models:
                    missing = [m for m in args.models if m not in enabled_models]
                    print(f"⚠️  Warning: Models {missing} not available, using {enabled_models}")

                # Load data and run RNN analysis
                results = {}
                for ticker in args.tickers:
                    if not getattr(args, 'json', False):
                        analysis._print_header(f"RNN ANALYSIS FOR {ticker}", "🧠")

                    # Download or load data
                    if not args.no_download:
                        print(f"📥 Downloading data for {ticker}...")
                        downloader = StockDownloader()
                        download_result = downloader.download_multiple_stocks([ticker], None, None, args.period)
                        if not download_result or not download_result.get(ticker):
                            analysis._print_error(f"Failed to download data for {ticker}")
                            continue

                    files = analysis.visualizer.find_stock_files(ticker)
                    if not files:
                        analysis._print_error(f"No data found for {ticker}. Download first with: ./clarifi.sh download {ticker}")
                        continue

                    latest_file = max(files, key=os.path.getctime)
                    data = analysis.visualizer.load_stock_data(latest_file)
                    if data is None or len(data) < 100:
                        analysis._print_error(f"Insufficient data for {ticker} (need 100+ points, got {len(data) if data is not None else 0})")
                        continue

                    # Run RNN analysis
                    rnn_result = rnn_analyzer.analyze(data, ticker, prediction_horizon=args.horizon)

                    if rnn_result:
                        results[ticker] = rnn_result

                        if not getattr(args, 'json', False):
                            # Display results
                            rec = rnn_result.recommendation
                            print(f"🎯 Recommendation: {rec.action} (Confidence: {rec.confidence:.1f})")
                            print(f"📈 Predicted Return: {rec.predicted_return:.1f}%")
                            print(f"⚠️  Risk Score: {rec.risk_score:.2f}")
                            print(f"🧠 Best Model: {rec.model_used}")
                            print(f"💡 Reasoning: {rec.reasoning}")

                            # Show top features
                            if rnn_result.feature_importance:
                                print("\n🔍 Top Features:")
                                for feat, imp in list(rnn_result.feature_importance.items())[:5]:
                                    print(f"  {feat}: {imp:.3f}")

                            print(f"\n📊 Models Trained: {len(rnn_result.models_results)}")
                            for model_name, model_result in rnn_result.models_results.items():
                                print(f"  {model_name}: MSE={model_result.mse:.4f}, MAE={model_result.mae:.4f}")
                    else:
                        analysis._print_error(f"RNN analysis failed for {ticker}")

                result = {
                    "command": "rnn",
                    "tickers": args.tickers,
                    "period": args.period,
                    "horizon": args.horizon,
                    "models_used": enabled_models,
                    "results": results
                }

                if getattr(args, 'json', False):
                    import json
                    print(json.dumps(result, indent=2))

            except ImportError as e:
                analysis._print_error(f"RNN analysis not available: {e}")
                analysis._print_error("Install required packages: pip install scikit-learn xgboost lightgbm")

        elif args.command == 'transformer':
            # Check if Transformer dependencies are available
            try:
                from core.transformer_analyzer import TransformerAnalyzer
                transformer_analyzer = TransformerAnalyzer()
                available_models = transformer_analyzer.get_available_models()
                enabled_models = [m for m in args.models if m in available_models]

                if not enabled_models:
                    analysis._print_error("No Transformer models available. Please install required dependencies:")
                    analysis._print_error("pip install torch torchvision tensorflow")
                    return

                if enabled_models != args.models:
                    missing = [m for m in args.models if m not in enabled_models]
                    print(f"⚠️  Warning: Models {missing} not available, using {enabled_models}")

                # Load data and run Transformer analysis
                results = {}
                for ticker in args.tickers:
                    if not getattr(args, 'json', False):
                        analysis._print_header(f"TRANSFORMER ANALYSIS FOR {ticker}", "🔄")

                    # Download or load data
                    if not args.no_download:
                        print(f"📥 Downloading data for {ticker}...")
                        downloader = StockDownloader()
                        download_result = downloader.download_multiple_stocks([ticker], None, None, args.period)
                        if not download_result or not download_result.get(ticker):
                            analysis._print_error(f"Failed to download data for {ticker}")
                            continue

                    files = analysis.visualizer.find_stock_files(ticker)
                    if not files:
                        analysis._print_error(f"No data found for {ticker}. Download first with: ./clarifi.sh download {ticker}")
                        continue

                    latest_file = max(files, key=os.path.getctime)
                    data = analysis.visualizer.load_stock_data(latest_file)
                    if data is None or len(data) < 100:
                        analysis._print_error(f"Insufficient data for {ticker} (need 100+ points, got {len(data) if data is not None else 0})")
                        continue

                    # Run Transformer analysis
                    transformer_result = transformer_analyzer.analyze(ticker, data, prediction_horizon=args.horizon)

                    if transformer_result:
                        results[ticker] = transformer_result

                        if not getattr(args, 'json', False):
                            # Display results
                            rec = transformer_result.recommendation
                            print(f"🎯 Recommendation: {rec.action} (Confidence: {rec.confidence:.1f})")
                            print(f"📈 Predicted Return: {rec.predicted_return_pct:.1f}%")
                            print(f"⚠️  Risk Score: {rec.risk_score:.2f}")
                            print(f"🔄 Best Model: {rec.model_used}")
                            print(f"💡 Reasoning: {rec.reasoning}")

                            # Show attention weights if available
                            if hasattr(rec, 'attention_focus') and rec.attention_focus:
                                print("\n🔍 Attention Analysis:")
                                top_features = sorted(rec.attention_focus.items(), key=lambda x: x[1], reverse=True)[:5]
                                for feat, weight in top_features:
                                    print(f"  {feat}: {weight:.3f}")

                            print(f"\n📊 Models Trained: {len(transformer_result.models_trained)}")
                            for model_result in transformer_result.models_trained:
                                print(f"  {model_result.model_name}: MSE={model_result.mse:.4f}, MAE={model_result.mae:.4f}")
                    else:
                        analysis._print_error(f"Transformer analysis failed for {ticker}")

                result = {
                    "command": "transformer",
                    "tickers": args.tickers,
                    "period": args.period,
                    "horizon": args.horizon,
                    "models_used": enabled_models,
                    "results": results
                }

                if getattr(args, 'json', False):
                    import json
                    print(json.dumps(result, indent=2))

            except ImportError as e:
                analysis._print_error(f"Transformer analysis not available: {e}")
                analysis._print_error("Install required packages: pip install torch torchvision tensorflow")

        elif args.command == 'rl':
            # Check if RL dependencies are available
            try:
                from core.rl_analyzer import RLAnalyzer
                rl_analyzer = RLAnalyzer()
                available_models = rl_analyzer.get_available_models()
                enabled_models = [m for m in args.models if m in available_models]

                if not enabled_models:
                    analysis._print_error("No RL models available. Please install required dependencies:")
                    analysis._print_error("pip install gymnasium stable-baselines3 torch")
                    return

                if enabled_models != args.models:
                    missing = [m for m in args.models if m not in enabled_models]
                    print(f"⚠️  Warning: Models {missing} not available, using {enabled_models}")

                # Load data and run RL analysis
                results = {}
                for ticker in args.tickers:
                    if not getattr(args, 'json', False):
                        analysis._print_header(f"REINFORCEMENT LEARNING ANALYSIS FOR {ticker}", "🎮")

                    # Download or load data
                    if not args.no_download:
                        print(f"📥 Downloading data for {ticker}...")
                        downloader = StockDownloader()
                        download_result = downloader.download_multiple_stocks([ticker], None, None, args.period)
                        if not download_result or not download_result.get(ticker):
                            analysis._print_error(f"Failed to download data for {ticker}")
                            continue

                    files = analysis.visualizer.find_stock_files(ticker)
                    if not files:
                        analysis._print_error(f"No data found for {ticker}. Download first with: ./clarifi.sh download {ticker}")
                        continue

                    latest_file = max(files, key=os.path.getctime)
                    data = analysis.visualizer.load_stock_data(latest_file)
                    if data is None or len(data) < 100:
                        analysis._print_error(f"Insufficient data for {ticker} (need 100+ points, got {len(data) if data is not None else 0})")
                        continue

                    # Run RL analysis
                    rl_result = rl_analyzer.analyze(ticker, data)

                    if rl_result:
                        results[ticker] = rl_result

                        if not getattr(args, 'json', False):
                            # Display results
                            rec = rl_result.recommendation
                            print(f"🎯 Recommendation: {rec.action} (Confidence: {rec.confidence:.1f})")
                            print(f"� Position Size: {rec.position_size:.1f}")
                            print(f"🛑 Stop Loss: ${rec.stop_loss:.2f}")
                            print(f"🎯 Take Profit: ${rec.take_profit:.2f}")
                            print(f"🎮 Best Model: {rec.model_used}")
                            print(f"💡 Reasoning: {rec.reasoning}")

                            # Show risk metrics
                            if hasattr(rec, 'risk_metrics') and rec.risk_metrics:
                                print("\n📊 Risk Metrics:")
                                for metric, value in rec.risk_metrics.items():
                                    if isinstance(value, float):
                                        print(f"  {metric}: {value:.3f}")
                                    else:
                                        print(f"  {metric}: {value}")
                            # Show models trained
                            print(f"\n🤖 Models Trained: {len(rl_result.models_trained)}")
                            for model_result in rl_result.models_trained:
                                print(f"  {model_result.model_name}: Sharpe={model_result.sharpe_ratio:.3f}, Win Rate={model_result.win_rate:.1%}")

                            # Show backtest results if available
                            if hasattr(rl_result, 'backtest_results') and rl_result.backtest_results:
                                print(f"\n🔄 Backtest Results:")
                                for model_name, backtest in rl_result.backtest_results.items():
                                    if backtest:
                                        print(f"  {model_name}: Return={backtest.get('total_return', 0):.2f}%, Trades={backtest.get('total_trades', 0)}")
                    else:
                        analysis._print_error(f"RL analysis failed for {ticker}")

                result = {
                    "command": "rl",
                    "tickers": args.tickers,
                    "period": args.period,
                    "episodes": args.episodes,
                    "backtest": args.backtest,
                    "models_used": enabled_models,
                    "results": results
                }

                if getattr(args, 'json', False):
                    import json
                    print(json.dumps(result, indent=2))

            except ImportError as e:
                analysis._print_error(f"RL analysis not available: {e}")
                analysis._print_error("Install required packages: pip install gymnasium stable-baselines3 torch")

        elif args.command == 'patterns':
            # Load data
            stock_data_dict = {}
            for ticker in args.tickers:
                files = analysis.visualizer.find_stock_files(ticker)
                if not files:
                    analysis._print_error(f"No data found for {ticker}. Download first with: ./clarifi.sh download {ticker}")
                    continue
                latest_file = max(files, key=os.path.getctime)
                data = analysis.visualizer.load_stock_data(latest_file)
                if data is not None:
                    stock_data_dict[ticker] = data

            if stock_data_dict:
                if not getattr(args, 'json', False):
                    analysis._print_header("PATTERN ANALYSIS", "🔍")
                    print(f"📈 Tickers: {', '.join(stock_data_dict.keys())}")
                correlation_results = analysis.pattern_analyzer.analyze_correlation_patterns(
                    stock_data_dict, window=args.window)
                trend_results = analysis.pattern_analyzer.analyze_trend_strength(stock_data_dict)

                result = {
                    "command": "patterns",
                    "tickers": list(stock_data_dict.keys()),
                    "window": args.window,
                    "correlation_results": correlation_results,
                    "trend_results": trend_results
                }

                if not getattr(args, 'json', False):
                    # Create visualizations
                    analysis.advanced_visualizer.plot_correlation_heatmap(correlation_results)
                    analysis.advanced_visualizer.plot_rolling_correlations(correlation_results)
                    analysis._print_success("Pattern analysis completed!")
                else:
                    import json
                    print(json.dumps(result, indent=2))

        elif args.command == 'correlations':
            if len(args.tickers) < 2:
                analysis._print_error("Need at least 2 tickers for correlation analysis")
                return

            # Load data
            stock_data_dict = {}
            for ticker in args.tickers:
                files = analysis.visualizer.find_stock_files(ticker)
                if not files:
                    analysis._print_error(f"No data found for {ticker}. Download first with: ./clarifi.sh download {ticker}")
                    continue
                latest_file = max(files, key=os.path.getctime)
                data = analysis.visualizer.load_stock_data(latest_file)
                if data is not None:
                    stock_data_dict[ticker] = data

            if len(stock_data_dict) >= 2:
                if not getattr(args, 'json', False):
                    analysis._print_header("CORRELATION ANALYSIS", "📊")
                    print(f"📈 Tickers: {', '.join(stock_data_dict.keys())}")
                correlation_results = analysis.pattern_analyzer.analyze_correlation_patterns(
                    stock_data_dict, window=args.window)

                result = {
                    "command": "correlations",
                    "tickers": list(stock_data_dict.keys()),
                    "window": args.window,
                    "correlation_results": correlation_results
                }

                if not getattr(args, 'json', False):
                    # Create visualizations
                    analysis.advanced_visualizer.plot_correlation_heatmap(correlation_results)
                    analysis.advanced_visualizer.plot_rolling_correlations(correlation_results)
                    analysis._print_success("Correlation analysis completed!")
                else:
                    import json
                    print(json.dumps(result, indent=2))

        elif args.command == 'events':
            # Load data
            stock_data_dict = {}
            for ticker in args.tickers:
                files = analysis.visualizer.find_stock_files(ticker)
                if not files:
                    analysis._print_error(f"No data found for {ticker}. Download first with: ./clarifi.sh download {ticker}")
                    continue
                latest_file = max(files, key=os.path.getctime)
                data = analysis.visualizer.load_stock_data(latest_file)
                if data is not None:
                    stock_data_dict[ticker] = data

            if stock_data_dict:
                if not getattr(args, 'json', False):
                    analysis._print_header("EVENT CORRELATION ANALYSIS", "📰")
                    print(f"📈 Tickers: {', '.join(stock_data_dict.keys())}")
                event_results = analysis.event_correlator.correlate_events_with_movements(
                    stock_data_dict, args.lookback, args.lookahead)
                unusual_movements = analysis.event_correlator.identify_unusual_movements(stock_data_dict)

                # Generate summary
                event_summary = analysis.event_correlator.generate_event_summary(event_results, unusual_movements)

                result = {
                    "command": "events",
                    "tickers": list(stock_data_dict.keys()),
                    "lookback": args.lookback,
                    "lookahead": args.lookahead,
                    "event_results": event_results,
                    "unusual_movements": unusual_movements,
                    "event_summary": event_summary
                }

                if not getattr(args, 'json', False):
                    # Create visualizations
                    analysis.advanced_visualizer.plot_event_impact_analysis(event_results)
                    analysis._print_success("Event correlation analysis completed!")
                else:
                    import json
                    print(json.dumps(result, indent=2))

        elif args.command == 'volatility':
            # Load data
            stock_data_dict = {}
            for ticker in args.tickers:
                files = analysis.visualizer.find_stock_files(ticker)
                if not files:
                    print(f"❌ No data found for {ticker}. Download first with: ./clarifi.sh download {ticker}")
                    continue
                latest_file = max(files, key=os.path.getctime)
                data = analysis.visualizer.load_stock_data(latest_file)
                if data is not None:
                    stock_data_dict[ticker] = data

            if stock_data_dict:
                if not getattr(args, 'json', False):
                    analysis._print_header("VOLATILITY ANALYSIS", "🌊")
                volatility_results = analysis.pattern_analyzer.detect_volatility_patterns(
                    stock_data_dict, window=args.window)

                result = {
                    "command": "volatility",
                    "tickers": list(stock_data_dict.keys()),
                    "window": args.window,
                    "clustering": args.clustering,
                    "volatility_results": volatility_results
                }

                if not getattr(args, 'json', False):
                    if args.clustering:
                        analysis.advanced_visualizer.plot_volatility_clustering(volatility_results)
                    analysis._print_success("Volatility analysis completed!")
                else:
                    import json
                    print(json.dumps(result, indent=2))

        elif args.command == 'download':
            downloader = StockDownloader()
            if args.period:
                results = downloader.download_multiple_stocks(args.tickers, None, None, args.period)
            else:
                start = args.start or (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
                end = args.end or datetime.now().strftime("%Y-%m-%d")
                results = downloader.download_multiple_stocks(args.tickers, start, end)

            result = {
                "command": "download",
                "tickers": args.tickers,
                "period": args.period,
                "start": args.start,
                "end": args.end,
                "results": results
            }

            if not getattr(args, 'json', False):
                analysis._print_header("DOWNLOAD COMPLETED", "📥")
                for ticker, filepath in results.items():
                    if filepath:
                        print(f"  ✅ {ticker}: {filepath}")
            else:
                import json
                print(json.dumps(result, indent=2))

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
            result = legacy_analysis.show_stock_info(args.tickers, json_output=getattr(args, 'json', False))
            if getattr(args, 'json', False):
                import json
                print(json.dumps(result, indent=2))

        elif args.command == 'list':
            result = legacy_analysis.list_available_data(json_output=getattr(args, 'json', False))
            if getattr(args, 'json', False):
                import json
                print(json.dumps(result, indent=2))

        elif args.command == 'live':
            # Initialize live monitor
            monitor = LiveStockMonitor()
            monitor.update_interval = args.interval
            monitor.add_tickers(args.tickers)

            analysis._print_header("STARTING LIVE MONITORING", "🚀")
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

            if not getattr(args, 'json', False):
                analysis._print_header(f"MARKET SCREENING: {args.category.upper()}", "🔍")
                print(f"📊 Limit: {args.limit} results")
                if args.export:
                    print(f"📁 Export to: {args.export}")
                print()

            # Perform screening
            result = screener.screen_market(args.category, args.limit, json_output=getattr(args, 'json', False))

            if getattr(args, 'json', False):
                import json
                print(json.dumps(result, indent=2))
            else:
                # TODO: Implement CSV export if requested
                if args.export:
                    print(f"💾 CSV export functionality coming soon...")

        elif args.command == 'prune':
            analysis.prune_data()

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
                    analysis._print_warning("No portfolios found")
                    return

                analysis._print_header("PORTFOLIOS", "📁")
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
                    analysis._print_warning(f"No tickers in portfolio {portfolio_id[:8]}...")
                    return

                analysis._print_header(f"TICKERS IN PORTFOLIO {portfolio_id[:8]}...", "📊")
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
                    analysis._print_success(f"Created portfolio '{args.name}'")
                    print(f"   ID: {portfolio_id}")
                    print(f"   Description: {args.description or '(none)'}")
                else:
                    analysis._print_error(f"Failed to create portfolio: {result.get('error')}")

            elif cmd == 'list':
                portfolios = engine.get_portfolios()
                format_portfolio_table(portfolios)

            elif cmd == 'info':
                # Handle portfolio identification by ID or name
                portfolio_id = args.portfolio_id
                portfolio = None

                # Try to get by ID first
                portfolio = engine.portfolio_model.get_by_id(portfolio_id)

                # If not found by ID, try by name
                if not portfolio:
                    portfolio = engine.portfolio_model.get_by_name(portfolio_id)
                    if portfolio:
                        portfolio_id = portfolio['id']

                if not portfolio:
                    analysis._print_error(f"Portfolio not found: {args.portfolio_id}")
                    return

                # Get portfolio info
                result = engine.get_portfolio_info(portfolio_id)
                if result.get('success'):
                    data = result['data']
                    portfolio_info = data['portfolio']

                    # Display portfolio metadata
                    analysis._print_header(f"PORTFOLIO INFORMATION: {portfolio_info['name']}", "📁")
                    print(f"   ID: {portfolio_info['id']}")
                    print(f"   Description: {portfolio_info.get('description', 'No description')}")
                    print(f"   Created: {portfolio_info.get('created_at', 'Unknown')}")
                    print(f"   Last Updated: {portfolio_info.get('updated_at', 'Unknown')}")

                    # Display financial summary
                    summary = data.get('summary', {})
                    analysis._print_section_header("FINANCIAL SUMMARY", "💰")
                    print(f"   Total Tickers: {summary.get('total_tickers', 0)}")
                    print(f"   Total Current Value: ${summary.get('total_current_value', 0):,.2f}")
                    print(f"   Total Cost Basis: ${summary.get('total_cost', 0):,.2f}")
                    print(f"   Total P&L: ${summary.get('total_unrealized_pnl', 0):+,.2f}")
                    print(f"   Portfolio Return: {summary.get('portfolio_percentage_change', 0):+.2f}%")

                    # Display accuracy metrics if available
                    accuracy = data.get('accuracy_metrics', {})
                    if accuracy.get('total_predictions', 0) > 0:
                        analysis._print_section_header("PREDICTION ACCURACY", "📊")
                        print(f"   Average Accuracy: {accuracy.get('avg_accuracy', 0):.1%}")
                        print(f"   Total Predictions: {accuracy.get('total_predictions', 0)}")
                        print(f"   Accuracy Range: {accuracy.get('min_accuracy', 0):.1%} - {accuracy.get('max_accuracy', 0):.1%}")

                    # Display tickers table
                    tickers = data.get('tickers', [])
                    if tickers:
                        analysis._print_section_header("HOLDINGS", "📊")
                        print("┌─────────┬──────────┬─────────────┬─────────────┬─────────────┬─────────────────┐")
                        print("│ Ticker  │ Quantity │ Avg Cost    │ Current $   │ Current Val │ P&L (%)         │")
                        print("├─────────┼──────────┼─────────────┼─────────────┼─────────────┼─────────────────┤")

                        for ticker_info in tickers:
                            ticker = ticker_info['ticker'][:8]
                            quantity = f"{ticker_info.get('quantity', 0):.2f}"[:9]
                            avg_cost = f"${ticker_info.get('avg_cost', 0):.2f}"[:10]
                            current_price = f"${ticker_info.get('current_price', 0):.2f}"[:10]
                            current_value = f"${ticker_info.get('current_value', 0):,.0f}"[:10]

                            pnl = ticker_info.get('unrealized_pnl', 0) or 0
                            pct_change = ticker_info.get('percentage_change', 0) or 0

                            if pnl >= 0:
                                pnl_display = f"+${pnl:,.0f} (+{pct_change:.1f}%)"[:15]
                            else:
                                pnl_display = f"-${abs(pnl):,.0f} ({pct_change:.1f}%)"[:15]

                            print(f"│ {ticker:7} │ {quantity:8} │ {avg_cost:11} │ {current_price:11} │ {current_value:11} │ {pnl_display:15} │")

                        print("└─────────┴──────────┴─────────────┴─────────────┴─────────────┴─────────────────┘")

                    # Display recent changes if any
                    recent_changes = data.get('recent_changes', [])
                    if recent_changes:
                        analysis._print_section_header("RECENT CHANGES (LAST 30 DAYS)", "📈")
                        print("┌─────────┬─────────────┬─────────────────────┬───────────────────────────┐")
                        print("│ Ticker  │ Action      │ Date                │ Notes                     │")
                        print("├─────────┼─────────────┼─────────────────────┼───────────────────────────┤")

                        for change in recent_changes[:10]:  # Show last 10 changes
                            ticker = change['ticker'][:8]
                            action = change['transaction_type'][:10]
                            date = change['change_date'][:19]
                            notes = (change.get('notes', '') or '')[:25]
                            print(f"│ {ticker:7} │ {action:11} │ {date:19} │ {notes:25} │")

                        print("└─────────┴─────────────┴─────────────────────┴───────────────────────────┘")

                    # Show analytics if requested
                    if args.analytics:
                        analytics_result = engine.get_portfolio_analytics(portfolio_id)
                        if analytics_result.get('success'):
                            analytics = analytics_result['data']
                            analysis._print_section_header("PORTFOLIO ANALYTICS", "📈")

                            # Portfolio summary
                            summary = analytics.get('portfolio_summary', {})
                            print(f"   📊 Holdings: {summary.get('total_holdings', 0)} positions")
                            print(f"   💰 Total Value: ${summary.get('total_value', 0):,.2f}")
                            print(f"   📈 Total Return: {summary.get('total_return_pct', 0):+.2f}%")

                            # Risk assessment
                            risk = analytics.get('risk_assessment', {})
                            print(f"   ⚠️ Overall Risk: {risk.get('overall_risk', 'N/A')}")
                            print(f"   🎯 Concentration Risk: {risk.get('concentration_risk', 'N/A')}")
                            print(f"   📊 Diversification Score: {risk.get('diversification_score', 0):.0f}/100")

                            # Top holdings composition
                            composition = analytics.get('composition', [])
                            if composition:
                                print(f"\n   🔝 Top Holdings:")
                                for i, holding in enumerate(composition[:5], 1):
                                    weight = holding['weight']
                                    ticker = holding['ticker']
                                    value = holding['value']
                                    print(f"      {i}. {ticker}: {weight:.1f}% (${value:,.0f})")

                            # Analysis-based metrics (if available)
                            analysis_metrics = analytics.get('analysis_based_metrics', {})
                            if analysis_metrics.get('has_analysis_data'):
                                recommendations = analysis_metrics.get('recommendation_distribution', [])
                                if recommendations:
                                    analysis._print_section_header("ANALYSIS RECOMMENDATIONS", "🎯")
                                    for rec in recommendations:
                                        if rec.get('recommendation'):
                                            print(f"      {rec['recommendation']}: {rec['count']} position(s)")
                            else:
                                print(f"\n   💡 Run portfolio analysis to get AI-powered recommendations")
                        else:
                            analysis._print_warning(f"Analytics unavailable: {analytics_result.get('error', 'Unknown error')}")
                    else:
                        print(f"\n💡 Use --analytics flag for detailed portfolio analytics")

                else:
                    analysis._print_error(f"Failed to get portfolio info: {result.get('message')}")
                    if result.get('error'):
                        print(f"   Error: {result['error']}")

            elif cmd == 'add':
                result = engine.add_ticker_to_portfolio(
                    args.portfolio_id, args.ticker,
                    quantity=args.quantity, avg_cost=args.avg_cost
                )
                if result.get('success'):
                    analysis._print_success(f"Added {args.ticker.upper()} to portfolio")
                    if args.quantity > 0:
                        print(f"   Quantity: {args.quantity}")
                    if args.avg_cost > 0:
                        print(f"   Average cost: ${args.avg_cost:.2f}")
                else:
                    analysis._print_error(f"Failed to add ticker: {result.get('error')}")

            elif cmd == 'remove':
                result = engine.remove_ticker_from_portfolio(args.portfolio_id, args.ticker)
                if result.get('success'):
                    analysis._print_success(f"Removed {args.ticker.upper()} from portfolio")
                else:
                    analysis._print_error(f"{result.get('message', 'Failed to remove ticker')}")

            elif cmd == 'tickers':
                tickers = engine.get_portfolio_tickers(args.portfolio_id)
                format_tickers_table(tickers, args.portfolio_id)

            elif cmd == 'update-ticker':
                # Validate that at least one field is provided
                if args.quantity is None and args.avg_cost is None:
                    analysis._print_error("At least one of --quantity or --avg-cost must be provided")
                    return

                result = engine.update_ticker_in_portfolio(
                    args.portfolio_id, args.ticker, args.quantity, args.avg_cost
                )
                if result.get('success'):
                    analysis._print_success(f"Ticker {result.get('ticker')} updated successfully")
                    if args.quantity is not None:
                        print(f"   New quantity: {args.quantity}")
                    if args.avg_cost is not None:
                        print(f"   New average cost: ${args.avg_cost:.2f}")
                else:
                    analysis._print_error(f"Failed to update ticker: {result.get('message')}")

            elif cmd == 'update':
                # Validate that at least one field is provided
                if not args.name and not args.description:
                    analysis._print_error("At least one of --name or --description must be provided")
                    return

                result = engine.update_portfolio(args.portfolio_id, args.name, args.description)
                if result.get('success'):
                    analysis._print_success("Portfolio updated successfully")
                    if args.name:
                        print(f"   New name: {args.name}")
                    if args.description:
                        print(f"   New description: {args.description}")
                else:
                    analysis._print_error(f"Failed to update portfolio: {result.get('message')}")

            elif cmd == 'delete':
                # Show warning and get portfolio info first
                portfolio = engine.portfolio_model.get_by_id(args.portfolio_id)
                if not portfolio:
                    analysis._print_error(f"Portfolio not found: {args.portfolio_id}")
                    return

                tickers = engine.get_portfolio_tickers(args.portfolio_id)
                ticker_count = len(tickers)

                analysis._print_warning(f"You are about to delete portfolio '{portfolio['name']}'")
                print(f"   This action is IRREVERSIBLE and will:")
                print(f"   - Delete the portfolio permanently")
                print(f"   - Remove all {ticker_count} associated tickers")
                print(f"   - Remove all analysis history")
                print()

                result = engine.delete_portfolio(args.portfolio_id, args.confirm_name)
                if result.get('success'):
                    analysis._print_success(f"{result.get('message')}")
                    print(f"   Deleted tickers: {result.get('deleted_tickers', 0)}")
                else:
                    analysis._print_error(f"{result.get('message')}")
                    if 'warning' in result:
                        print(f"   {result['warning']}")

            elif cmd == 'sync':
                # Show portfolio info first
                portfolio = engine.portfolio_model.get_by_id(args.portfolio_id)
                if not portfolio:
                    analysis._print_error(f"Portfolio not found: {args.portfolio_id}")
                    return

                analysis._print_header(f"SYNCING PRICES FOR PORTFOLIO '{portfolio['name']}'", "🔄")

                result = engine.sync_portfolio_prices(args.portfolio_id)
                if result.get('success'):
                    analysis._print_success(f"{result.get('message')}")
                    print(f"   Portfolio: {result.get('portfolio_name')}")
                    print(f"   Total tickers: {result.get('total_tickers', 0)}")
                    print(f"   Successful syncs: {result.get('successful_syncs', 0)}")
                    print(f"   Failed syncs: {result.get('failed_syncs', 0)}")
                    print(f"   Execution time: {result.get('execution_time', 0):.2f}s")

                    # Show detailed results in a table
                    sync_results = result.get('sync_results', {})
                    if sync_results:
                        analysis._print_section_header("PRICE UPDATE DETAILS", "📊")
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
                    analysis._print_error(f"Failed to sync portfolio: {result.get('message')}")
                    print(f"   Error: {result.get('error', 'Unknown error')}")

            elif cmd == 'analyze':
                # Fetch tickers first
                tickers = engine.get_portfolio_tickers(args.portfolio_id)
                if not tickers:
                    analysis._print_error(f"No tickers in portfolio {args.portfolio_id[:8]}...")
                    return
                ticker_list = [t['ticker'] for t in tickers]
                analysis._print_header(f"ANALYZING PORTFOLIO {args.portfolio_id[:8]}...", "🚀")
                print(f"📊 Tickers: {', '.join(ticker_list)}")
                print(f"📅 Period: {args.period}")

                result = engine.comprehensive_analysis(
                    tickers=ticker_list,
                    portfolio_id=args.portfolio_id,
                    period=args.period,
                    include_patterns=not args.no_patterns,
                    include_events=not args.no_events,
                    include_options=not args.no_options,
                    include_seasonal=not args.no_seasonal,
                    include_deep=args.include_deep,
                    deep_chunk_months=args.deep_chunk_months
                )
                if result.get('success'):
                    if args.summary_only:
                        analysis._print_header("PORTFOLIO ANALYSIS SUMMARY", "📋")
                    else:
                        analysis._print_header("PORTFOLIO ANALYSIS COMPLETE", "📋")

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
                    analysis._print_success("Portfolio analysis complete")

                    print_json_minimal(result, show_json=not args.summary_only)
                else:
                    analysis._print_error(f"Analysis failed: {result.get('error')}")
                    print_json_minimal(result, show_json=True)

            elif cmd == 'history':
                history = engine.get_analysis_history(
                    ticker=args.ticker, portfolio_id=args.portfolio_id, limit=args.limit
                )
                if history:
                    analysis._print_header("RECENT ANALYSIS HISTORY", "📜")
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
                    analysis._print_warning("No analysis history found")

            elif cmd == 'accuracy':
                trends = engine.get_accuracy_trends(
                    ticker=args.ticker, portfolio_id=args.portfolio_id
                )
                if trends:
                    analysis._print_header("ACCURACY TRENDS", "📈")
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
                    analysis._print_warning("No accuracy data found")
            else:
                portfolio_parser.print_help()

        elif args.command == 'ai':
            # Lazy import to keep base dependencies light
            try:
                from ai_analyzer import AIAnalyzer, is_probable_portfolio_identifier
            except Exception as e:
                analysis._print_error(f"Failed to load AI analyzer: {e}")
                return

            call_llm = not args.no_llm
            model_name = args.model
            period = args.period
            raw_inputs = args.tickers

            # Detect portfolio vs ticker list
            portfolio_id = None
            tickers = raw_inputs
            if len(raw_inputs) == 1 and is_probable_portfolio_identifier(raw_inputs[0]):
                portfolio_id = raw_inputs[0]

            if portfolio_id:
                if engine is None:
                    from engine import ClariFiEngine  # local import
                    engine = ClariFiEngine()
                try:
                    tdata = engine.get_portfolio_tickers(portfolio_id)
                    if not tdata:
                        analysis._print_error(f"Portfolio {portfolio_id} has no tickers")
                        return
                    tickers = [t['ticker'] for t in tdata]
                    analysis._print_header(f"USING PORTFOLIO {portfolio_id} WITH {len(tickers)} TICKERS", "📁")
                except Exception as e:
                    analysis._print_error(f"Failed to load portfolio: {e}")
                    return

            analyzer = AIAnalyzer(model=model_name)

            # Determine analysis mode
            if not getattr(args, 'json', False):
                if args.combined:
                    analysis._print_header(f"COMBINED ANALYSIS (COMPREHENSIVE + AI) FOR: {', '.join(tickers)} (PERIOD {period})", "🤖")
                    print("📊 This includes patterns, options, seasonal, and quantitative analysis...")
                else:
                    analysis._print_header(f"AI QUANTITATIVE ANALYSIS FOR: {', '.join(tickers)} (PERIOD {period})", "🤖")

                if not call_llm:
                    print("🧪 LLM call disabled (--no-llm)")

            result = analyzer.analyze(tickers, period=period, call_model=call_llm, include_comprehensive=args.combined)

            analyses = result.get('analyses', [])
            if not analyses:
                if not getattr(args, 'json', False):
                    analysis._print_error("No analyses produced")
                    if result.get('errors'):
                        print("Errors:")
                        for k, v in result['errors'].items():
                            print(f"  {k}: {v}")
                return

            # Optional prompt transparency
            if not getattr(args, 'json', False) and args.show_prompt:
                print("\n📝 Prompt sent to LLM (quantitative basis):\n")
                print(result.get('prompt', ''))

            # Optional raw JSON output
            if getattr(args, 'json', False):
                import json
                print(json.dumps(result, indent=2))
                return

            # Optional raw JSON output (legacy flag for backward compatibility)
            if args.raw_json:
                print("\n🔧 Raw AI Response Debug Information:")
                print("=" * 50)
                print("FINAL PROMPT:")
                print(result.get('prompt', ''))
                print("\n" + "=" * 50)
                print("RAW LLM RESPONSE:")
                print(result.get('llm_raw', 'No LLM response'))
                print("\n" + "=" * 50)
                print("PARSED JSON:")
                import json
                llm_data = result.get('llm', {})
                print(json.dumps(llm_data.get('parsed', {}), indent=2))
                if llm_data.get('validation_errors'):
                    print("\nVALIDATION ERRORS:")
                    for error in llm_data['validation_errors']:
                        print(f"  - {error}")
                print("=" * 50)
                return  # Exit early if user just wants raw output

            import math
            # Summary table
            if not getattr(args, 'json', False):
                analysis._print_header("QUANTITATIVE METRICS (PER TICKER)", "📊")
                header = (
                    "Ticker  Last  AvgDaily%  AnnVol%  MaxDD%  SMA50/200%  RSI14  BT_Str%  BT_Excess%  Trend"
                )
                print(header)
                print("-" * len(header))
                for a in analyses:
                    bt = a.get('backtest') or {}
                    print(
                        f"{a['ticker']:<6} {a['last_price']:<5.2f} {a['avg_daily_return_pct']:<9.2f} {a['vol_annualized_pct']:<7.2f} {a['max_drawdown_pct']:<7.2f} "
                        f"{(a['sma50_vs_200_pct'] if a['sma50_vs_200_pct'] is not None else float('nan')):<11.2f} {a['rsi_14']:<6.1f} "
                        f"{bt.get('strategy_return_pct', float('nan')):<8.2f} {bt.get('excess_return_pct', float('nan')):<11.2f} {a['quantitative_trend']}"
                    )

            # Display comprehensive analysis results if available
            if not getattr(args, 'json', False) and args.combined and result.get('comprehensive_recommendations'):
                analysis._print_header("COMPREHENSIVE ANALYSIS RECOMMENDATIONS", "📋")
                comp_recs = result.get('comprehensive_recommendations', {})
                for ticker, rec in comp_recs.items():
                    print(f"  {ticker}: {rec}")

            llm_parsed = (result.get('llm') or {}).get('parsed')
            combined_recs = result.get('combined_recommendations')

            if not getattr(args, 'json', False) and call_llm and (llm_parsed or combined_recs):
                # Display combined recommendations if available, otherwise standard AI recommendations
                if args.combined and combined_recs:
                    analysis._print_header("COMBINED AI + COMPREHENSIVE RECOMMENDATIONS", "🎯")
                    tick_list = combined_recs.get('tickers') or []
                    if tick_list:
                        print("Ticker  AI-Rec  Comp-Rec  Final-Rec  Confidence")
                        print("------------------------------------------------")
                        for t in tick_list:
                            ai_rec = t.get('ai_recommendation', '?')
                            comp_rec = t.get('comprehensive_recommendation', '?')
                            final_rec = t.get('recommendation', '?')
                            confidence = t.get('confidence', '?')
                            print(f"{t.get('ticker','?'):<7} {ai_rec:<7} {comp_rec:<9} {final_rec:<10} {confidence}")

                    overall = combined_recs.get('overall')
                    if overall:
                        print("\nCombined Overall Stance:", overall.get('stance'))
                        notes = overall.get('notes') or []
                        for n in notes[:5]:
                            print(" -", n)

                    if not args.summary_only:
                        # Show combined rationale details
                        for t in tick_list:
                            rationale = t.get('rationale') or []
                            if rationale:
                                print(f"\n{t.get('ticker')} Combined Rationale:")
                                for r in rationale[:5]:
                                    print(" -", r)

                elif llm_parsed:
                    analysis._print_header("AI RECOMMENDATIONS", "🎯")
                    tick_list = llm_parsed.get('tickers') or []
                    if tick_list:
                        print("Ticker  Recommendation")
                        print("----------------------")
                        for t in tick_list:
                            print(f"{t.get('ticker','?'):<7} {t.get('recommendation','?')}")
                    overall = llm_parsed.get('overall')
                    if overall:
                        print("\nOverall Stance:", overall.get('stance'))
                        notes = overall.get('notes') or []
                        for n in notes[:5]:
                            print(" -", n)

                    if not args.summary_only:
                        # Show rationale details if available
                        for t in tick_list:
                            rationale = t.get('rationale') or []
                            if rationale:
                                print(f"\n{t.get('ticker')} Rationale:")
                                for r in rationale[:5]:
                                    print(" -", r)

            if not getattr(args, 'json', False) and result.get('errors'):
                analysis._print_warning("Non-fatal errors:")
                for k, v in result['errors'].items():
                    print(f"  {k}: {v}")

        elif args.command == 'av':
            # Alpha Vantage API commands
            if not args.av_command:
                av_parser.print_help()
                return

            try:
                av_analyzer = AlphaVantageAnalyzer()
            except ValueError as e:
                analysis._print_error(str(e))
                print("💡 Get your free API key from: https://www.alphavantage.co/support/#api-key")
                print("💡 Set it as an environment variable: export ALPHA_VANTAGE_API_KEY=your_key_here")
                return

            if args.av_command == 'news-sentiment':
                # Handle news sentiment analysis
                tickers = args.tickers if args.tickers else None
                topics = args.topics if hasattr(args, 'topics') and args.topics else None

                if not getattr(args, 'json', False):
                    analysis._print_header("ALPHA VANTAGE NEWS SENTIMENT ANALYSIS", "📰")
                    if tickers:
                        print(f"📊 Tickers: {', '.join(tickers)}")
                    if topics:
                        print(f"🗂️ Topics: {', '.join(topics)}")
                    if args.time_from:
                        print(f"📅 From: {args.time_from}")
                    if args.time_to:
                        print(f"📅 To: {args.time_to}")
                    print(f"🔢 Limit: {args.limit}")
                    print(f"📈 Sort: {args.sort}")
                    print()

                try:
                    news_data = av_analyzer.get_news_sentiment(
                        tickers=tickers,
                        topics=topics,
                        time_from=args.time_from,
                        time_to=args.time_to,
                        sort=args.sort,
                        limit=args.limit
                    )

                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "news-sentiment",
                            "tickers": tickers,
                            "topics": topics,
                            "time_from": args.time_from,
                            "time_to": args.time_to,
                            "limit": args.limit,
                            "sort": args.sort,
                            "data": news_data
                        }
                        print(json.dumps(result, indent=2))
                        return

                    # Display results
                    metadata = news_data.get('metadata', {})
                    feed = news_data.get('feed', [])

                    analysis._print_section_header("NEWS SUMMARY", "📊")
                    print(f"📄 Total Articles: {metadata.get('total_items', 0)}")
                    print(f"🎯 Tickers: {metadata.get('tickers', 'All')}")
                    print(f"🗂️ Topics: {metadata.get('topics', 'All')}")
                    print(f"📅 Date Range: {metadata.get('time_range', {}).get('from', 'Any')} to {metadata.get('time_range', {}).get('to', 'Now')}")
                    print()

                    if feed:
                        analysis._print_section_header("RECENT NEWS ARTICLES", "📰")
                        print("┌─────────────────────────────────────────────────────────────────────────────────────────────┐")
                        print("│ Title                                                                                       │")
                        print("├─────────────────────────────────────────────────────────────────────────────────────────────┤")

                        for i, item in enumerate(feed[:10], 1):  # Show first 10 articles
                            title = item.get('title', 'No title')[:85]
                            print(f"│ {i:2d}. {title:<83} │")

                        print("└─────────────────────────────────────────────────────────────────────────────────────────────┘")

                        # Show detailed sentiment for first few articles
                        analysis._print_section_header("SENTIMENT ANALYSIS", "📈")
                        print("┌─────────┬─────────────┬─────────────┬─────────────────┬─────────────────────────────┐")
                        print("│ Article │ Overall     │ Ticker      │ Relevance      │ Sentiment Label             │")
                        print("├─────────┼─────────────┼─────────────┼─────────────────┼─────────────────────────────┤")

                        for i, item in enumerate(feed[:5], 1):  # Show first 5 articles
                            overall_score = item.get('overall_sentiment_score', 0)
                            overall_label = item.get('overall_sentiment_label', 'N/A')

                            # Get primary ticker sentiment if available
                            ticker_sentiments = item.get('ticker_sentiment', [])
                            if ticker_sentiments:
                                primary_ticker = ticker_sentiments[0]
                                ticker = primary_ticker.get('ticker', 'N/A')
                                relevance = primary_ticker.get('relevance_score', 'N/A')
                                sentiment_label = primary_ticker.get('ticker_sentiment_label', 'N/A')
                            else:
                                ticker = 'N/A'
                                relevance = 'N/A'
                                sentiment_label = 'N/A'

                            print(f"│ {i:7d} │ {overall_score:>11.3f} │ {ticker:>10} │ {relevance:>14} │ {sentiment_label:>26} │")

                        print("└─────────┴─────────────┴─────────────┴─────────────────┴─────────────────────────────┘")

                        if args.analyze:
                            # Perform sentiment trend analysis
                            analysis_result = av_analyzer.analyze_sentiment_trends(news_data)
                            analysis._print_section_header("SENTIMENT TRENDS ANALYSIS", "📊")
                            print(f"📈 Overall Sentiment Trend: {analysis_result.get('sentiment_trend', 'N/A')}")
                            print(f"📊 Average Sentiment Score: {analysis_result.get('average_sentiment_score', 0):.3f}")
                            print(f"📰 Total Articles Analyzed: {analysis_result.get('total_articles', 0)}")

                            # Show sentiment distribution
                            distribution = analysis_result.get('sentiment_distribution', {})
                            if distribution:
                                print("\n📊 Sentiment Distribution:")
                                for sentiment, count in distribution.items():
                                    percentage = (count / analysis_result.get('total_articles', 1)) * 100
                                    print(f"   {sentiment}: {count} articles ({percentage:.1f}%)")

                            # Show ticker-specific sentiment
                            ticker_sentiment = analysis_result.get('ticker_specific_sentiment', {})
                            if ticker_sentiment:
                                analysis._print_section_header("TICKER-SPECIFIC SENTIMENT", "📈")
                                print("┌─────────┬─────────────────┬─────────────────┬─────────────┐")
                                print("│ Ticker  │ Avg Sentiment   │ Article Count   │ Trend       │")
                                print("├─────────┼─────────────────┼─────────────────┼─────────────┤")

                                for ticker, data in ticker_sentiment.items():
                                    avg_score = data.get('average_score', 0)
                                    count = data.get('article_count', 0)
                                    trend = data.get('sentiment_trend', 'N/A')
                                    print(f"│ {ticker:7} │ {avg_score:>15.3f} │ {count:>14} │ {trend:>10} │")

                                print("└─────────┴─────────────────┴─────────────────┴─────────────┘")

                    analysis._print_success("News sentiment analysis completed!")

                except Exception as e:
                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "news-sentiment",
                            "tickers": tickers,
                            "topics": topics,
                            "time_from": args.time_from,
                            "time_to": args.time_to,
                            "limit": args.limit,
                            "sort": args.sort,
                            "errors": [str(e)]
                        }
                        print(json.dumps(result, indent=2))
                    else:
                        analysis._print_error(f"Failed to fetch news sentiment: {str(e)}")

            elif args.av_command == 'overview':
                # Handle company overview
                if not getattr(args, 'json', False):
                    analysis._print_header(f"ALPHA VANTAGE COMPANY OVERVIEW: {args.symbol.upper()}", "📊")

                try:
                    overview_data = av_analyzer.get_company_overview(args.symbol)

                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "overview",
                            "symbol": args.symbol,
                            "data": overview_data
                        }
                        print(json.dumps(result, indent=2))
                        return

                    analysis._print_section_header("COMPANY INFORMATION", "🏢")
                    print(f"🏷️ Symbol: {overview_data.get('symbol', 'N/A')}")
                    print(f"🏢 Name: {overview_data.get('name', 'N/A')}")
                    print(f"🌍 Exchange: {overview_data.get('exchange', 'N/A')}")
                    print(f"🇺🇸 Country: {overview_data.get('country', 'N/A')}")
                    print(f"🏭 Sector: {overview_data.get('sector', 'N/A')}")
                    print(f"🏭 Industry: {overview_data.get('industry', 'N/A')}")

                    analysis._print_section_header("FINANCIAL METRICS", "💰")
                    print(f"💵 Market Cap: {overview_data.get('market_capitalization', 'N/A')}")
                    print(f"💰 EBITDA: {overview_data.get('ebitda', 'N/A')}")
                    print(f"📊 PE Ratio: {overview_data.get('pe_ratio', 'N/A')}")
                    print(f"💹 EPS: {overview_data.get('eps', 'N/A')}")
                    print(f"💰 Dividend Yield: {overview_data.get('dividend_yield', 'N/A')}")
                    print(f"📈 52W High: {overview_data.get('52_week_high', 'N/A')}")
                    print(f"📉 52W Low: {overview_data.get('52_week_low', 'N/A')}")

                    analysis._print_section_header("ANALYST RECOMMENDATIONS", "🎯")
                    print(f"🟢 Strong Buy: {overview_data.get('analyst_rating_strong_buy', 'N/A')}")
                    print(f"🟢 Buy: {overview_data.get('analyst_rating_buy', 'N/A')}")
                    print(f"🟡 Hold: {overview_data.get('analyst_rating_hold', 'N/A')}")
                    print(f"🔴 Sell: {overview_data.get('analyst_rating_sell', 'N/A')}")
                    print(f"🔴 Strong Sell: {overview_data.get('analyst_rating_strong_sell', 'N/A')}")
                    print(f"🎯 Target Price: {overview_data.get('analyst_target_price', 'N/A')}")

                    analysis._print_success("Company overview retrieved successfully!")

                except Exception as e:
                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "overview",
                            "symbol": args.symbol,
                            "errors": [str(e)]
                        }
                        print(json.dumps(result, indent=2))
                    else:
                        analysis._print_error(f"Failed to fetch company overview: {str(e)}")

            elif args.av_command == 'quote':
                # Handle global quote
                if not getattr(args, 'json', False):
                    analysis._print_header(f"ALPHA VANTAGE GLOBAL QUOTE: {args.symbol.upper()}", "💰")

                try:
                    quote_data = av_analyzer.get_global_quote(args.symbol)

                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "quote",
                            "symbol": args.symbol,
                            "data": quote_data
                        }
                        print(json.dumps(result, indent=2))
                        return

                    analysis._print_section_header("QUOTE INFORMATION", "💹")
                    print(f"🏷️ Symbol: {quote_data.get('symbol', 'N/A')}")
                    print(f"💵 Price: ${quote_data.get('price', 'N/A')}")
                    print(f"📈 Open: ${quote_data.get('open', 'N/A')}")
                    print(f"📊 High: ${quote_data.get('high', 'N/A')}")
                    print(f"📉 Low: ${quote_data.get('low', 'N/A')}")
                    print(f"📅 Previous Close: ${quote_data.get('previous_close', 'N/A')}")
                    print(f"📊 Volume: {quote_data.get('volume', 'N/A')}")
                    print(f"📅 Latest Trading Day: {quote_data.get('latest_trading_day', 'N/A')}")

                    # Calculate change
                    try:
                        change = float(quote_data.get('change', 0))
                        change_pct = quote_data.get('change_percent', '0%').strip('%')
                        change_pct_val = float(change_pct)

                        if change >= 0:
                            print(f"📈 Change: +${change:.2f} (+{change_pct}%) 🟢")
                        else:
                            print(f"📉 Change: -${abs(change):.2f} ({change_pct}%) 🔴")
                    except (ValueError, TypeError):
                        print(f"📊 Change: {quote_data.get('change', 'N/A')} ({quote_data.get('change_percent', 'N/A')})")

                    analysis._print_success("Quote data retrieved successfully!")

                except Exception as e:
                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "quote",
                            "symbol": args.symbol,
                            "errors": [str(e)]
                        }
                        print(json.dumps(result, indent=2))
                    else:
                        analysis._print_error(f"Failed to fetch quote: {str(e)}")

            elif args.av_command == 'income-statement':
                # Handle income statement
                annual = not getattr(args, 'quarterly', False)
                if not getattr(args, 'json', False):
                    analysis._print_header(f"ALPHA VANTAGE INCOME STATEMENT: {args.symbol.upper()}", "💼")
                    print(f"📊 Period: {'Annual' if annual else 'Quarterly'}")

                try:
                    income_data = av_analyzer.get_income_statement(args.symbol, annual=annual)

                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "income-statement",
                            "symbol": args.symbol,
                            "period": "annual" if annual else "quarterly",
                            "data": income_data
                        }
                        print(json.dumps(result, indent=2))
                        return

                    # This would display the income statement data
                    # For brevity, showing basic structure
                    analysis._print_section_header("INCOME STATEMENT DATA", "📋")
                    print("💡 Income statement data retrieved successfully!")
                    print("📄 Use this data for detailed financial analysis")

                    analysis._print_success("Income statement retrieved successfully!")

                except Exception as e:
                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "income-statement",
                            "symbol": args.symbol,
                            "period": "annual" if annual else "quarterly",
                            "errors": [str(e)]
                        }
                        print(json.dumps(result, indent=2))
                    else:
                        analysis._print_error(f"Failed to fetch income statement: {str(e)}")

            elif args.av_command == 'balance-sheet':
                # Handle balance sheet
                annual = not getattr(args, 'quarterly', False)
                if not getattr(args, 'json', False):
                    analysis._print_header(f"ALPHA VANTAGE BALANCE SHEET: {args.symbol.upper()}", "🏦")
                    print(f"📊 Period: {'Annual' if annual else 'Quarterly'}")

                try:
                    balance_data = av_analyzer.get_balance_sheet(args.symbol, annual=annual)

                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "balance-sheet",
                            "symbol": args.symbol,
                            "period": "annual" if annual else "quarterly",
                            "data": balance_data
                        }
                        print(json.dumps(result, indent=2))
                        return

                    analysis._print_section_header("BALANCE SHEET DATA", "📋")
                    print("💡 Balance sheet data retrieved successfully!")
                    print("📄 Use this data for detailed financial analysis")

                    analysis._print_success("Balance sheet retrieved successfully!")

                except Exception as e:
                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "balance-sheet",
                            "symbol": args.symbol,
                            "period": "annual" if annual else "quarterly",
                            "errors": [str(e)]
                        }
                        print(json.dumps(result, indent=2))
                    else:
                        analysis._print_error(f"Failed to fetch balance sheet: {str(e)}")

            elif args.av_command == 'cash-flow':
                # Handle cash flow
                annual = not getattr(args, 'quarterly', False)
                if not getattr(args, 'json', False):
                    analysis._print_header(f"ALPHA VANTAGE CASH FLOW: {args.symbol.upper()}", "💵")
                    print(f"📊 Period: {'Annual' if annual else 'Quarterly'}")

                try:
                    cashflow_data = av_analyzer.get_cash_flow(args.symbol, annual=annual)

                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "cash-flow",
                            "symbol": args.symbol,
                            "period": "annual" if annual else "quarterly",
                            "data": cashflow_data
                        }
                        print(json.dumps(result, indent=2))
                        return

                    analysis._print_section_header("CASH FLOW DATA", "📋")
                    print("💡 Cash flow data retrieved successfully!")
                    print("📄 Use this data for detailed financial analysis")

                    analysis._print_success("Cash flow statement retrieved successfully!")

                except Exception as e:
                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "cash-flow",
                            "symbol": args.symbol,
                            "period": "annual" if annual else "quarterly",
                            "errors": [str(e)]
                        }
                        print(json.dumps(result, indent=2))
                    else:
                        analysis._print_error(f"Failed to fetch cash flow: {str(e)}")

            elif args.av_command == 'earnings':
                # Handle earnings
                if not getattr(args, 'json', False):
                    analysis._print_header(f"ALPHA VANTAGE EARNINGS: {args.symbol.upper()}", "📈")

                try:
                    earnings_data = av_analyzer.get_earnings(args.symbol)

                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "earnings",
                            "symbol": args.symbol,
                            "data": earnings_data
                        }
                        print(json.dumps(result, indent=2))
                        return

                    analysis._print_section_header("EARNINGS DATA", "📋")
                    print("💡 Earnings data retrieved successfully!")
                    print("📄 Use this data for detailed financial analysis")

                    analysis._print_success("Earnings data retrieved successfully!")

                except Exception as e:
                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "earnings",
                            "symbol": args.symbol,
                            "errors": [str(e)]
                        }
                        print(json.dumps(result, indent=2))
                    else:
                        analysis._print_error(f"Failed to fetch earnings: {str(e)}")

            elif args.av_command == 'top-gainers-losers':
                # Handle top gainers and losers
                if not getattr(args, 'json', False):
                    analysis._print_header("ALPHA VANTAGE TOP GAINERS, LOSERS & MOST ACTIVE", "📊")

                try:
                    gainers_losers_data = av_analyzer.get_top_gainers_losers()

                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "top-gainers-losers",
                            "data": gainers_losers_data
                        }
                        print(json.dumps(result, indent=2))
                        return

                    analysis._print_section_header("TOP GAINERS", "📈")
                    if gainers_losers_data['top_gainers']:
                        print("🏆 Top 20 Gainers:")
                        print("-" * 80)
                        print(f"{'Symbol':<10} {'Price':<10} {'Change':<12} {'Change %':<12} {'Volume':<15}")
                        print("-" * 80)
                        for gainer in gainers_losers_data['top_gainers'][:20]:
                            symbol = gainer.get('ticker', 'N/A')
                            price = gainer.get('price', 'N/A')
                            change = gainer.get('change_amount', 'N/A')
                            change_pct = gainer.get('change_percentage', 'N/A')
                            volume = gainer.get('volume', 'N/A')
                            print(f"{symbol:<10} {price:<10} {change:<12} {change_pct:<12} {volume:<15}")
                    else:
                        print("No gainers data available")

                    analysis._print_section_header("TOP LOSERS", "📉")
                    if gainers_losers_data['top_losers']:
                        print("💔 Top 20 Losers:")
                        print("-" * 80)
                        print(f"{'Symbol':<10} {'Price':<10} {'Change':<12} {'Change %':<12} {'Volume':<15}")
                        print("-" * 80)
                        for loser in gainers_losers_data['top_losers'][:20]:
                            symbol = loser.get('ticker', 'N/A')
                            price = loser.get('price', 'N/A')
                            change = loser.get('change_amount', 'N/A')
                            change_pct = loser.get('change_percentage', 'N/A')
                            volume = loser.get('volume', 'N/A')
                            print(f"{symbol:<10} {price:<10} {change:<12} {change_pct:<12} {volume:<15}")
                    else:
                        print("No losers data available")

                    analysis._print_section_header("MOST ACTIVELY TRADED", "🔥")
                    if gainers_losers_data['most_actively_traded']:
                        print("🚀 Most Active:")
                        print("-" * 80)
                        print(f"{'Symbol':<10} {'Price':<10} {'Change':<12} {'Change %':<12} {'Volume':<15}")
                        print("-" * 80)
                        for active in gainers_losers_data['most_actively_traded'][:20]:
                            symbol = active.get('ticker', 'N/A')
                            price = active.get('price', 'N/A')
                            change = active.get('change_amount', 'N/A')
                            change_pct = active.get('change_percentage', 'N/A')
                            volume = active.get('volume', 'N/A')
                            print(f"{symbol:<10} {price:<10} {change:<12} {change_pct:<12} {volume:<15}")
                    else:
                        print("No most active data available")

                    analysis._print_success("Top gainers, losers, and most active data retrieved successfully!")

                except Exception as e:
                    if getattr(args, 'json', False):
                        import json
                        result = {
                            "command": "av",
                            "subcommand": "top-gainers-losers",
                            "errors": [str(e)]
                        }
                        print(json.dumps(result, indent=2))
                    else:
                        analysis._print_error(f"Failed to fetch top gainers/losers: {str(e)}")

            else:
                av_parser.print_help()

        elif args.command == 'ingest':
            # Event ingestion command
            try:
                from ingest_events import import_events_from_json, process_ingest_folder, monitor_ingest_folder
            except ImportError:
                analysis._print_error("Could not import ingestion module. Make sure ingest_events.py is available.")
                return

            skip_duplicates = not getattr(args, 'no_skip_duplicates', False)

            if args.file:
                # Import specific file
                analysis._print_header(f"EVENT DATA INGESTION: {args.file}", "📥")
                imported_count = import_events_from_json(args.file, skip_duplicates=skip_duplicates)
                if imported_count > 0:
                    analysis._print_success(f"Successfully imported {imported_count} events from {args.file}")
                else:
                    analysis._print_warning(f"No events imported from {args.file}")

            elif args.monitor:
                # Monitor folder continuously
                analysis._print_header("EVENT INGESTION MONITOR", "📡")
                print(f"📁 Ingest Directory: {args.ingest_dir}")
                print(f"📁 Processed Directory: {args.ingested_dir}")
                print(f"⏱️ Monitoring Interval: {args.interval} seconds")
                print(f"🔄 Skip Duplicates: {skip_duplicates}")
                print()
                print("🚀 Starting continuous monitoring... (Press Ctrl+C to stop)")
                monitor_ingest_folder(
                    ingest_dir=args.ingest_dir,
                    ingested_dir=args.ingested_dir,
                    interval=args.interval,
                    skip_duplicates=skip_duplicates
                )

            else:
                # Process folder once (default)
                analysis._print_header("EVENT INGESTION PROCESSING", "📥")
                print(f"📁 Ingest Directory: {args.ingest_dir}")
                print(f"📁 Processed Directory: {args.ingested_dir}")
                print(f"🔄 Skip Duplicates: {skip_duplicates}")
                print()

                total_imported = process_ingest_folder(
                    ingest_dir=args.ingest_dir,
                    ingested_dir=args.ingested_dir,
                    skip_duplicates=skip_duplicates
                )

                if total_imported > 0:
                    analysis._print_success(f"Successfully processed {total_imported} events")
                else:
                    analysis._print_warning("No events were processed")

    except KeyboardInterrupt:
        analysis._print_warning("Operation cancelled by user")
    except Exception as e:
        analysis._print_error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
