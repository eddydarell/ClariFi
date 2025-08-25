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
from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Add engine to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from clarifi_engine.engine import ClariFiEngine

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

# Initialize ClariFi Engine
engine = ClariFiEngine()

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
    """Get command execution history"""
    try:
        history = engine.get_command_history(limit)
        return {"success": True, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Static file serving for frontend (now from frontend/ClariFi/dist)
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "ClariFi", "dist")


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
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message received: {data}", websocket)
    except WebSocketDisconnect:
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
