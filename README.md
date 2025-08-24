# 🚀 ClariFi: Clarify your Finances

## Advanced Market Intelligence & Pattern Analysis Tool

A sophisticated financial analysis system that provides deep insights into stock patterns, correlations, event impacts, seasonal trends, options pricing, and investment recommendations to help clarify your financial decisions and make informed investments.

## 💡 About ClariFi

ClariFi combines "Clarity" and "Finances" to deliver exactly what modern investors need: **clear, actionable insights** from complex financial data. Our tool transforms raw market data into understandable patterns and recommendations.

## 🎯 Core Features

### 📊 **Pattern Analysis**

- **Correlation Detection**: Identify stocks that move together or in opposition
- **Leading Indicators**: Find stocks that predict movements in others
- **Volatility Clustering**: Detect periods of high/low volatility grouping
- **Support/Resistance**: Automatically identify key price levels
- **Trend Strength**: Analyze momentum and trend reliability

### 📰 **Event Correlation**

- **Major Event Impact**: Correlate market movements with world events
- **Unusual Movement Detection**: Identify unexplained large price swings
- **Event Timeline**: Track how events affect different stocks over time
- **Custom Events**: Add your own events for analysis

### ⚖️ **Options & Risk Analysis** (NEW)

- **Black-Scholes Pricing**: Full implementation of the Black-Scholes equation for options pricing
- **Greeks Calculation**: Delta, Gamma, Theta, Vega, and Rho for risk assessment
- **Implied Volatility**: Calculate IV from market prices using Newton-Raphson method
- **Risk Assessment**: Comprehensive volatility analysis and risk level determination
- **Expected Moves**: Predict price movement ranges for different timeframes

### 🗓️ **Seasonal Analysis** (NEW)

- **Monthly Pattern Detection**: Identify best and worst performing months for each stock
- **Holiday Effects**: Track performance around major holidays (New Year, Christmas, Thanksgiving, etc.)
- **Seasonal Bias Scoring**: Quantify how seasonal a stock's behavior is
- **Current Timing Analysis**: Get recommendations for optimal entry/exit times
- **Business Cycle Integration**: Perfect for sector-specific seasonal trends (retail, energy, agriculture)

### 💰 **Investment Advisory** (NEW)

- **BUY/SELL/HOLD Recommendations**: Clear, actionable investment suggestions
- **Confidence Levels**: HIGH/MEDIUM/LOW confidence ratings for each recommendation
- **Portfolio Analysis**: Portfolio-level risk assessment and diversification analysis
- **Signal Integration**: Combines technical, fundamental, and options analysis
- **Risk-Adjusted Advice**: Recommendations account for individual risk tolerance

### �🔬 **Advanced Analytics**

- **Rolling Correlations**: See how relationships change over time
- **Cross-Asset Analysis**: Compare stocks, indices, sectors
- **Multi-timeframe Analysis**: From daily to yearly patterns
- **Statistical Significance**: All results include confidence metrics
- **Options Market Intelligence**: Real-time risk metrics and market sentiment

### 🎨 **Professional Visualizations**

- **Interactive Charts**: Multiple chart types with rich annotations
- **Correlation Heatmaps**: Visual correlation matrices with stability metrics
- **Event Impact Plots**: Timeline of how events affected prices
- **Volatility Clustering**: Visual representation of volatility patterns
- **Risk Visualization**: Options risk profiles and expected move charts

## Directory Structure

```
ClariFi/
├── main.py                 # Main orchestration script
├── stock_downloader.py     # Stock data downloading functionality
├── stock_visualizer.py     # Chart and graph generation
├── seasonal_analyzer.py    # Seasonal pattern analysis
├── pattern_analyzer.py     # Pattern detection and correlation analysis
├── event_correlator.py     # Event correlation analysis
├── advanced_visualizer.py  # Advanced charts and visualizations
├── options_analyzer.py     # Black-Scholes options analysis
├── requirements.txt        # Python dependencies
├── data/                   # CSV data files storage
├── graphs/                 # Generated charts and visualizations
└── README.md              # This file
```

## Installation & Setup

### Quick Start

1. **Initialize Environment** (One-time setup):
   ```bash
   ./run.sh init
   ```
   This will:
   - Create a virtual environment at `/Users/eddyntambwe/Dev/scripts-project/venv`
   - Install all required Python packages
   - Set up the environment for immediate use

2. **Verify Installation**:
   ```bash
   ./run.sh --help
   ```

### Manual Installation (Alternative)

If you prefer manual setup:

1. **Create Virtual Environment**:
   ```bash
   python3 -m venv /Users/eddyntambwe/Dev/scripts-project/venv
   source /Users/eddyntambwe/Dev/scripts-project/venv/bin/activate
   ```

2. **Install Required Packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Installation**:
   ```bash
   python main.py --help
   ```

### Dependencies

The tool requires these Python packages:
- `yfinance>=0.2.18` - Yahoo Finance data
- `matplotlib>=3.7.0` - Charting and visualization
- `seaborn>=0.12.0` - Statistical visualization
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical computing
- `scipy>=1.10.0` - Scientific computing
- `requests>=2.28.0` - HTTP requests

## Usage

### Comprehensive Analysis with Seasonal, Options & Investment Advice (NEW)

Perform full market analysis including seasonal patterns, Black-Scholes options pricing and investment recommendations:

```bash
# Complete analysis with all features (including seasonal)
./run.sh analyze AAPL MSFT TSLA --period 1y

# Skip specific analysis components
./run.sh analyze PLTR --no-options          # Skip options analysis
./run.sh analyze QBTS --no-investment-advice # Skip investment suggestions
./run.sh analyze AAPL --no-events           # Skip event correlation
./run.sh analyze MSFT --no-seasonal         # Skip seasonal analysis

# Focus only on seasonal analysis
./run.sh seasonal AAPL MSFT --period 5y     # 5y recommended for better patterns

# Focus only on options and risk analysis
./run.sh analyze MSFT --no-patterns --no-events --no-advanced-viz --no-seasonal
```

#### Key Features of Comprehensive Analysis

- **Seasonal Pattern Analysis**: Monthly performance patterns and holiday effects
- **Pattern Analysis**: Correlation detection, trend analysis, volatility clustering
- **Event Correlation**: Major event impact analysis and unusual movement detection
- **Black-Scholes Options Pricing**: Full options analysis with Greeks calculation
- **Risk Assessment**: Volatility percentiles, expected moves, risk level determination
- **Investment Suggestions**: BUY/SELL/HOLD recommendations with confidence levels
- **Portfolio Analysis**: Portfolio-level risk assessment and diversification analysis

### Demo the New Options Features

Run the options analyzer demo to see the Black-Scholes implementation in action:

```bash
# Run the interactive demo
python demo_options.py
```

This demo showcases:

- Black-Scholes call and put option pricing
- Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
- Risk analysis for different volatility stocks
- Investment suggestion engine with portfolio recommendations

### Quick Analysis (Recommended)

Perform complete analysis with one command:

```bash
# Analyze PLTR and QBTS for the last year
python main.py quick PLTR QBTS

# Analyze for different time periods
python main.py quick AAPL MSFT GOOGL --period 6mo
python main.py quick TSLA --period 2y
```

### Individual Commands

#### 1. Download Stock Data

```bash
# Download with period specification
python main.py download PLTR QBTS --period 1y

# Download with specific date range
python main.py download AAPL --start 2023-01-01 --end 2024-01-01

# Multiple stocks with different periods
python main.py download MSFT GOOGL AMZN --period 6mo
```

#### 2. Create Visualizations

```bash
# Individual stock charts
python main.py visualize PLTR --single

# Comparison charts
python main.py visualize PLTR QBTS --compare

# Correlation matrix
python main.py visualize AAPL MSFT GOOGL --correlation

# All visualizations for multiple stocks
python main.py visualize PLTR QBTS --single --compare --correlation
```

#### 3. Stock Information

```bash
# Get company information
python main.py info PLTR QBTS
```

#### 4. List Available Data

```bash
# Show all downloaded data files
python main.py list
```

## Available Time Periods

- `1d` - 1 day
- `5d` - 5 days
- `1mo` - 1 month
- `3mo` - 3 months
- `6mo` - 6 months
- `1y` - 1 year (default)
- `2y` - 2 years
- `5y` - 5 years
- `10y` - 10 years
- `ytd` - Year to date
- `max` - Maximum available data

## Chart Types

### Individual Stock Analysis

Each stock gets a comprehensive 4-panel chart:

1. **Price Chart**: Open and Close prices over time
2. **Volume Chart**: Trading volume
3. **High/Low Range**: Price range with closing prices
4. **Daily Returns**: Percentage daily returns

### Comparison Analysis

Multi-stock comparison includes:

1. **Normalized Price Comparison**: All stocks normalized to 100 for relative performance
2. **Absolute Price Comparison**: Raw price movements
3. **Volume Comparison**: Trading volume comparison
4. **Daily Returns Comparison**: Return volatility comparison

### Correlation Matrix

- Heatmap showing price correlations between stocks
- Values from -1 (negative correlation) to +1 (positive correlation)
- Useful for portfolio diversification analysis

## Examples

### Example 1: Tech Stock Analysis

```bash
# Download and analyze major tech stocks
python main.py quick AAPL MSFT GOOGL AMZN --period 1y
```

### Example 2: Growth Stock Comparison

```bash
# Compare growth stocks
python main.py quick PLTR QBTS SNOW CRWD --period 6mo
```

### Example 3: Sector Analysis

```bash
# Download financial sector stocks
python main.py download JPM BAC WFC C --period 2y

# Create comparison visualization
python main.py visualize JPM BAC WFC C --compare --correlation
```

### Example 4: Custom Date Range

```bash
# Analyze specific period
python main.py download TSLA --start 2023-01-01 --end 2023-12-31
python main.py visualize TSLA --single
```

## File Organization

### Data Files

- Saved in `data/` directory
- Format: `{TICKER}_{START_DATE}_{END_DATE}.csv`
- Example: `PLTR_2023-08-23_2024-08-23.csv`

### Chart Files

- Saved in `graphs/` directory
- Individual charts: `{TICKER}_analysis_{DATE}.png`
- Comparisons: `comparison_{TICKER1}_{TICKER2}_..._{DATE}.png`
- Correlations: `correlation_{TICKER1}_{TICKER2}_..._{DATE}.png`

## Tips

1. **Stock Tickers**: Use standard Yahoo Finance ticker symbols
2. **Data Validation**: The tool validates ticker symbols and shows company information
3. **Batch Processing**: Download multiple stocks at once for efficiency
4. **Period vs Dates**: Use `--period` for convenience or `--start`/`--end` for precision
5. **Visualization**: Charts are saved as high-resolution PNG files suitable for presentations

## Common Stock Tickers

- **Tech**: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA
- **Growth**: PLTR, SNOW, CRWD, ZM, ROKU
- **Quantum**: QBTS (D-Wave), IBM, GOOGL
- **Finance**: JPM, BAC, WFC, GS
- **Indices**: ^GSPC (S&P 500), ^IXIC (NASDAQ), ^DJI (Dow Jones)

## Troubleshooting

- **No data found**: Check ticker symbol validity with `python main.py info TICKER`
- **Import errors**: Install requirements with `pip install -r requirements.txt`
- **Empty charts**: Ensure data exists in `data/` directory
- **Date issues**: Use YYYY-MM-DD format for dates

## Advanced Usage

### Scripting Integration

```python
from stock_downloader import StockDownloader
from stock_visualizer import StockVisualizer

# Download data programmatically
downloader = StockDownloader()
data = downloader.download_stock_data("PLTR", "2023-01-01", "2024-01-01")

# Create custom visualizations
visualizer = StockVisualizer()
visualizer.plot_single_stock("PLTR")
```
