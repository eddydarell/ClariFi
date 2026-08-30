# ClariFi - Clarify your Finances 📈

An advanced financial analysis platform that combines machine learning, pattern recognition, real-time market data, and comprehensive investment intelligence to provide professional-grade financial insights.

## 🌟 Features

### Core Analysis Engine

- **📊 Comprehensive Market Analysis**: Technical patterns, seasonal trends, event correlation, and volatility analysis
- **⚖️ Advanced Options Analysis**: Black-Scholes pricing, Greeks calculation, risk assessment, and strategy optimization
- **💼 Professional Portfolio Management**: Multi-portfolio tracking with position management and risk analysis
- **🔮 Investment Intelligence**: AI-powered BUY/SELL/HOLD recommendations with confidence levels
- **🕐 Timing Intelligence**: Holding period suggestions and recovery forecasts based on historical patterns
- **🔍 Prediction vs Reality Tracking**: Compare AI predictions with actual market performance for model refinement
- **📈 Interactive Visualizations**: Advanced charts, correlation matrices, and risk visualizations
- **🗄️ SQLite Database**: Persistent storage with complete audit trails and versioning

### Live Market Features

- **📱 Real-time Monitoring**: Live price tracking with customizable alerts
- **🔔 Smart Alerts**: Price, volume, and volatility-based notifications
- **📊 Live Dashboard**: Real-time portfolio performance and market updates
- **⚡ WebSocket Integration**: Real-time data streaming for instant updates

### Web Platform

- **🌐 FastAPI Backend**: High-performance RESTful API with comprehensive endpoints
- **💻 Modern Web UI**: Responsive React-based interface with professional design
- **📊 Interactive Dashboard**: Portfolio overview, analysis results, and performance metrics
- **🎯 Advanced Screener**: Multi-criteria stock screening with custom filters
- **📈 Professional Charts**: Interactive visualizations with zoom, annotations, and export capabilities

### Intelligence Features

- **🧠 Seasonal Pattern Analysis**: Monthly performance patterns and holiday effects
- **🎯 Event Correlation**: Major market event impact analysis and anomaly detection
- **📈 Technical Analysis**: Moving averages, RSI, MACD, Bollinger Bands, and custom indicators
- **🔥 Volatility Clustering**: Advanced volatility analysis and prediction
- **📊 Risk Assessment**: Portfolio-level risk metrics and diversification analysis
- **💡 Investment Suggestions**: Automated recommendations with detailed reasoning

## 🚀 Quick Start

### Option 1: One-Click Launch (Recommended)

```bash
# Navigate to ClariFi directory
cd /path/to/ClariFi

# Launch ClariFi (installs dependencies automatically)
python3 run_clarifi.py
```

This will:

- Check and install missing dependencies
- Create virtual environment if needed
- Start the FastAPI backend server
- Open the web interface in your browser
- Access at: <http://localhost:8000>

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the application
python3 run_clarifi.py
```

## Current Quotes

Historical OHLCV downloads continue to use yfinance. For current US stock and ETF
quotes, configure a free Twelve Data API key in `.env` or the environment:

```bash
TWELVE_DATA_API_KEY=your_key_here
CLARIFI_QUOTE_CACHE_TTL_SECONDS=300
```

Twelve Data Basic currently allows 8 API credits per minute and 800 per day, with
real-time US equities and ETFs. The default five-minute cache keeps a 10-symbol
watchlist within that daily budget during a regular US market session. The live
monitor may refresh its display every five seconds, but it reuses cached quotes.

International symbols fall back to yfinance delayed or end-of-day data and are
reported as `delayed_or_end_of_day`; they are not presented as real-time. Real-time
international coverage requires a provider plan with the applicable exchange data.

## 🏗️ Architecture

### Directory Structure

```bash
ClariFi/
├── 🚀 Application Launchers
│   ├── run_clarifi.py          # Main application launcher
│   ├── start_clarifi.sh        # Shell script launcher
│   └── run.sh                  # Legacy CLI launcher
│
├── 🧠 Core Analysis Engine
│   ├── core/
│   │   ├── engine.py           # Main ClariFi analysis engine
│   │   ├── stock_downloader.py # Market data acquisition
│   │   ├── stock_visualizer.py # Chart generation
│   │   ├── pattern_analyzer.py # Technical pattern analysis
│   │   ├── seasonal_analyzer.py# Seasonal trend analysis
│   │   ├── event_correlator.py # Market event correlation
│   │   ├── options_analyzer.py # Options pricing & Greeks
│   │   ├── advanced_visualizer.py # Advanced charts
│   │   ├── live_monitor.py     # Real-time monitoring
│   │   └── stock_screener.py   # Stock screening engine
│
├── 🌐 Web Platform
│   ├── backend/
│   │   └── server.py           # FastAPI REST API server
│   └── frontend/
│       └── ClariFi/            # React-based web interface
│           ├── src/            # Source components
│           ├── dist/           # Built application
│           └── public/         # Static assets
│
├── 🗄️ Database Layer
│   ├── database/
│   │   └── models.py           # SQLite database models
│   └── clarifi.db              # SQLite database file
│
├── 📊 Data & Output
│   ├── data/                   # Market data CSV files
│   └── graphs/                 # Generated visualizations
│
├── 📚 Documentation
│   └── docs/                   # Feature documentation
│
└── 🛠️ CLI Tools
    ├── cli_analysis.py         # Command-line analysis tool
    └── PORTFOLIO_INFO_COMPLETE.py # Portfolio management CLI
```

## 💡 Usage Examples

### 🤖 AI Analyzer (LLM + Quantitative Backtesting)

The AI Analyzer blends deterministic quantitative metrics with an optional local LLM (via **Ollama**) to produce concise BUY / SELL / HOLD recommendations with structured, consistent output.

Key quantitative inputs per ticker:

- Last price, average daily return, annualized volatility
- Maximum drawdown (risk) and 50/200 SMA relationship (momentum / regime)
- RSI(14) (overbought/oversold context)
- Lightweight SMA(20/50) crossover backtest: strategy vs buy & hold return, excess alpha, trade count, win rate
- 30‑day regression trend classification (UP / DOWN / FLAT)
- Calculated Sharpe ratio for risk-adjusted performance evaluation

**Enhanced Features (v2.0)**:

- 🔧 **Structured JSON Schema**: Consistent response format across all LLM models
- 📝 **Enhanced Prompts**: Precise instructions with decision criteria and confidence levels
- 🔍 **Response Validation**: Schema validation with fallback parsing for robust operation
- 🐛 **Debug Mode**: Raw JSON output with full prompt transparency

Recommendation generation steps:

1. Fetch historical price data (default 1y, configurable with `--period`).
2. Compute metrics + run internal SMA crossover backtest with risk-adjusted analysis.
3. Assemble a structured prompt with explicit JSON schema and decision criteria.
4. (Optional) Call local LLM model (default `qwen3:latest`) through Ollama with optimized parameters.
5. Parse and validate structured JSON response with confidence levels and rationale.

Usage:

```bash
# Multiple tickers with enhanced analysis
./run.sh ai AAPL MSFT NVDA --period 6mo

# Quant metrics only (skip LLM model)
./run.sh ai PLTR TSLA --no-llm

# Show the structured prompt sent to the model
./run.sh ai AAPL --show-prompt

# Debug mode: see raw JSON response and validation
./run.sh ai AAPL --raw-json

# Analyze a portfolio by its ID (UUID-like)
./run.sh ai 123e4567-e89b-12d3-a456-426614174000 --period 1y

# Use a different local model (must be pulled in Ollama first)
./run.sh ai AAPL MSFT --model qwen2:7b
```

Flags:

- `--period <range>`: Historical period (e.g. 6mo, 1y, 2y).
- `--no-llm`: Skip model call; still prints quantitative table & backtest metrics.
- `--show-prompt`: Display structured prompt for auditability & debugging.
- `--raw-json`: Show raw AI response, final prompt, and validation results.
- `--summary-only`: Hide rationale details and show compact output.
- `--model <name>`: Specify Ollama model tag (default `qwen3:latest`).

**Structured Output Format**:

The AI now returns consistent JSON with:

- **Per-ticker analysis**: Recommendation (BUY/SELL/HOLD), rationale (1-3 bullet points), confidence level (HIGH/MEDIUM/LOW)
- **Overall portfolio stance**: BULLISH/BEARISH/NEUTRAL with market outlook (FAVORABLE/CAUTIOUS/UNFAVORABLE)
- **Decision transparency**: Clear criteria for each recommendation type
- **Validation**: Schema compliance checking with error reporting

Output Sections:

1. **Quantitative Metrics Table** – raw computed factors & backtest results including Sharpe ratios.
2. **AI Recommendations** – structured per-ticker BUY/SELL/HOLD with confidence and rationale.
3. **Overall Portfolio Analysis** – aggregated stance and market outlook.
4. **Non‑fatal Errors** – e.g. missing model, insufficient data, validation issues.

Requirements:

- Local Ollama installed & running (`ollama run qwen3:latest` to pre-pull the model).
- Python `ollama` client installed (already in `requirements.txt`).

Graceful Degradation:

- If Ollama or the model is unavailable, the command still returns quantitative metrics and clearly reports the issue.
- Schema validation failures trigger fallback parsing to ensure recommendations are always extracted.

Disclaimer: The AI Analyzer provides heuristic + LLM synthesized suggestions and is NOT financial advice.

---

### 🎯 Strategy Analyzer (Time-Sensitive Investment Strategies)

The Strategy Analyzer generates actionable, time-sensitive investment recommendations by combining multi-dimensional analysis across trends, seasonality, backtesting, and risk metrics. Unlike simple BUY/SELL/HOLD signals, it provides specific timeframes like **"BUY now and SELL in 2 days"** or **"HOLD for 2 months"**.

**Key Analysis Dimensions**:

- **Multi-timeframe Trends**: Short-term (10/20 SMA), medium-term (20/50 SMA), long-term (50/200 SMA)
- **Technical Indicators**: RSI, MACD, ADX, Williams %R, market regime detection
- **Seasonal Patterns**: Monthly performance stats, best/worst months, holiday effects
- **Risk Metrics**: Max drawdown, Sharpe ratio, Value at Risk (VaR 95%)
- **Deep Backtesting**: Optional chunked historical validation with precision coefficients
- **Optimal Timeframe**: Analyzes 2-day, 5-day, 1-week, 2-week, 1-month, 2-month holding periods

**Strategy Scoring System** (composite -100 to +100):

- **Trend Signals (40%)**: Short/medium/long-term alignment
- **Momentum (25%)**: RSI oversold/overbought, MACD crossovers
- **Seasonal (15%)**: Historical month performance patterns
- **Backtesting (10%)**: Strategy validation across periods
- **Volatility/Risk (10%)**: High volatility penalties

**Action Thresholds**:

- **BUY**: Score ≥ 40 (strong bullish signals)
- **SELL**: Score ≤ -40 (strong bearish signals)
- **HOLD**: -40 < Score < 40 (mixed/neutral signals)

Usage:

```bash
# Default: machine-parseable JSON envelope only
./clarifi.sh strategy AAPL --period 1y

# Pretty human-readable mode
./clarifi.sh --pretty strategy AAPL --period 1y

# Graphs are opt-in (independent of --pretty)
./clarifi.sh --pretty --graph strategy AAPL --period 1y

# Basic strategy analysis
./clarifi.sh strategy AAPL --period 1y

# With deep backtesting for higher confidence
./clarifi.sh strategy TSLA --period 2y --include-deep

# Find optimal buy/sell moment
./clarifi.sh strategy MSFT --period 2y --optimum

# Complete analysis with all features
./clarifi.sh strategy NVDA --period 2y --include-deep --optimum

# Using existing data (no download)
./clarifi.sh strategy AAPL --period 6mo --no-download

# Custom deep analysis parameters
./clarifi.sh strategy GOOG --period 2y --include-deep --deep-chunk-months 6 --optimum
```

Flags:

- `--pretty`: Human-readable CLI output
- `--graph`: Enable chart/graph generation (disabled by default)
- `--period <range>`: Analysis period (default: 1y, recommended: 2y+ for seasonal data)
- `--no-download`: Use existing data without downloading fresh data
- `--include-deep`: Enable deep backtesting analysis (increases confidence)
- `--deep-chunk-months`: Chunk size for deep analysis (default: 3 months)
- `--optimum`: Find optimal buy/sell moment based on all KPIs and analysis data

Event ingestion:

```bash
# Inline JSON payload
./clarifi.sh ingest '{"date":"2026-08-24","event":"Fed commentary","category":"macro","impact":"neutral"}'

# File payload
./clarifi.sh ingest --file ./ingest/events.json
```

**Output Components**:

1. **Strategy Recommendation**:
   - Action: BUY 🟢, SELL 🔴, or HOLD 🟡
   - Timeframe: Optimal holding period (e.g., "2 days", "1 week", "2 months")
   - Target Date: Estimated action date
   - Confidence: HIGH/MEDIUM/LOW
   - Risk Level: LOW/MEDIUM/HIGH
   - Expected Return: Projected % return (if applicable)

2. **Rationale**: 3-5 key factors driving the recommendation

3. **Future Price Predictions**:
   - Short-term (5 days): Predicted price, % change, confidence, key factors
   - Mid-term (30 days): Predicted price, % change, confidence, key factors
   - Long-term (90 days): Predicted price, % change, confidence, key factors
   - Based on trend extrapolation, seasonal patterns, and momentum analysis

4. **Optimal Buy/Sell Moment** (with --optimum flag):
   - Recommended action (BUY/SELL) with optimal timing
   - Expected price and return at optimal moment
   - Confidence level and risk/reward ratio
   - Key reasoning (seasonal patterns, technical signals, historical performance)
   - Supporting analysis (signal type, win rates, trend alignment)

5. **Key Metrics**:
   - Overall score (0-100)
   - Trend directions across timeframes
   - Risk metrics (drawdown, Sharpe, VaR)
   - Market regime classification

**Example Output**:

```
📊 Ticker: AAPL
💰 Current Price: $270.37

🟡 ACTION: HOLD
⏱️  TIMEFRAME: Current
📅 TARGET DATE: 2025-11-10
🎯 CONFIDENCE: MEDIUM
⚠️  RISK LEVEL: LOW
📈 EXPECTED RETURN: +0.00%

💭 RATIONALE:
  1. HOLD signal (score: 35/100) - Mixed signals
  2. Short-term uptrend (SMA10 > SMA20)
  3. Overbought conditions (RSI: 80.5)
  4. Significant drawdown risk (-33.4%)

📊 KEY METRICS:
  Overall Score: 35/100
  Max Drawdown: -33.36%
  Sharpe Ratio: 0.83
  VaR (95%): -3.18%
  Short-term Trend: BULLISH
  Medium-term Trend: BULLISH
  Long-term Trend: BULLISH
```

**Best Practices**:

- Use periods of 2y+ for reliable seasonal analysis
- Enable `--include-deep` for higher confidence strategies
- Compare strategies across different time periods
- Always validate with fresh data for critical decisions
- Consider risk level alongside the recommendation

**See Full Documentation**: [docs/STRATEGY_COMMAND.md](docs/STRATEGY_COMMAND.md)

Disclaimer: Strategy recommendations are based on historical patterns and are NOT financial advice.

---

### Web Interface (Recommended)

1. **Launch the application**:

   ```bash
   python3 run_clarifi.py
   ```

2. **Access the web interface**: <http://localhost:8000>

3. **Create a portfolio**:
   - Navigate to "Portfolio Management"
   - Create new portfolio
   - Add tickers with position sizes

4. **Run comprehensive analysis**:
   - Select portfolio or individual stocks
   - Choose analysis options (patterns, options, seasonal, etc.)
   - View results in interactive dashboard

### Command Line Interface

#### Comprehensive Analysis

```bash
# Analyze AAPL with all features
python3 core/main.py analyze AAPL --period 1y

# Analyze multiple stocks with specific features
python3 core/main.py analyze AAPL MSFT TSLA --no-seasonal --no-events

# Portfolio analysis
python3 PORTFOLIO_INFO_COMPLETE.py analyze "My Portfolio"
```

#### Quick Analysis Commands

```bash
# Quick analysis (patterns + options + seasonal)
python3 core/main.py quick PLTR QBTS --period 6mo

# Options-focused analysis
python3 core/main.py options AAPL --strike 150 --expiry 2024-12-20

# Seasonal patterns only
python3 core/main.py seasonal MSFT --period 5y

# Machine Learning analysis
python3 core/main.py ml_analyze AAPL --period 2y --horizon 5
python3 core/main.py ml_analyze AAPL MSFT --models random_forest xgboost

# Recurrent Neural Network analysis
python3 core/main.py rnn AAPL --period 2y --horizon 5
python3 core/main.py rnn TSLA --models lstm bidirectional_gru
```

#### Real-time Monitoring

```bash
# Start live monitoring
python3 core/live_monitor.py --tickers AAPL,MSFT,TSLA

# Stock screener with custom criteria
python3 core/stock_screener.py --min-volume 1000000 --max-pe 20
```

### API Usage

```python
import requests

# Base URL for local instance
base_url = "http://localhost:8000"

# Create portfolio
portfolio_data = {
    "name": "Tech Portfolio",
    "description": "Technology stocks portfolio"
}
response = requests.post(f"{base_url}/portfolios", json=portfolio_data)
portfolio_id = response.json()["id"]

# Add ticker to portfolio
ticker_data = {
    "ticker": "AAPL",
    "quantity": 100,
    "avg_cost": 150.0
}
requests.post(f"{base_url}/portfolios/{portfolio_id}/tickers", json=ticker_data)

# Run comprehensive analysis
analysis_request = {
    "tickers": ["AAPL"],
    "period": "1y",
    "include_options": True,
    "include_seasonal": True
}
response = requests.post(f"{base_url}/analyze/comprehensive", json=analysis_request)
analysis_result = response.json()
```

## 🔧 Advanced Features

### Options Analysis

ClariFi includes a sophisticated options analysis engine:

- **Black-Scholes Pricing**: Accurate options pricing with Greeks
- **Risk Assessment**: Volatility percentiles and expected moves
- **Strategy Analysis**: Covered calls, protective puts, spreads
- **Investment Suggestions**: AI-powered recommendations with confidence levels

```python
# Example: Options analysis for AAPL
from core.options_analyzer import OptionsAnalyzer, InvestmentAdvisor

analyzer = OptionsAnalyzer()
advisor = InvestmentAdvisor()

# Get options data and analysis
options_data = analyzer.analyze_stock_options("AAPL")
investment_suggestion = advisor.generate_investment_suggestion("AAPL")

print(f"Suggestion: {investment_suggestion['suggestion']}")
print(f"Confidence: {investment_suggestion['confidence']}")
print(f"Risk Level: {investment_suggestion['risk_level']}")
```

### Seasonal Analysis

Identify recurring seasonal patterns:

```python
from core.seasonal_analyzer import SeasonalAnalyzer

seasonal = SeasonalAnalyzer()
patterns = seasonal.analyze_seasonal_patterns(["AAPL", "MSFT"], period="5y")

# View monthly performance patterns
for ticker, data in patterns.items():
    print(f"{ticker} best months: {data['best_months']}")
    print(f"{ticker} worst months: {data['worst_months']}")
```

### ML Analysis Usage

Advanced ensemble methods for price prediction:

```python
from core.ml_analyzer import MLAnalyzer

ml_analyzer = MLAnalyzer()

# Analyze stock with ML models
result = ml_analyzer.analyze(stock_data, "AAPL", prediction_horizon=5)

print(f"Recommendation: {result.recommendation.action}")
print(f"Confidence: {result.recommendation.confidence:.1%}")
print(f"Predicted Return: {result.recommendation.predicted_return:.2f}%")

# View model performance
for model_name, model_result in result.models_results.items():
    print(f"{model_name}: MSE={model_result.mse:.4f}, MAE={model_result.mae:.4f}")
```

### RNN Analysis Usage

Deep learning for time series forecasting:

```python
from core.rnn_analyzer import RNNAnalyzer

rnn_analyzer = RNNAnalyzer()

# Analyze stock with RNN models
result = rnn_analyzer.analyze(stock_data, "AAPL", prediction_horizon=5)

print(f"Recommendation: {result.recommendation.action}")
print(f"Confidence: {result.recommendation.confidence:.1%}")
print(f"Predicted Return: {result.recommendation.predicted_return:.2f}%")

# View trained models
for model_name, model_result in result.models_results.items():
    print(f"{model_name}: MSE={model_result.mse:.4f}, MAE={model_result.mae:.4f}")
```

### Real-time Monitoring Setup

Set up live market monitoring:

```python
from core.live_monitor import LiveMonitor

# Create monitor with custom alerts
monitor = LiveMonitor()
monitor.add_ticker("AAPL", price_alert_threshold=5.0)  # 5% price change alert
monitor.add_ticker("TSLA", volume_alert_multiplier=2.0)  # 2x avg volume alert

# Start monitoring
monitor.start_monitoring()
```

### Portfolio Management

Comprehensive portfolio tracking:

```python
from core.engine import ClariFiEngine

engine = ClariFiEngine()

# Create portfolio
portfolio_id = engine.create_portfolio("Tech Growth", "High-growth tech stocks")

# Add positions
engine.add_ticker_to_portfolio(portfolio_id, "AAPL", quantity=100, avg_cost=150.0)
engine.add_ticker_to_portfolio(portfolio_id, "MSFT", quantity=50, avg_cost=300.0)

# Analyze entire portfolio
analysis = engine.analyze_portfolio(portfolio_id, include_options=True)
```

## 📈 Analysis Types

### Technical Analysis

- **Moving Averages**: SMA, EMA, custom periods
- **Momentum Indicators**: RSI, MACD, Stochastic
- **Volatility**: Bollinger Bands, ATR, volatility clustering
- **Pattern Recognition**: Support/resistance, trend lines
- **Volume Analysis**: Volume trends, OBV, volume-price correlation

### Machine Learning Analysis

- **Ensemble Methods**: Random Forest, XGBoost, LightGBM for price prediction
- **Feature Engineering**: Technical indicators, volatility measures, momentum features
- **Time Series Cross-Validation**: Proper validation for financial time series
- **Recommendation Engine**: BUY/HOLD/SELL with confidence scores and risk assessment
- **Model Interpretability**: Feature importance analysis and performance metrics

### Deep Learning Analysis

- **RNN Architectures**: LSTM, GRU, Bidirectional variants for sequence prediction
- **Time Series Processing**: Sequence creation, scaling, and temporal feature extraction
- **Neural Network Training**: Early stopping, dropout, and learning rate scheduling
- **Advanced Forecasting**: Multi-step ahead predictions with uncertainty estimation
- **Model Comparison**: Automated evaluation of different RNN architectures

### Fundamental Integration

- **Company Information**: Sector, industry, market cap
- **Financial Metrics**: P/E, P/B, dividend yield
- **Event Correlation**: Earnings, splits, dividends impact
- **News Sentiment**: Major event impact analysis

### Risk Analysis

- **Portfolio Risk**: VaR, correlation analysis, diversification metrics
- **Options Risk**: Greeks, implied volatility, time decay
- **Volatility Analysis**: Historical vs implied, clustering patterns
- **Drawdown Analysis**: Maximum drawdown, recovery periods

## 🔗 Integration & Extensibility

### Data Sources

- **Yahoo Finance**: Primary market data source
- **Real-time Data**: WebSocket integration for live updates
- **Custom Data**: CSV import capabilities
- **Historical Data**: Up to maximum available history

### Export Capabilities

- **Charts**: PNG, SVG export with customizable resolution
- **Data**: CSV, JSON export for analysis results
- **Reports**: PDF generation for comprehensive analysis
- **API**: RESTful endpoints for integration

### Plugin Architecture

ClariFi is designed for extensibility:

```python
# Example: Custom analyzer plugin
class CustomAnalyzer:
    def analyze(self, data):
        # Your custom analysis logic
        return analysis_result

# Register with engine
engine.register_analyzer("custom", CustomAnalyzer())
```

## 📊 Performance & Scalability

### Optimization Features

- **Async Processing**: Non-blocking analysis execution
- **Caching**: Intelligent data caching for faster responses
- **Batch Processing**: Efficient multi-stock analysis
- **Memory Management**: Optimized for large datasets

### System Requirements

- **Python**: 3.8+ (3.10+ recommended)
- **Memory**: 4GB+ RAM (8GB+ for large portfolios)
- **Storage**: 1GB+ free space for data and charts
- **Network**: Internet connection for market data

## 🛠️ Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_options.py
python -m pytest tests/test_portfolio.py
```

### Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### API Documentation

When running the application, comprehensive API documentation is available at:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

## 🔒 Security & Privacy

- **Local Data**: All data stored locally in SQLite database
- **No Cloud Dependencies**: Runs entirely on your machine
- **API Security**: Rate limiting and input validation
- **Data Privacy**: No data sent to external servers (except market data APIs)

## 📞 Support & Troubleshooting

### Common Issues

1. **Module Import Errors**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Permission Errors**:

   ```bash
   chmod +x start_clarifi.sh
   chmod +x run.sh
   ```

3. **Port Already in Use**:

   ```bash
   # Kill existing process
   lsof -ti:8000 | xargs kill -9
   ```

4. **Market Data Issues**:
   - Check internet connection
   - Verify ticker symbols
   - Check if markets are open

### Getting Help

- Check the `docs/` directory for detailed documentation
- Review error messages in terminal output
- Verify all dependencies are installed
- Ensure Python 3.8+ is being used

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Yahoo Finance**: Market data provider
- **FastAPI**: Web framework
- **React**: Frontend framework
- **Plotly**: Interactive charting
- **Black-Scholes Model**: Options pricing foundation

---

**ClariFi** - Making financial analysis clear, comprehensive, and actionable. 📈✨
