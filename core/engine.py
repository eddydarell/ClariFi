#!/usr/bin/env python3
"""
Enhanced ClariFi Engine with Database Integration
"""

import os
import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Optional

# Add the current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import database models
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from database.models import DatabaseManager, Portfolio, AnalysisResult, CommandHistory, ComparisonResult

# Import existing analysis modules
from stock_downloader import StockDownloader
from stock_visualizer import StockVisualizer
from pattern_analyzer import PatternAnalyzer
from event_correlator import EventCorrelator
from advanced_visualizer import AdvancedVisualizer
from options_analyzer import OptionsAnalyzer, InvestmentAdvisor
from seasonal_analyzer import SeasonalAnalyzer
from ml_analyzer import MLAnalyzer


class ClariFiEngine:
    """Enhanced ClariFi Engine with database integration and comprehensive analysis"""

    def __init__(self, db_path: str = "clarifi.db"):
        # Initialize database
        self.db_manager = DatabaseManager(db_path)
        self.portfolio_model = Portfolio(self.db_manager)
        self.analysis_model = AnalysisResult(self.db_manager)
        self.command_model = CommandHistory(self.db_manager)
        self.comparison_model = ComparisonResult(self.db_manager)

        # Initialize analysis modules
        self.downloader = StockDownloader()
        self.visualizer = StockVisualizer()
        self.pattern_analyzer = PatternAnalyzer()
        self.event_correlator = EventCorrelator()
        self.advanced_visualizer = AdvancedVisualizer()
        self.options_analyzer = OptionsAnalyzer()
        self.investment_advisor = InvestmentAdvisor()
        self.seasonal_analyzer = SeasonalAnalyzer()
        self.ml_analyzer = MLAnalyzer()

    def _make_json_serializable(self, obj):
        """Convert pandas objects and numpy types to JSON-serializable Python types."""
        try:
            if obj is None:
                return None
            elif isinstance(obj, pd.Series):
                # Convert Series to dict with string keys to avoid serialization issues
                try:
                    # Handle datetime index specially
                    if isinstance(obj.index, pd.DatetimeIndex):
                        return {str(k): self._make_json_serializable(v) for k, v in obj.to_dict().items()}
                    else:
                        return {str(k): self._make_json_serializable(v) for k, v in obj.to_dict().items()}
                except Exception:
                    # Fallback to list if to_dict() fails
                    try:
                        return [self._make_json_serializable(item) for item in obj.tolist()]
                    except Exception:
                        return str(obj)
            elif isinstance(obj, pd.DataFrame):
                try:
                    records = obj.to_dict(orient='records')
                    return [self._make_json_serializable(record) for record in records]
                except Exception:
                    # Fallback to dict conversion
                    try:
                        return self._make_json_serializable(obj.to_dict())
                    except Exception:
                        return str(obj)
            elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
                return str(obj)
            elif isinstance(obj, (datetime, timedelta)):
                return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
            elif isinstance(obj, int):
                return obj
            elif isinstance(obj, float):
                if np.isnan(obj) or np.isinf(obj):
                    return None
                return obj
            elif isinstance(obj, np.generic):
                val = obj.item()
                if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
                    return None
                return val
            elif isinstance(obj, np.ndarray):
                try:
                    return [self._make_json_serializable(item) for item in obj.tolist()]
                except Exception:
                    return str(obj)
            elif isinstance(obj, (np.bool_, bool)):
                return bool(obj)
            elif isinstance(obj, (np.str_, str)):
                return str(obj)
            elif isinstance(obj, bytes):
                return obj.decode('utf-8', errors='ignore')
            elif isinstance(obj, dict):
                try:
                    return {str(key): self._make_json_serializable(value) for key, value in obj.items()}
                except Exception:
                    return str(obj)
            elif isinstance(obj, (list, tuple, set)):
                try:
                    return [self._make_json_serializable(item) for item in obj]
                except Exception:
                    return str(obj)
            elif hasattr(obj, '__dict__'):
                # Handle custom class objects by converting their attributes to dict
                try:
                    result = {}
                    for attr in dir(obj):
                        if not attr.startswith('_'):
                            try:
                                value = getattr(obj, attr)
                                if not callable(value):
                                    result[attr] = self._make_json_serializable(value)
                            except Exception:
                                continue
                    return result
                except Exception:
                    return str(obj)
            else:
                # Try to convert to string if all else fails
                try:
                    # Check if it's JSON serializable first
                    import json
                    json.dumps(obj)
                    return obj
                except (TypeError, ValueError):
                    return str(obj)
        except Exception:
            # Ultimate fallback
            return str(obj)

    def log_command(self, command: str, parameters: Dict[str, Any] = None) -> str:
        """Log command execution"""
        return self.command_model.log_command(
            command=command,
            parameters=parameters,
            status="STARTED"
        )

    def update_command_status(self, command_id: str, status: str,
                            execution_time: float = 0.0, output: str = "",
                            error_message: str = ""):
        """Update command execution status"""
        return self.command_model.update_status(
            command_id, status, execution_time, output, error_message
        )

    # Portfolio Management
    def create_portfolio(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new portfolio"""
        command_id = self.log_command("create_portfolio", {"name": name, "description": description})
        try:
            portfolio_id = self.portfolio_model.create(name, description)
            return {
                "success": True,
                "portfolio_id": portfolio_id,
                "message": f"Portfolio '{name}' created successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create portfolio: {str(e)}"
            }

    def get_portfolios(self) -> List[Dict[str, Any]]:
        """Get all portfolios"""
        return self.portfolio_model.get_all()

    def get_portfolio_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get portfolio by name"""
        return self.portfolio_model.get_by_name(name)

    def update_portfolio(self, portfolio_id: str, name: str = None, description: str = None) -> Dict[str, Any]:
        """Update portfolio name and/or description"""
        command_id = self.log_command("update_portfolio", {
            "portfolio_id": portfolio_id,
            "name": name,
            "description": description
        })

        try:
            # Check if portfolio exists
            portfolio = self.portfolio_model.get_by_id(portfolio_id)
            if not portfolio:
                return {
                    "success": False,
                    "error": "Portfolio not found",
                    "message": f"Portfolio with ID {portfolio_id} does not exist"
                }

            # Update portfolio
            success = self.portfolio_model.update(portfolio_id, name, description)
            if success:
                return {
                    "success": True,
                    "message": f"Portfolio updated successfully",
                    "portfolio_id": portfolio_id
                }
            else:
                return {
                    "success": False,
                    "error": "No changes made",
                    "message": "No valid fields provided for update"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update portfolio: {str(e)}"
            }

    def delete_portfolio(self, portfolio_id: str, confirmation_name: str) -> Dict[str, Any]:
        """Delete a portfolio with name confirmation"""
        command_id = self.log_command("delete_portfolio", {
            "portfolio_id": portfolio_id,
            "confirmation_provided": bool(confirmation_name)
        })

        try:
            # Check if portfolio exists
            portfolio = self.portfolio_model.get_by_id(portfolio_id)
            if not portfolio:
                return {
                    "success": False,
                    "error": "Portfolio not found",
                    "message": f"Portfolio with ID {portfolio_id} does not exist"
                }

            # Verify confirmation name (case sensitive)
            if confirmation_name != portfolio["name"]:
                return {
                    "success": False,
                    "error": "Name confirmation failed",
                    "message": f"Please type the exact portfolio name '{portfolio['name']}' to confirm deletion",
                    "warning": "⚠️  Portfolio deletion is irreversible and will remove all associated data!"
                }

            # Get tickers count for warning message
            tickers = self.portfolio_model.get_tickers(portfolio_id)
            ticker_count = len(tickers)

            # Delete portfolio
            success = self.portfolio_model.delete(portfolio_id)
            if success:
                return {
                    "success": True,
                    "message": f"Portfolio '{portfolio['name']}' deleted successfully",
                    "deleted_tickers": ticker_count,
                    "portfolio_id": portfolio_id
                }
            else:
                return {
                    "success": False,
                    "error": "Deletion failed",
                    "message": "Failed to delete portfolio from database"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete portfolio: {str(e)}"
            }

    def sync_portfolio_prices(self, portfolio_id: str) -> Dict[str, Any]:
        """Sync portfolio by fetching the most recent prices for all tickers"""
        command_id = self.log_command("sync_portfolio", {"portfolio_id": portfolio_id})
        start_time = time.time()

        try:
            # Check if portfolio exists
            portfolio = self.portfolio_model.get_by_id(portfolio_id)
            if not portfolio:
                return {
                    "success": False,
                    "error": "Portfolio not found",
                    "message": f"Portfolio with ID {portfolio_id} does not exist"
                }

            # Get all tickers in portfolio
            tickers = self.portfolio_model.get_tickers(portfolio_id)
            if not tickers:
                return {
                    "success": True,
                    "message": "No tickers in portfolio to sync",
                    "portfolio_name": portfolio["name"],
                    "synced_tickers": 0
                }

            sync_results = {}
            successful_syncs = 0
            failed_syncs = 0

            print(f"\n🔄 Syncing prices for portfolio '{portfolio['name']}'...")

            for ticker_data in tickers:
                ticker = ticker_data["ticker"]
                try:
                    print(f"📥 Fetching current price for {ticker}...")

                    # Download recent data (1 day to get latest price)
                    stock_data = self.downloader.download_stock_data(ticker, None, None, period="1d")

                    if stock_data is not None and not stock_data.empty:
                        # Get the most recent closing price
                        latest_price = float(stock_data['Close'].iloc[-1])

                        # Update the price in database
                        update_success = self.portfolio_model.update_ticker_price(
                            portfolio_id, ticker, latest_price
                        )

                        if update_success:
                            sync_results[ticker] = {
                                "success": True,
                                "previous_price": ticker_data.get("current_price", 0.0),
                                "current_price": latest_price,
                                "price_change": latest_price - ticker_data.get("current_price", 0.0),
                                "price_change_pct": ((latest_price / ticker_data.get("current_price", latest_price)) - 1) * 100 if ticker_data.get("current_price", 0) > 0 else 0.0
                            }
                            successful_syncs += 1
                            print(f"✅ {ticker}: ${latest_price:.2f}")
                        else:
                            sync_results[ticker] = {
                                "success": False,
                                "error": "Database update failed"
                            }
                            failed_syncs += 1
                    else:
                        sync_results[ticker] = {
                            "success": False,
                            "error": "No price data available"
                        }
                        failed_syncs += 1
                        print(f"❌ {ticker}: Failed to fetch price data")

                except Exception as e:
                    sync_results[ticker] = {
                        "success": False,
                        "error": str(e)
                    }
                    failed_syncs += 1
                    print(f"❌ {ticker}: {str(e)}")

            execution_time = time.time() - start_time

            return {
                "success": True,
                "message": f"Portfolio sync completed",
                "portfolio_name": portfolio["name"],
                "portfolio_id": portfolio_id,
                "total_tickers": len(tickers),
                "successful_syncs": successful_syncs,
                "failed_syncs": failed_syncs,
                "sync_results": sync_results,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to sync portfolio: {str(e)}",
                "execution_time": execution_time
            }

    def add_ticker_to_portfolio(self, portfolio_id: str, ticker: str,
                               quantity: float = 0.0, avg_cost: float = 0.0) -> Dict[str, Any]:
        """Add a ticker to a portfolio"""
        command_id = self.log_command("add_ticker", {
            "portfolio_id": portfolio_id,
            "ticker": ticker,
            "quantity": quantity,
            "avg_cost": avg_cost
        })

        try:
            ticker_id = self.portfolio_model.add_ticker(portfolio_id, ticker, quantity, avg_cost)
            return {
                "success": True,
                "ticker_id": ticker_id,
                "message": f"Ticker {ticker} added to portfolio successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to add ticker: {str(e)}"
            }

    def remove_ticker_from_portfolio(self, portfolio_id: str, ticker: str) -> Dict[str, Any]:
        """Remove a ticker from a portfolio"""
        command_id = self.log_command("remove_ticker", {
            "portfolio_id": portfolio_id,
            "ticker": ticker
        })

        try:
            success = self.portfolio_model.remove_ticker(portfolio_id, ticker)
            if success:
                return {
                    "success": True,
                    "message": f"Ticker {ticker} removed from portfolio successfully"
                }
            else:
                return {
                    "success": False,
                    "message": f"Ticker {ticker} not found in portfolio"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to remove ticker: {str(e)}"
            }

    def get_portfolio_tickers(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """Get all tickers in a portfolio"""
        return self.portfolio_model.get_tickers(portfolio_id)

    def update_ticker_in_portfolio(self, portfolio_id: str, ticker: str,
                                 quantity: float = None, avg_cost: float = None) -> Dict[str, Any]:
        """Update ticker quantity and/or average cost in a portfolio"""
        command_id = self.log_command("update_ticker", {
            "portfolio_id": portfolio_id,
            "ticker": ticker,
            "quantity": quantity,
            "avg_cost": avg_cost
        })

        try:
            # Validate that at least one field is provided
            if quantity is None and avg_cost is None:
                return {
                    "success": False,
                    "error": "No updates provided",
                    "message": "At least one of quantity or avg_cost must be provided"
                }

            # Check if portfolio exists
            portfolio = self.portfolio_model.get_by_id(portfolio_id)
            if not portfolio:
                return {
                    "success": False,
                    "error": "Portfolio not found",
                    "message": f"Portfolio with ID {portfolio_id} does not exist"
                }

            # Check if ticker exists in portfolio
            tickers = self.portfolio_model.get_tickers(portfolio_id)
            ticker_exists = any(t['ticker'].upper() == ticker.upper() for t in tickers)
            if not ticker_exists:
                return {
                    "success": False,
                    "error": "Ticker not found",
                    "message": f"Ticker {ticker.upper()} not found in portfolio"
                }

            # Update the ticker
            success = self.portfolio_model.update_ticker(portfolio_id, ticker, quantity, avg_cost)
            if success:
                response = {
                    "success": True,
                    "message": f"Ticker {ticker.upper()} updated successfully",
                    "ticker": ticker.upper()
                }
                if quantity is not None:
                    response["new_quantity"] = quantity
                if avg_cost is not None:
                    response["new_avg_cost"] = avg_cost
                return response
            else:
                return {
                    "success": False,
                    "error": "Update failed",
                    "message": "Failed to update ticker in database"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update ticker: {str(e)}"
            }

    def get_portfolio_info(self, portfolio_id: str) -> Dict[str, Any]:
        """Get comprehensive portfolio information"""
        command_id = self.log_command("get_portfolio_info", {"portfolio_id": portfolio_id})

        try:
            # Get comprehensive portfolio information from database
            portfolio_info = self.portfolio_model.get_portfolio_info(portfolio_id)

            if "error" in portfolio_info:
                return {
                    "success": False,
                    "error": portfolio_info["error"],
                    "message": portfolio_info["error"]
                }

            # Update current prices for all tickers if needed
            for ticker_info in portfolio_info['tickers']:
                ticker = ticker_info['ticker']
                try:
                    # Get latest price data using period parameter with None for start/end dates
                    stock_data = self.downloader.download_stock_data(ticker, None, None, period="1d")
                    if stock_data is not None and not stock_data.empty:
                        current_price = float(stock_data['Close'].iloc[-1])
                        # Update price in database
                        self.portfolio_model.update_ticker_price(portfolio_id, ticker, current_price)
                        # Update the info with fresh price
                        ticker_info['current_price'] = current_price
                        if ticker_info['quantity']:
                            ticker_info['current_value'] = current_price * ticker_info['quantity']
                            if ticker_info['avg_cost']:
                                ticker_info['unrealized_pnl'] = (current_price - ticker_info['avg_cost']) * ticker_info['quantity']
                                ticker_info['percentage_change'] = ((current_price - ticker_info['avg_cost']) / ticker_info['avg_cost']) * 100
                except Exception as price_error:
                    print(f"Warning: Could not update price for {ticker}: {price_error}")

            # Recalculate summary with updated prices
            total_current_value = sum(t.get('current_value', 0) or 0 for t in portfolio_info['tickers'])
            total_cost = sum(t.get('total_cost', 0) or 0 for t in portfolio_info['tickers'])
            total_unrealized_pnl = sum(t.get('unrealized_pnl', 0) or 0 for t in portfolio_info['tickers'])
            portfolio_percentage_change = 0
            if total_cost > 0:
                portfolio_percentage_change = ((total_current_value - total_cost) / total_cost) * 100

            portfolio_info['summary'] = {
                'total_tickers': len(portfolio_info['tickers']),
                'total_current_value': round(total_current_value, 2),
                'total_cost': round(total_cost, 2),
                'total_unrealized_pnl': round(total_unrealized_pnl, 2),
                'portfolio_percentage_change': round(portfolio_percentage_change, 2)
            }

            return {
                "success": True,
                "data": portfolio_info
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get portfolio info: {str(e)}"
            }

    def get_portfolio_analytics(self, portfolio_id: str) -> Dict[str, Any]:
        """Get advanced portfolio analytics and insights"""
        command_id = self.log_command("get_portfolio_analytics", {"portfolio_id": portfolio_id})

        try:
            analytics = self.portfolio_model.get_portfolio_analytics(portfolio_id)

            return {
                "success": True,
                "data": analytics
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get portfolio analytics: {str(e)}"
            }

    # Analysis Methods
    def comprehensive_analysis(self, tickers: List[str], portfolio_id: str = None,
                             period: str = "1y", save_to_db: bool = True,
                             include_patterns: bool = True, include_events: bool = True,
                             include_options: bool = True, include_seasonal: bool = True,
                             include_ml: bool = False, include_deep: bool = False, deep_chunk_months: int = 3) -> Dict[str, Any]:
        """Perform comprehensive analysis on tickers"""

        command_id = self.log_command("comprehensive_analysis", {
            "tickers": tickers,
            "portfolio_id": portfolio_id,
            "period": period,
            "include_patterns": include_patterns,
            "include_events": include_events,
            "include_options": include_options,
            "include_seasonal": include_seasonal,
            "include_ml": include_ml,
            "include_deep": include_deep,
            "deep_chunk_months": deep_chunk_months
        })

        start_time = time.time()
        results = {}

        try:
            for ticker in tickers:
                try:
                    print(f"\n🔍 Analyzing {ticker}...")
                    ticker_results = {}

                    # Download data
                    print(f"📥 Downloading data for {ticker}...")
                    stock_data = self.downloader.download_stock_data(ticker, None, None, period=period)

                    if stock_data is None:
                        print(f"⚠️  Warning: No data found for ticker {ticker}")
                        ticker_results["error"] = f"Failed to download data for {ticker}"
                        results[ticker] = ticker_results
                        continue

                    # Save the downloaded data for analysis
                    saved_file = self.downloader.save_to_csv(stock_data, ticker)
                    if not saved_file:
                        print(f"⚠️  Warning: Failed to save data for {ticker}")
                        ticker_results["error"] = f"Failed to save data for {ticker}"
                        results[ticker] = ticker_results
                        continue

                    # Pattern Analysis
                    if include_patterns:
                        print(f"📊 Running pattern analysis for {ticker}...")
                        try:
                            stock_data_dict = {ticker: stock_data}
                            pattern_data = self.pattern_analyzer.analyze_correlation_patterns(stock_data_dict)
                            # Ensure JSON serializable
                            ticker_results["patterns"] = self._make_json_serializable(pattern_data)
                        except Exception as e:
                            print(f"⚠️  Pattern analysis failed for {ticker}: {str(e)}")
                            ticker_results["patterns"] = {"error": f"Pattern analysis failed: {str(e)}"}

                    # Event Correlation
                    if include_events:
                        print(f"📰 Running event correlation analysis for {ticker}...")
                        try:
                            stock_data_dict = {ticker: stock_data}
                            event_data = self.event_correlator.correlate_events_with_movements(stock_data_dict)
                            # Ensure JSON serializable
                            ticker_results["events"] = self._make_json_serializable(event_data)
                        except Exception as e:
                            print(f"⚠️  Event analysis failed for {ticker}: {str(e)}")
                            ticker_results["events"] = {"error": f"Event analysis failed: {str(e)}"}

                    # Options Analysis
                    if include_options:
                        print(f"⚖️ Running options analysis for {ticker}...")
                        try:
                            options_data = self.options_analyzer.analyze_options(ticker, stock_data)
                            # Ensure JSON serializable
                            ticker_results["options"] = self._make_json_serializable(options_data)
                        except Exception as e:
                            print(f"⚠️  Options analysis failed for {ticker}: {str(e)}")
                            ticker_results["options"] = {"error": f"Options analysis failed: {str(e)}"}

                        try:
                            investment_advice = self.investment_advisor.generate_investment_suggestion(stock_data)
                            # Ensure JSON serializable
                            ticker_results["investment_advice"] = self._make_json_serializable(investment_advice)
                        except Exception as e:
                            print(f"⚠️  Investment advice failed for {ticker}: {str(e)}")
                            ticker_results["investment_advice"] = {"error": f"Investment advice failed: {str(e)}"}

                    # Seasonal Analysis
                    if include_seasonal:
                        print(f"🗓️ Running seasonal analysis for {ticker}...")
                        try:
                            seasonal_data = self.seasonal_analyzer.analyze(stock_data)
                            # Ensure JSON serializable
                            ticker_results["seasonal"] = self._make_json_serializable(seasonal_data)
                        except Exception as e:
                            print(f"⚠️  Seasonal analysis failed for {ticker}: {str(e)}")
                            ticker_results["seasonal"] = {"error": f"Seasonal analysis failed: {str(e)}"}

                    # ML Analysis
                    if include_ml:
                        print(f"🤖 Running ML analysis for {ticker}...")
                        try:
                            ml_data = self.ml_analyzer.analyze(stock_data, ticker, prediction_horizon=5)
                            # Ensure JSON serializable
                            ticker_results["ml_analysis"] = self._make_json_serializable(ml_data)
                        except Exception as e:
                            print(f"⚠️  ML analysis failed for {ticker}: {str(e)}")
                            ticker_results["ml_analysis"] = {"error": f"ML analysis failed: {str(e)}"}

                    # Deep (historical chunk) Analysis / Backtesting
                    if include_deep:
                        print(f"🔁 Running deep backtesting analysis for {ticker} (chunk={deep_chunk_months}mo)...")
                        try:
                            deep_result = self._run_deep_analysis(
                                ticker,
                                stock_data.copy(),
                                chunk_months=deep_chunk_months
                            )
                            # Ensure JSON serializable
                            ticker_results["deep_analysis"] = self._make_json_serializable(deep_result)
                            # Attach coefficient of precision at top-level
                            if deep_result and isinstance(deep_result, dict):
                                summary = deep_result.get("summary", {})
                                if "coefficient_of_precision" in summary:
                                    ticker_results["coefficient_of_precision"] = summary["coefficient_of_precision"]
                        except Exception as e:
                            print(f"⚠️  Deep analysis failed HERE for {ticker}: {str(e)}")
                            ticker_results["deep_analysis"] = {"error": f"Deep analysis failed: {str(e)}"}

                    # Generate overall recommendation
                    try:
                        recommendation, confidence, risk_level = self._generate_overall_recommendation(ticker_results)
                        ticker_results["overall_recommendation"] = recommendation
                        ticker_results["confidence_level"] = confidence
                        ticker_results["risk_level"] = risk_level
                    except Exception as e:
                        print(f"⚠️  Recommendation generation failed for {ticker}: {str(e)}")
                        ticker_results["overall_recommendation"] = "HOLD"
                        ticker_results["confidence_level"] = "LOW"
                        ticker_results["risk_level"] = "MEDIUM"

                    # Save to database if requested
                    if save_to_db:
                        try:
                            # Ensure ticker_results is JSON serializable before saving
                            serializable_ticker_results = self._make_json_serializable(ticker_results)
                            analysis_id = self.analysis_model.save(
                                portfolio_id=portfolio_id,
                                ticker=ticker,
                                analysis_type="comprehensive",
                                analysis_data=serializable_ticker_results,
                                recommendation=ticker_results.get("overall_recommendation", "HOLD"),
                                confidence_level=ticker_results.get("confidence_level", "LOW"),
                                risk_level=ticker_results.get("risk_level", "MEDIUM")
                            )
                            ticker_results["analysis_id"] = analysis_id
                        except Exception as e:
                            print(f"⚠️  Failed to save analysis to database for {ticker}: {str(e)}")

                    # Ensure final ticker results are JSON serializable
                    results[ticker] = self._make_json_serializable(ticker_results)

                except Exception as e:
                    # If individual ticker analysis fails completely, store the error
                    print(f"❌ Complete analysis failure for {ticker}: {str(e)}")
                    results[ticker] = self._make_json_serializable({
                        "error": f"Complete analysis failure: {str(e)}",
                        "ticker": ticker,
                        "timestamp": datetime.now().isoformat()
                    })

            execution_time = time.time() - start_time

            # Make all results JSON-serializable
            try:
                serializable_results = self._make_json_serializable(results)
            except Exception as e:
                raise Exception(f"JSON serialization failed: {str(e)}")

            return {
                "success": True,
                "results": serializable_results,
                "execution_time": execution_time,
                "analyzed_tickers": len(tickers),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            execution_time = time.time() - start_time
            # Make partial results JSON-serializable if they exist
            partial_results = self._make_json_serializable(results) if results else None
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "partial_results": partial_results
            }

    def _generate_overall_recommendation(self, analysis_data: Dict[str, Any]) -> tuple:
        """Generate overall recommendation from analysis data"""
        recommendations = []
        confidence_scores = []
        risk_scores = []

        # Extract recommendations from different analyses
        if "investment_advice" in analysis_data:
            advice = analysis_data["investment_advice"]
            if isinstance(advice, dict) and "recommendation" in advice:
                recommendations.append(advice["recommendation"])
                if "confidence" in advice:
                    confidence_scores.append(advice["confidence"])

        if "options" in analysis_data:
            options = analysis_data["options"]
            if isinstance(options, dict) and "risk_level" in options:
                risk_scores.append(options["risk_level"])

        # Simple logic to combine recommendations
        if not recommendations:
            return "HOLD", "LOW", "MEDIUM"

        # Count buy/sell/hold recommendations
        buy_count = sum(1 for r in recommendations if "BUY" in str(r).upper())
        sell_count = sum(1 for r in recommendations if "SELL" in str(r).upper())
        hold_count = sum(1 for r in recommendations if "HOLD" in str(r).upper())

        if buy_count > sell_count and buy_count > hold_count:
            overall_rec = "BUY"
        elif sell_count > buy_count and sell_count > hold_count:
            overall_rec = "SELL"
        else:
            overall_rec = "HOLD"

        # Calculate confidence
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            if avg_confidence > 0.7:
                confidence = "HIGH"
            elif avg_confidence > 0.4:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"
        else:
            confidence = "MEDIUM"

        # Determine risk level
        if risk_scores:
            # This would need more sophisticated logic based on actual risk analysis
            risk_level = risk_scores[0] if risk_scores else "MEDIUM"
        else:
            risk_level = "MEDIUM"

        return overall_rec, confidence, risk_level

    def get_analysis_history(self, ticker: str = None, portfolio_id: str = None,
                           limit: int = 20) -> List[Dict[str, Any]]:
        """Get analysis history"""
        if ticker:
            return self.analysis_model.get_by_ticker(ticker, limit)
        elif portfolio_id:
            return self.analysis_model.get_by_portfolio(portfolio_id, limit)
        else:
            # Would need to implement get_all method in AnalysisResult
            return []

    def get_command_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get command execution history"""
        return self.command_model.get_recent(limit)

    def compare_predictions_vs_actual(self, ticker: str, portfolio_id: str = None,
                                    prediction_data: Dict[str, Any] = None,
                                    days_ahead: int = 30) -> Dict[str, Any]:
        """Compare predictions vs actual results"""

        command_id = self.log_command("compare_predictions", {
            "ticker": ticker,
            "portfolio_id": portfolio_id,
            "days_ahead": days_ahead
        })

        try:
            # Get recent analysis for comparison
            if prediction_data is None:
                recent_analyses = self.get_analysis_history(ticker=ticker, limit=1)
                if not recent_analyses:
                    return {
                        "success": False,
                        "error": "No recent analysis found for comparison"
                    }
                prediction_data = recent_analyses[0]["analysis_data"]

            # Download recent actual data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_ahead)

            # This would need to be implemented to get actual price data
            # For now, we'll create a placeholder
            actual_data = {
                "ticker": ticker,
                "period": f"{days_ahead}d",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "actual_price_change": 0.0,  # Would calculate from actual data
                "actual_volatility": 0.0,    # Would calculate from actual data
            }

            # Calculate comparison metrics
            comparison_metrics = self._calculate_comparison_metrics(prediction_data, actual_data)

            # Calculate accuracy score
            accuracy_score = comparison_metrics.get("overall_accuracy", 0.0)

            # Save comparison to database
            comparison_id = self.comparison_model.save_comparison(
                portfolio_id=portfolio_id,
                ticker=ticker,
                predicted_data=prediction_data,
                actual_data=actual_data,
                comparison_metrics=comparison_metrics,
                accuracy_score=accuracy_score,
                prediction_date=datetime.fromisoformat(prediction_data.get("timestamp", datetime.now().isoformat())),
                actual_date=datetime.now()
            )

            return {
                "success": True,
                "comparison_id": comparison_id,
                "accuracy_score": accuracy_score,
                "comparison_metrics": comparison_metrics,
                "predicted_data": prediction_data,
                "actual_data": actual_data
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _calculate_comparison_metrics(self, predicted: Dict[str, Any],
                                    actual: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comparison metrics between predicted and actual data"""

        metrics = {
            "price_accuracy": 0.0,
            "direction_accuracy": 0.0,
            "volatility_accuracy": 0.0,
            "overall_accuracy": 0.0,
            "comparison_date": datetime.now().isoformat()
        }

        # This would implement actual comparison logic
        # For now, return placeholder metrics
        metrics["overall_accuracy"] = 0.75  # 75% accuracy placeholder

        return metrics

    # ------------------------------------------------------------------
    # Deep Analysis / Historical Chunk Backtesting
    # ------------------------------------------------------------------
    def _run_deep_analysis(self, ticker: str, full_data: pd.DataFrame, chunk_months: int = 3) -> Dict[str, Any]:
        """
        Perform rolling historical backtest to evaluate predictive indicators accuracy.

        Process:
          1. Use the full dataset (assumed already limited to desired period, e.g. 5y).
          2. Walk forward in fixed month chunks. For each chunk end date T:
             - Use data up to T (inclusive) as if "current".
             - Derive simple predictions from available analyses logic (trend direction, next-period drift estimate).
             - Compare with actual price at T + next chunk (or dataset end) to measure accuracy.
          3. Aggregate metrics into coefficient of precision.

        Returns dict containing per-chunk records and summary statistics.
        """
        if full_data is None or full_data.empty:
            return {"error": "No data provided for deep analysis"}

        # Ensure chronological order
        data = full_data.sort_index().copy()

        # Expect a DateTimeIndex; if not, try to convert
        if not isinstance(data.index, pd.DatetimeIndex):
            # Attempt to parse an index column
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
                data = data.set_index('Date')
            else:
                try:
                    data.index = pd.to_datetime(data.index)
                except Exception:
                    return {"error": "Data does not have a valid datetime index"}

        # Basic price column selection
        price_col = 'Close' if 'Close' in data.columns else data.columns[0]

        # Determine rolling chunk boundaries
        start_date = data.index.min()
        end_date = data.index.max()
        if pd.isna(start_date) or pd.isna(end_date):
            return {"error": "Invalid date range in data"}

        chunk_results = []
        current_start = start_date

        # Helper for month increment
        def add_months(dt: pd.Timestamp, months: int) -> pd.Timestamp:
            year = dt.year + (dt.month - 1 + months) // 12
            month = (dt.month - 1 + months) % 12 + 1
            day = min(dt.day, [31,
                               29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                               31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
            return pd.Timestamp(year=year, month=month, day=day)

        # Minimal length guard (need at least two chunks)
        if add_months(start_date, chunk_months * 2) > end_date:
            return {"error": "Not enough data for deep analysis with given chunk size"}

        while True:
            chunk_end = add_months(current_start, chunk_months)
            if chunk_end >= end_date:
                break  # Need future data for evaluation

            in_sample = data.loc[(data.index >= current_start) & (data.index < chunk_end)]
            if in_sample.empty:
                current_start = chunk_end
                continue

            # Compute simple predictive indicators
            # Trend: linear regression slope on prices inside sample
            try:
                closes = in_sample[price_col]
                x = np.arange(len(closes))
                slope = 0.0
                direction = 'FLAT'
                if len(closes) > 1:
                    slope = np.polyfit(x, closes.values, 1)[0]
                    direction = 'BULLISH' if slope > 0 else 'BEARISH' if slope < 0 else 'FLAT'
                recent_return = (closes.iloc[-1] / closes.iloc[0] - 1) if len(closes) > 1 else 0.0
                # Simple projection: assume continuation of average daily return over next chunk
                avg_daily_ret = closes.pct_change().mean()
                future_period_days = max(1, int((add_months(chunk_end, chunk_months) - chunk_end).days))
                projected_change = (1 + avg_daily_ret) ** future_period_days - 1 if avg_daily_ret is not None else 0.0
            except Exception as e:
                chunk_results.append({
                    "chunk_start": current_start.isoformat(),
                    "chunk_end": chunk_end.isoformat(),
                    "error": f"Indicator calculation failed: {str(e)}"
                })
                current_start = chunk_end
                continue


            # Actual future window for evaluation
            future_start = chunk_end
            future_end = add_months(chunk_end, chunk_months)
            future_window = data.loc[(data.index >= future_start) & (data.index < future_end)]
            if future_window.empty:
                break  # No future data left

            actual_future_price = future_window[price_col].iloc[-1]
            reference_price = closes.iloc[-1]

            # Coerce pandas Series/ndarray (one-row results) to scalar values
            try:
                if isinstance(actual_future_price, (pd.Series, pd.DataFrame, np.ndarray)):
                    actual_future_price = actual_future_price.squeeze()
                actual_future_price = float(actual_future_price) if pd.notna(actual_future_price) else None
            except Exception:
                actual_future_price = None

            try:
                if isinstance(reference_price, (pd.Series, pd.DataFrame, np.ndarray)):
                    reference_price = reference_price.squeeze()
                reference_price = float(reference_price) if pd.notna(reference_price) else None
            except Exception:
                reference_price = None

            # Safely compute actual change: avoid truth-value checks on Series and handle None/zero
            if reference_price is None or reference_price == 0:
                actual_change = 0.0
            else:
                if actual_future_price is None:
                    actual_change = 0.0
                else:
                    actual_change = (actual_future_price / reference_price - 1)

            actual_direction = 'BULLISH' if actual_change > 0 else 'BEARISH' if actual_change < 0 else 'FLAT'


            # Ensure projected_change is a scalar (handle pandas Series/ndarray)
            try:
                if isinstance(projected_change, (pd.Series, pd.DataFrame, np.ndarray)):
                    projected_change = projected_change.squeeze()
                projected_change = float(projected_change) if pd.notna(projected_change) else None
            except Exception:
                projected_change = None

            # Metrics
            # If either value is missing, treat the change as zero-difference
            if projected_change is None:
                price_change_error = abs(0.0 - actual_change)
            else:
                price_change_error = abs(projected_change - actual_change)

            # Convert to accuracy (1 - normalized error). Use a soft normalization factor.
            norm_factor = max(0.0001, abs(actual_change) + 0.02)
            price_accuracy = max(0.0, 1 - price_change_error / norm_factor)
            direction_accuracy = 1.0 if direction == actual_direction else 0.0
            chunk_results.append({
                "chunk_start": current_start.isoformat(),
                "chunk_end": chunk_end.isoformat(),
                "evaluation_end": future_end.isoformat(),
                "predicted_direction": direction,
                "actual_direction": actual_direction,
                "direction_accuracy": direction_accuracy,
                "predicted_change_pct": projected_change * 100,
                "actual_change_pct": actual_change * 100,
                "price_accuracy": price_accuracy,
                "slope": slope,
                "recent_return_pct": recent_return * 100
            })

            current_start = chunk_end

        if not chunk_results:
            return {"error": "No chunk results produced"}

        # Aggregate summary
        df_chunks = pd.DataFrame(chunk_results)
        coefficient_of_precision = float(
            0.6 * df_chunks['price_accuracy'].mean() +
            0.4 * df_chunks['direction_accuracy'].mean()
        )
        summary = {
            "chunks_evaluated": int(len(df_chunks)),
            "avg_price_accuracy": float(df_chunks['price_accuracy'].mean()),
            "avg_direction_accuracy": float(df_chunks['direction_accuracy'].mean()),
            "coefficient_of_precision": coefficient_of_precision,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "chunk_months": chunk_months
        }

        return {
            "ticker": ticker,
            "summary": summary,
            "chunks": chunk_results
        }

    def get_accuracy_trends(self, ticker: str = None, portfolio_id: str = None) -> Dict[str, Any]:
        """Get accuracy trends for model refinement"""
        return self.comparison_model.get_accuracy_trends(ticker, portfolio_id)

    def portfolio_analysis(self, portfolio_id: str, period: str = "1y") -> Dict[str, Any]:
        """Analyze entire portfolio"""

        # Get portfolio tickers
        tickers_data = self.get_portfolio_tickers(portfolio_id)
        tickers = [t["ticker"] for t in tickers_data]

        if not tickers:
            return {
                "success": False,
                "error": "No tickers found in portfolio"
            }

        # Run comprehensive analysis
        return self.comprehensive_analysis(
            tickers=tickers,
            portfolio_id=portfolio_id,
            period=period
        )

    def deep_comprehensive_analysis(self, tickers: List[str], period: str = "5y",
                                    chunk_months: int = 3, **kwargs) -> Dict[str, Any]:
        """
        Convenience wrapper to run comprehensive analysis with deep backtesting enabled.

        Args:
            tickers (List[str]): Tickers to analyze
            period (str): Overall historical period (e.g. '5y')
            chunk_months (int): Size of rolling evaluation chunk
            **kwargs: Other flags forwarded to comprehensive_analysis
        """
        kwargs.setdefault('include_deep', True)
        kwargs.setdefault('deep_chunk_months', chunk_months)
        return self.comprehensive_analysis(tickers=tickers, period=period, **kwargs)
