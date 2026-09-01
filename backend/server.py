#!/usr/bin/env python3
"""
ClariFi Backend API Server
FastAPI-based REST API for ClariFi financial analysis engine
"""

import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import uvicorn
import asyncio
import json
import traceback
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, WebSocket, WebSocketDisconnect

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Add engine to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from core.engine import ClariFiEngine
from core.stock_screener import StockScreener
from core.strategy_analyzer import StrategyAnalyzer
from core.live_monitor import LiveStockMonitor
from core.forecast_engine import forecast_prices
from core.prediction_tracker import PredictionTracker
from core.recommendation_validation import (
    validate_forecast_evidence,
    validate_market_data,
    validate_trade_plan,
)
from core.result_schema import envelope, error_item, to_jsonable

# Initialize FastAPI app
app = FastAPI(
    title="ClariFi API",
    description="Advanced Market Intelligence & Pattern Analysis API",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ClariFi Engines
engine = ClariFiEngine()
screener = StockScreener()
strategy_analyzer = StrategyAnalyzer()
live_monitor = LiveStockMonitor()
prediction_tracker = PredictionTracker(engine.db_manager)


# Pydantic models for request/response
class PortfolioCreate(BaseModel):
    name: str = Field(..., description="Portfolio name")
    description: str = Field("", description="Portfolio description")

class TickerAdd(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    quantity: float = Field(0.0, description="Number of shares")
    avg_cost: float = Field(0.0, description="Average cost per share")

class AnalysisRequest(BaseModel):
    tickers: List[str] = Field(..., description="List of ticker symbols")
    portfolio_id: Optional[str] = Field(None, description="Portfolio ID")
    period: str = Field("1y", description="Analysis period")
    include_patterns: bool = Field(True, description="Include pattern analysis")
    include_events: bool = Field(True, description="Include event correlation")
    include_options: bool = Field(True, description="Include options analysis")
    include_seasonal: bool = Field(True, description="Include seasonal analysis")

class ComparisonRequest(BaseModel):
    ticker: str = Field(..., description="Ticker symbol")
    portfolio_id: Optional[str] = Field(None, description="Portfolio ID")
    days_ahead: int = Field(30, description="Days to compare")

class ScreenerRequest(BaseModel):
    category: str = Field("gainers", description="Screening category: gainers, losers, actives, new")
    limit: int = Field(20, description="Number of results")


class PredictionRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=12)
    period: str = Field("2y")
    horizons: List[int] = Field(default=[5, 20, 60], min_length=1, max_length=5)


class ComprehensiveV1Request(BaseModel):
    tickers: List[str] = Field(..., min_length=1, max_length=25)
    period: str = "1y"
    include_patterns: bool = True
    include_events: bool = True
    include_options: bool = True
    include_seasonal: bool = True
    include_ml: bool = False
    include_deep: bool = False

class StrategyRequest(BaseModel):
    ticker: str = Field(..., description="Ticker symbol")
    period: str = Field("1y", description="Analysis period")
    evidence_threshold: int = Field(
        2, ge=0, le=10,
        description="Minimum independent signals required before BUY or SELL is actionable",
    )
    minimum_walk_forward_observations: int = Field(3, ge=1, le=100)
    minimum_directional_accuracy: float = Field(0.55, ge=0.5, le=1.0)
    max_data_age_days: int = Field(7, ge=0, le=30)

class MonitorRequest(BaseModel):
    tickers: List[str] = Field(..., description="List of tickers to monitor")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Portfolio endpoints
@app.post("/api/portfolios")
async def create_portfolio(portfolio: PortfolioCreate):
    """Create a new portfolio"""
    try:
        result = engine.create_portfolio(portfolio.name, portfolio.description)
        if result["success"]:
            return {"success": True, "portfolio_id": result["portfolio_id"], "message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolios")
async def get_portfolios():
    """Get all portfolios"""
    try:
        portfolios = engine.get_portfolios()
        return {"success": True, "portfolios": portfolios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolios/{portfolio_id}")
async def get_portfolio(portfolio_id: str):
    """Get specific portfolio"""
    try:
        portfolio = engine.portfolio_model.get_by_id(portfolio_id)
        if portfolio:
            tickers = engine.get_portfolio_tickers(portfolio_id)
            portfolio["tickers"] = tickers
            return {"success": True, "portfolio": portfolio}
        else:
            raise HTTPException(status_code=404, detail="Portfolio not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolios/{portfolio_id}/tickers")
async def add_ticker_to_portfolio(portfolio_id: str, ticker_data: TickerAdd):
    """Add ticker to portfolio"""
    try:
        result = engine.add_ticker_to_portfolio(
            portfolio_id,
            ticker_data.ticker,
            ticker_data.quantity,
            ticker_data.avg_cost
        )
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/portfolios/{portfolio_id}/tickers/{ticker}")
async def remove_ticker_from_portfolio(portfolio_id: str, ticker: str):
    """Remove ticker from portfolio"""
    try:
        result = engine.remove_ticker_from_portfolio(portfolio_id, ticker)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolios/{portfolio_id}/tickers")
async def get_portfolio_tickers(portfolio_id: str):
    """Get all tickers in portfolio"""
    try:
        tickers = engine.get_portfolio_tickers(portfolio_id)
        return {"success": True, "tickers": tickers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolios/{portfolio_id}/info")
async def get_portfolio_info(portfolio_id: str):
    """Get comprehensive portfolio information including current prices, analysis, and metrics"""
    try:
        result = engine.get_portfolio_info(portfolio_id)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolios/{portfolio_id}/analytics")
async def get_portfolio_analytics(portfolio_id: str):
    """Get advanced portfolio analytics including risk distribution and performance trends"""
    try:
        result = engine.get_portfolio_analytics(portfolio_id)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/comprehensive")
async def run_comprehensive_analysis(analysis_request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Run comprehensive analysis on tickers"""
    try:
        # For long-running analysis, you might want to run it in background
        # and return a task ID, then provide a status endpoint
        result = engine.comprehensive_analysis(
            tickers=analysis_request.tickers,
            portfolio_id=analysis_request.portfolio_id,
            period=analysis_request.period,
            include_patterns=analysis_request.include_patterns,
            include_events=analysis_request.include_events,
            include_options=analysis_request.include_options,
            include_seasonal=analysis_request.include_seasonal,
            save_to_db=False  # Disable database save to avoid pandas serialization issues
        )
        print(f"Analysis result: {result}")

        # Ensure the result is JSON serializable before returning
        # The engine should already handle this, but double-check
        serializable_result = engine._make_json_serializable(result)
        return serializable_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/portfolio/{portfolio_id}")
async def analyze_portfolio(portfolio_id: str, period: str = "1y"):
    """Analyze entire portfolio"""
    try:
        result = engine.portfolio_analysis(portfolio_id, period)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/history")
async def get_analysis_history(ticker: Optional[str] = None, portfolio_id: Optional[str] = None, limit: int = 20):
    """Get analysis history"""
    try:
        history = engine.get_analysis_history(ticker, portfolio_id, limit)
        return {"success": True, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/compare")
async def compare_predictions(comparison_request: ComparisonRequest):
    """Compare predictions vs actual results"""
    try:
        result = engine.compare_predictions_vs_actual(
            ticker=comparison_request.ticker,
            portfolio_id=comparison_request.portfolio_id,
            days_ahead=comparison_request.days_ahead
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/accuracy-trends")
async def get_accuracy_trends(ticker: Optional[str] = None, portfolio_id: Optional[str] = None):
    """Get accuracy trends for model refinement"""
    try:
        trends = engine.get_accuracy_trends(ticker, portfolio_id)
        return {"success": True, "trends": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Command history endpoint
@app.get("/api/commands/history")
async def get_command_history(limit: int = 50):
    """Get command execution execution history"""
    try:
        history = engine.get_command_history(limit)
        return {"success": True, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Screener Endpoints
@app.post("/api/screener")
async def screen_market(request: ScreenerRequest):
    """Screen the market for stocks"""
    try:
        results = screener.screen_market(request.category, request.limit, json_output=True)
        return {"success": True, "data": engine._make_json_serializable(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Strategy Endpoints
@app.post("/api/strategy")
async def generate_strategy(request: StrategyRequest):
    """Generate investment strategy for a ticker"""
    try:
        stock_data = engine.downloader.download_stock_data(request.ticker, period=request.period)
        
        if stock_data is None or stock_data.empty:
             raise HTTPException(status_code=404, detail=f"No data found for {request.ticker}")

        data_quality = validate_market_data(stock_data, request.max_data_age_days)
        if not data_quality['valid']:
            strategy = strategy_analyzer.create_suppressed_strategy(
                request.ticker, data_quality['reasons'], data_quality.get('data_as_of')
            )
            return {
                "success": True,
                "strategy": engine._make_json_serializable(strategy),
                "data_quality": data_quality,
                "prediction_tracking": None,
                "decision_support_only": True,
            }

        # Compute technical indicators
        try:
            stock_data = stock_data.copy()
            engine.pattern_analyzer.add_technical_indicators(stock_data, validate=False)
            last_row = stock_data.iloc[-1]
            technical_indicators = {
                'RSI_14': float(last_row['RSI_14']) if 'RSI_14' in last_row and not pd.isna(last_row['RSI_14']) else None,
                'MACD': float(last_row['MACD']) if 'MACD' in last_row and not pd.isna(last_row['MACD']) else None,
                'MACD_Signal': float(last_row['MACD_Signal']) if 'MACD_Signal' in last_row and not pd.isna(last_row['MACD_Signal']) else None,
                'ADX': float(last_row['ADX']) if 'ADX' in last_row and not pd.isna(last_row['ADX']) else None,
                'Williams_%R': float(last_row['Williams_%R']) if 'Williams_%R' in last_row and not pd.isna(last_row['Williams_%R']) else None,
                'CCI': float(last_row['CCI']) if 'CCI' in last_row and not pd.isna(last_row['CCI']) else None,
                'BB_Upper': float(last_row['BB_Upper']) if 'BB_Upper' in last_row and not pd.isna(last_row['BB_Upper']) else None,
                'BB_Lower': float(last_row['BB_Lower']) if 'BB_Lower' in last_row and not pd.isna(last_row['BB_Lower']) else None,
                'BB_Middle': float(last_row['BB_Middle']) if 'BB_Middle' in last_row and not pd.isna(last_row['BB_Middle']) else None,
                'BB_Width': float(last_row['BB_Width']) if 'BB_Width' in last_row and not pd.isna(last_row['BB_Width']) else None,
                '_last_close': float(last_row['Close']),
            }
        except Exception as e:
            print(f"Warning: Failed to compute technical indicators: {e}")
            technical_indicators = None

        # Seasonal analysis
        try:
            seasonal = engine.seasonal_analyzer.analyze(stock_data)
        except Exception as e:
            print(f"Warning: Seasonal analysis failed: {e}")
            seasonal = None

        strategy = strategy_analyzer.generate_strategy(
            ticker=request.ticker,
            data=stock_data,
            period=request.period,
            seasonal_analysis=seasonal,
            deep_analysis=None,
            technical_indicators=technical_indicators,
            find_optimum=True,
            evidence_threshold=request.evidence_threshold,
        )
        forecast = forecast_prices(stock_data, request.ticker, (5, 20, 60))
        strategy.empirical_validation = validate_forecast_evidence(
            strategy,
            forecast,
            minimum_observations=request.minimum_walk_forward_observations,
            minimum_directional_accuracy=request.minimum_directional_accuracy,
        )
        strategy.trade_plan_validation = validate_trade_plan(strategy)
        provenance = {
            'decision_status': strategy.decision_status,
            'evidence_tags': strategy.evidence_tags,
            'data_quality': data_quality,
            'empirical_validation': strategy.empirical_validation,
            'trade_plan_validation': strategy.trade_plan_validation,
            'policy_version': 'swing-v1',
        }
        
        import dataclasses
        strategy_dict = dataclasses.asdict(strategy)

        try:
            prediction_tracking = prediction_tracker.process_run(
                ticker=request.ticker, entry_price=strategy.entry_price, predictions=strategy.predictions,
                provenance=provenance,
            )
        except Exception as e:
            print(f"Warning: prediction tracking failed: {e}")
            prediction_tracking = None

        return {
            "success": True,
            "strategy": engine._make_json_serializable(strategy_dict),
            "prediction_tracking": engine._make_json_serializable(prediction_tracking) if prediction_tracking else None,
            "decision_support_only": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Strategy endpoint error:\n{tb}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@app.post("/api/v1/predictions")
async def generate_predictions_v1(request: PredictionRequest):
    """Return validated baseline forecasts using the canonical result envelope."""
    ticker = request.ticker.strip().upper()
    try:
        if any(h < 1 or h > 252 for h in request.horizons):
            raise ValueError("horizons must be between 1 and 252 trading days")
        stock_data = engine.downloader.download_stock_data(ticker, period=request.period)
        if stock_data is None or stock_data.empty:
            return envelope("prediction.forecast", errors=[error_item(
                f"No market data found for {ticker}", "NO_DATA", "forecast", ticker
            )], meta={"ticker": ticker})
        result = forecast_prices(stock_data, ticker, tuple(request.horizons))
        return envelope("prediction.forecast", result, meta={
            "ticker": ticker,
            "period": request.period,
            "horizons": request.horizons,
            "data_as_of": result["as_of"],
        })
    except ValueError as exc:
        return envelope("prediction.forecast", errors=[error_item(str(exc), "INVALID_INPUT", "forecast", ticker)])
    except Exception as exc:
        traceback.print_exc()
        return envelope("prediction.forecast", errors=[error_item(
            str(exc), "PREDICTION_FAILED", "forecast", ticker, retryable=True
        )])


@app.post("/api/v1/strategy")
async def generate_strategy_v1(request: StrategyRequest):
    """Canonical wrapper around the existing explainable strategy analysis."""
    try:
        stock_data = engine.downloader.download_stock_data(request.ticker.strip().upper(), period=request.period)
        if stock_data is None or stock_data.empty:
            return envelope("strategy.generate", errors=[error_item(
                "No market data found", "NO_DATA", "strategy", request.ticker
            )])
        data_quality = validate_market_data(stock_data, request.max_data_age_days)
        if not data_quality['valid']:
            strategy = strategy_analyzer.create_suppressed_strategy(
                request.ticker.strip().upper(), data_quality['reasons'], data_quality.get('data_as_of')
            )
            return envelope("strategy.generate", {"strategy": strategy, "prediction_tracking": None}, meta={
                "ticker": request.ticker.upper(),
                "decision_support_only": True,
                "data_quality": data_quality,
            })
        technical_indicators = {"_last_close": float(stock_data["Close"].iloc[-1])}
        seasonal = engine.seasonal_analyzer.analyze(stock_data)
        strategy = strategy_analyzer.generate_strategy(
            ticker=request.ticker.strip().upper(), data=stock_data, period=request.period,
            seasonal_analysis=seasonal, technical_indicators=technical_indicators,
            find_optimum=True,
            evidence_threshold=request.evidence_threshold,
        )
        forecast = forecast_prices(stock_data, request.ticker.strip().upper(), (5, 20, 60))
        strategy.empirical_validation = validate_forecast_evidence(
            strategy,
            forecast,
            minimum_observations=request.minimum_walk_forward_observations,
            minimum_directional_accuracy=request.minimum_directional_accuracy,
        )
        strategy.trade_plan_validation = validate_trade_plan(strategy)
        provenance = {
            'decision_status': strategy.decision_status,
            'evidence_tags': strategy.evidence_tags,
            'data_quality': data_quality,
            'empirical_validation': strategy.empirical_validation,
            'trade_plan_validation': strategy.trade_plan_validation,
            'policy_version': 'swing-v1',
        }
        try:
            prediction_tracking = prediction_tracker.process_run(
                ticker=request.ticker.strip().upper(), entry_price=strategy.entry_price,
                predictions=strategy.predictions, provenance=provenance,
            )
        except Exception as e:
            print(f"Warning: prediction tracking failed: {e}")
            prediction_tracking = None
        return envelope("strategy.generate", {"strategy": strategy, "prediction_tracking": prediction_tracking},
                       meta={
                           "ticker": request.ticker.upper(),
                           "decision_support_only": True,
                           "evidence_threshold": request.evidence_threshold,
                       })
    except Exception as exc:
        traceback.print_exc()
        return envelope("strategy.generate", errors=[error_item(
            str(exc), "STRATEGY_FAILED", "strategy", request.ticker
        )])


@app.post("/api/v1/screener")
async def screen_market_v1(request: ScreenerRequest):
    """Canonical market-screening response for frontend and API clients."""
    category = request.category if request.category != "active" else "actives"
    try:
        result = screener.screen_market(category, request.limit, json_output=True)
        return envelope("market.screen", result, meta={"category": category, "limit": request.limit})
    except Exception as exc:
        return envelope("market.screen", errors=[error_item(str(exc), "SCREEN_FAILED", "screener")])


@app.post("/api/v1/analysis/comprehensive")
async def comprehensive_analysis_v1(request: ComprehensiveV1Request):
    """Expose all existing checks through one versioned, JSON-safe contract."""
    tickers = [ticker.strip().upper() for ticker in request.tickers if ticker.strip()]
    if not tickers:
        return envelope("analysis.comprehensive", errors=[error_item(
            "At least one ticker is required", "INVALID_INPUT", "analysis"
        )])
    try:
        result = engine.comprehensive_analysis(
            tickers=tickers,
            period=request.period,
            save_to_db=False,
            include_patterns=request.include_patterns,
            include_events=request.include_events,
            include_options=request.include_options,
            include_seasonal=request.include_seasonal,
            include_ml=request.include_ml,
            include_deep=request.include_deep,
        )
        return envelope("analysis.comprehensive", result, meta={"tickers": tickers, "period": request.period})
    except Exception as exc:
        traceback.print_exc()
        return envelope("analysis.comprehensive", errors=[error_item(
            str(exc), "ANALYSIS_FAILED", "analysis", retryable=True
        )])

# Live Monitor Endpoints
monitoring_active = False

@app.post("/api/live-monitor/start")
async def start_monitoring(request: MonitorRequest, background_tasks: BackgroundTasks):
    """Start live monitoring"""
    global monitoring_active
    
    if monitoring_active:
        # Update tickers if already running
        live_monitor.add_tickers(request.tickers)
        return {"success": True, "message": "Updated monitored tickers"}
    
    live_monitor.add_tickers(request.tickers)
    monitoring_active = True
    
    # We don't start a blocking loop here. 
    # Instead, the WebSocket endpoint or a background task will handle updates.
    # For this architecture, we'll use the WebSocket to drive updates when clients are connected.
    
    return {"success": True, "message": "Monitoring configured"}

@app.post("/api/live-monitor/stop")
async def stop_monitoring():
    """Stop live monitoring"""
    global monitoring_active
    monitoring_active = False
    return {"success": True, "message": "Monitoring stopped"}


# Static file serving for the active lowercase frontend.
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "clarifi", "dist")


# Serve static assets (Vite build)
@app.get("/favicon.ico")
async def get_favicon():
    favicon_path = os.path.join(frontend_dir, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/x-icon")
    return Response(status_code=204)

# Mount Vite assets and compatibility static path
try:
    # Vite build places hashed assets under /assets
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "assets")), name="assets")
    # Also provide /static for older clients
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "assets")), name="static")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")


# Serve the frontend app (index.html) for all non-API routes
@app.get("/")
async def serve_frontend():
    frontend_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    else:
        return {"message": "ClariFi API is running", "docs": "/docs", "frontend": "Not built yet"}


@app.get("/{path:path}")
async def spa_fallback(path: str):
    """Serve Vue history routes while leaving API/static routes to their handlers."""
    if path.startswith(("api/", "assets/", "static/", "ws")):
        raise HTTPException(status_code=404, detail="Not found")
    frontend_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    raise HTTPException(status_code=404, detail="Frontend not built")


@app.get("/vite.svg")
async def get_vite_svg():
    vite_path = os.path.join(frontend_dir, "vite.svg")
    if os.path.exists(vite_path):
        return FileResponse(vite_path, media_type="image/svg+xml")
    return Response(status_code=204)

# WebSocket endpoint for real-time updates (optional)
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Wait for messages from client (e.g., heartbeat or commands)
            # We use a timeout so we can send updates even if no message received
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                # Handle client messages if needed
                if data == "ping":
                    await manager.send_personal_message("pong", websocket)
            except asyncio.TimeoutError:
                # No message from client, check if we need to send updates
                pass
            
            # If monitoring is active, fetch and send updates
            if monitoring_active and live_monitor.tickers:
                try:
                    updates = live_monitor.fetch_updates()
                    if updates:
                        await manager.broadcast(json.dumps({"type": "price_update", "data": updates}))
                except Exception as e:
                    print(f"Error fetching updates: {e}")
                
                # Wait a bit to avoid flooding
                await asyncio.sleep(2)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)



def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    """Run the FastAPI server"""
    uvicorn.run("server:app", host=host, port=port, reload=reload)

if __name__ == "__main__":
    import sys
    port = 8000
    host = "0.0.0.0"
    # Allow: python server.py --port 8181
    if len(sys.argv) > 2 and sys.argv[1] == "--port":
        try:
            port = int(sys.argv[2])
        except Exception:
            pass
    run_server(host=host, port=port)
