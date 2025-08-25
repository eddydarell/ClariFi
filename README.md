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
