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
from typing import List, Dict, Any, Optional

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

    def _make_json_serializable(self, obj):
        """Convert pandas objects and numpy types to JSON-serializable Python types."""
        if obj is None:
            return None
        elif isinstance(obj, pd.Series):
            # Convert Series to dict with string keys to avoid serialization issues
            try:
                return obj.to_dict()
            except:
                # Fallback to list if to_dict() fails
                return obj.tolist()
        elif isinstance(obj, pd.DataFrame):
            try:
                return obj.to_dict(orient='records')
            except:
                # Fallback to dict conversion
                return obj.to_dict()
        elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
            return str(obj)
        elif isinstance(obj, (datetime, timedelta)):
            return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, dict):
            return {str(key): self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            # Handle custom class objects by converting their attributes to dict
            try:
                return {attr: self._make_json_serializable(getattr(obj, attr))
                        for attr in dir(obj) if not attr.startswith('_') and not callable(getattr(obj, attr))}
            except:
                return str(obj)
        else:
            # Try to convert to string if all else fails
            try:
                return obj
            except:
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

    # Analysis Methods
    def comprehensive_analysis(self, tickers: List[str], portfolio_id: str = None,
                             period: str = "1y", save_to_db: bool = True,
                             include_patterns: bool = True, include_events: bool = True,
                             include_options: bool = True, include_seasonal: bool = True) -> Dict[str, Any]:
        """Perform comprehensive analysis on tickers"""

        command_id = self.log_command("comprehensive_analysis", {
            "tickers": tickers,
            "portfolio_id": portfolio_id,
            "period": period,
            "include_patterns": include_patterns,
            "include_events": include_events,
            "include_options": include_options,
            "include_seasonal": include_seasonal
        })

        start_time = time.time()
        results = {}

        try:
            for ticker in tickers:
                print(f"\n🔍 Analyzing {ticker}...")
                ticker_results = {}

                # Download data
                print(f"📥 Downloading data for {ticker}...")
                stock_data = self.downloader.download_stock_data(ticker, None, None, period=period)

                if stock_data is None:
                    ticker_results["error"] = f"Failed to download data for {ticker}"
                    results[ticker] = ticker_results
                    continue

                # Save the downloaded data for analysis
                saved_file = self.downloader.save_to_csv(stock_data, ticker)
                if not saved_file:
                    ticker_results["error"] = f"Failed to save data for {ticker}"
                    results[ticker] = ticker_results
                    continue

                # Pattern Analysis
                if include_patterns:
                    print(f"📊 Running pattern analysis for {ticker}...")
                    try:
                        stock_data_dict = {ticker: stock_data}
                        pattern_data = self.pattern_analyzer.analyze_correlation_patterns(stock_data_dict)
                        ticker_results["patterns"] = pattern_data
                    except Exception as e:
                        ticker_results["patterns"] = {"error": f"Pattern analysis failed: {str(e)}"}

                # Event Correlation
                if include_events:
                    print(f"📰 Running event correlation analysis for {ticker}...")
                    try:
                        stock_data_dict = {ticker: stock_data}
                        event_data = self.event_correlator.correlate_events_with_movements(stock_data_dict)

                        # Make event data JSON serializable if needed
                        try:
                            import json
                            json.dumps(event_data, default=str)
                        except Exception:
                            event_data = self._make_json_serializable(event_data)

                        ticker_results["events"] = event_data

                    except Exception as e:
                        ticker_results["events"] = {"error": f"Event analysis failed: {str(e)}"}

                # Options Analysis
                if include_options:
                    print(f"⚖️ Running options analysis for {ticker}...")
                    try:
                        options_data = self.options_analyzer.analyze_options(ticker, stock_data)
                        ticker_results["options"] = options_data
                    except Exception as e:
                        ticker_results["options"] = {"error": f"Options analysis failed: {str(e)}"}

                    try:
                        investment_advice = self.investment_advisor.generate_investment_suggestion(stock_data)
                        ticker_results["investment_advice"] = investment_advice
                    except Exception as e:
                        ticker_results["investment_advice"] = {"error": f"Investment advice failed: {str(e)}"}

                # Seasonal Analysis
                if include_seasonal:
                    print(f"🗓️ Running seasonal analysis for {ticker}...")
                    try:
                        seasonal_data = self.seasonal_analyzer.analyze(stock_data)
                        ticker_results["seasonal"] = seasonal_data
                    except Exception as e:
                        ticker_results["seasonal"] = {"error": f"Seasonal analysis failed: {str(e)}"}

                # Generate overall recommendation
                recommendation, confidence, risk_level = self._generate_overall_recommendation(ticker_results)
                ticker_results["overall_recommendation"] = recommendation
                ticker_results["confidence_level"] = confidence
                ticker_results["risk_level"] = risk_level

                # Save to database if requested
                if save_to_db:
                    analysis_id = self.analysis_model.save(
                        portfolio_id=portfolio_id,
                        ticker=ticker,
                        analysis_type="comprehensive",
                        analysis_data=ticker_results,
                        recommendation=recommendation,
                        confidence_level=confidence,
                        risk_level=risk_level
                    )
                    ticker_results["analysis_id"] = analysis_id

                results[ticker] = ticker_results

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
