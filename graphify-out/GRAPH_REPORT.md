# Graph Report - ClariFi  (2026-08-24)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 933 nodes · 1606 edges · 49 communities (45 shown, 4 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 73 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9ca8060b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- RLAnalyzer
- StrategyAnalyzer
- ClariFiEngine
- OptionsAnalyzer
- AIAnalyzer
- LiveStockMonitor
- TransformerAnalyzer
- .comprehensive_analysis
- make_price_data
- MLAnalyzer
- RNNAnalyzer
- Portfolio
- AlphaVantageAnalyzer
- server.py
- engine.py
- PatternAnalyzer
- AdvancedStockAnalysis
- StockScreener
- .analyze
- DatabaseManager
- post
- main.py
- envelope
- AdvancedVisualizer
- .load_stock_data
- ClariFiCLI
- AnalysisResult
- clarifi_cli.py
- ._parse_event_date
- .download_stock_data
- forecast_prices
- ConnectionManager
- EventCorrelator
- .generate_investment_suggestion
- setup_completion.sh
- run_comprehensive_analysis
- import_events.py
- screen_market_v1
- _clarifi_completion.bash
- remove_ticker_from_portfolio
- clarifi.sh
- run_ingestion.sh
- setup_venv.sh
- start_clarifi.sh

## God Nodes (most connected - your core abstractions)
1. `ClariFiEngine` - 47 edges
2. `AdvancedStockAnalysis` - 33 edges
3. `DatabaseManager` - 33 edges
4. `StrategyAnalyzer` - 29 edges
5. `OptionsAnalyzer` - 27 edges
6. `AIAnalyzer` - 24 edges
7. `make_price_data()` - 22 edges
8. `LiveStockMonitor` - 21 edges
9. `MLAnalyzer` - 21 edges
10. `main()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `analyzer()` --uses--> `StrategyAnalyzer`  [INFERRED]
  tests/test_strategy_analyzer.py → core/strategy_analyzer.py
- `TestMultiTimeframe` --uses--> `StrategyAnalyzer`  [INFERRED]
  tests/test_strategy_analyzer.py → core/strategy_analyzer.py
- `ClariFiEngine` --uses--> `Portfolio`  [INFERRED]
  core/engine.py → database/models.py
- `ClariFiEngine` --uses--> `CommandHistory`  [INFERRED]
  core/engine.py → database/models.py
- `ClariFiEngine` --uses--> `ComparisonResult`  [INFERRED]
  core/engine.py → database/models.py

## Import Cycles
- None detected.

## Communities (49 total, 4 thin omitted)

### Community 0 - "RLAnalyzer"
Cohesion: 0.06
Nodes (31): Any, DataFrame, Reset environment to initial state., Get current observation., Execute one step in the environment., Render environment state., Reinforcement Learning agent for trading using Q-Learning or PPO., Make prediction using trained model. (+23 more)

### Community 1 - "StrategyAnalyzer"
Cohesion: 0.07
Nodes (30): OptimalMoment, PricePrediction, any, DataFrame, Series, Calculate days from now to the start of target month., Create a default optimal moment when no clear signal exists., Create a default strategy when insufficient data is available. (+22 more)

### Community 2 - "ClariFiEngine"
Cohesion: 0.07
Nodes (27): ClariFiEngine, Any, DataFrame, Get accuracy trends for model refinement, Analyze entire portfolio, Convenience wrapper to run comprehensive analysis with deep backtesting…, Log command execution, Update command execution status (+19 more)

### Community 3 - "OptionsAnalyzer"
Cohesion: 0.08
Nodes (27): create_sample_data(), demo_black_scholes(), demo_investment_suggestions(), demo_risk_analysis(), main(), Demonstrate investment suggestion engine., Create sample stock data for demonstration., Run all demonstrations. (+19 more)

### Community 4 - "AIAnalyzer"
Cohesion: 0.09
Nodes (20): AIAnalyzer, BacktestResult, is_probable_portfolio_identifier(), Any, DataFrame, Series, Very light heuristic to detect if a single argument might be a portfolio id…, Build enhanced, structured prompt for consistent AI responses across models. (+12 more)

### Community 5 - "LiveStockMonitor"
Cohesion: 0.07
Nodes (23): demo_live_monitor(), Fore, Demo the live monitor with automatic exit, Style, LiveStockMonitor, main(), Update prices for all monitored tickers, Fetch updates and return data (for API usage) (+15 more)

### Community 6 - "TransformerAnalyzer"
Cohesion: 0.08
Nodes (25): DataFrame, Model, ndarray, Build the TFT model architecture., Transformer-based Analyzer for stock price prediction. Implements Temporal…, Get list of available Transformer models., Create comprehensive technical features for Transformer analysis. Args: data:…, Prepare sequences for Transformer training. Args: data: Feature-engineered data… (+17 more)

### Community 7 - ".comprehensive_analysis"
Cohesion: 0.09
Nodes (18): Generate a comprehensive text summary of all analyses. Accepts…, Analyze ticker across multiple timeframes for trend confirmation. Args: ticker…, Display enhanced ticker summary with recommendations and accuracy highlighting., Display highlighted investment opportunities and risks based on combined…, Run all available analysis commands sequentially for a single ticker and return…, Print a consistent header for all analysis types., Legacy quick analysis method., Print a consistent section header. (+10 more)

### Community 8 - "make_price_data"
Cohesion: 0.08
Nodes (12): fixture, analyzer(), make_price_data(), Generate synthetic OHLCV data with a trend and noise., TestDaysToMonth, TestInsufficientData, TestMultiTimeframe, TestOptimalMoment (+4 more)

### Community 9 - "MLAnalyzer"
Cohesion: 0.09
Nodes (22): MLAnalysisResult, MLAnalyzer, MLModelResult, MLRecommendation, Any, DataFrame, ndarray, Series (+14 more)

### Community 10 - "RNNAnalyzer"
Cohesion: 0.09
Nodes (22): DataFrame, Model, ndarray, Get list of available RNN models., Create technical features for RNN analysis. Args: data: Stock price data…, Create sequences for RNN training. Args: data: Scaled feature data seq_length:…, Build Bidirectional LSTM model., Build Bidirectional GRU model. (+14 more)

### Community 11 - "Portfolio"
Cohesion: 0.07
Nodes (17): Portfolio, Any, Portfolio model for managing collections of tickers, Create a new portfolio, Get portfolio by name, Add a ticker to portfolio, Remove a ticker from portfolio, Update the current price for a ticker in portfolio (+9 more)

### Community 12 - "AlphaVantageAnalyzer"
Cohesion: 0.13
Nodes (14): AlphaVantageAnalyzer, Any, Get company overview data. Args: symbol: Stock ticker symbol Returns: Dict…, Get income statement data. Args: symbol: Stock ticker symbol annual: If True,…, Get balance sheet data. Args: symbol: Stock ticker symbol annual: If True, get…, Alpha Vantage API client for financial data and analysis., Get cash flow statement data. Args: symbol: Stock ticker symbol annual: If…, Get earnings data. Args: symbol: Stock ticker symbol Returns: Dict containing… (+6 more)

### Community 13 - "server.py"
Cohesion: 0.12
Nodes (24): get_accuracy_trends(), get_analysis_history(), get_command_history(), get_favicon(), get_portfolio(), get_portfolio_analytics(), get_portfolio_info(), get_portfolio_tickers() (+16 more)

### Community 14 - "engine.py"
Cohesion: 0.10
Nodes (14): Back, Fore, main(), Style, main(), CommandHistory, ComparisonResult, datetime (+6 more)

### Community 15 - "PatternAnalyzer"
Cohesion: 0.10
Nodes (12): PatternAnalyzer, Find which stocks tend to lead others in price movements., Analyze correlation patterns between stocks over rolling windows. Args:…, Create a summary of detected patterns., Detect volatility patterns and clustering. Args: stock_data_dict (dict):…, Calculate a score indicating how clustered volatility periods are., Identify support and resistance levels using peak detection. Args: stock_data…, Calculate distances from current price to support/resistance levels. (+4 more)

### Community 16 - "AdvancedStockAnalysis"
Cohesion: 0.13
Nodes (13): AdvancedStockAnalysis, main(), Print an info message., StockAnalysis, InvestmentAdvisor, Analyzes seasonal patterns and holiday effects in stock data., SeasonalAnalyzer, Get list of available CSV files. (+5 more)

### Community 17 - "StockScreener"
Cohesion: 0.12
Nodes (13): demo_market_screening(), Demo the market screening functionality, Fore, main(), Get recently listed stocks (IPOs) This is a simplified version - in practice…, Format screener results for display, Main screening function Args: category: "gainers", "losers", "actives", or…, CLI for stock screener (+5 more)

### Community 18 - ".analyze"
Cohesion: 0.11
Nodes (13): DataFrame, datetime, Analyze performance patterns by month., Analyze stock performance around major holidays., Results from seasonal pattern analysis., Calculate stock performance around a specific holiday., Calculate overall seasonal bias score (0-1, higher = more seasonal)., Identify the best and worst performing months. (+5 more)

### Community 19 - "DatabaseManager"
Cohesion: 0.13
Nodes (12): DatabaseManager, Context manager for database connections, Initialize database with all required tables, Insert a new event into the events table., Fetch all events from the events table., Insert or update ticker OHLCV rows., Fetch OHLCV rows for ticker ordered by date ascending., Get all tickers that have persisted price data. (+4 more)

### Community 20 - "post"
Cohesion: 0.12
Nodes (20): add_ticker_to_portfolio(), analyze_portfolio(), compare_predictions(), ComparisonRequest, comprehensive_analysis_v1(), ComprehensiveV1Request, create_portfolio(), generate_strategy() (+12 more)

### Community 21 - "main.py"
Cohesion: 0.15
Nodes (15): Back, Fore, # TODO: Implement CSV export if requested, Style, main(), Test the seasonal analyzer with sample data., import_events_from_json(), main() (+7 more)

### Community 22 - "envelope"
Cohesion: 0.23
Nodes (14): generate_predictions_v1(), generate_strategy_v1(), PredictionRequest, Return validated baseline forecasts using the canonical result envelope., Canonical wrapper around the existing explainable strategy analysis., envelope(), error_item(), Any (+6 more)

### Community 23 - "AdvancedVisualizer"
Cohesion: 0.14
Nodes (7): AdvancedVisualizer, Plot rolling correlations over time., Visualize the impact of events on stock prices. Args: event_correlations…, Visualize volatility clustering patterns. Args: volatility_analysis (dict):…, Create output directory if it doesn't exist., Create an advanced correlation heatmap with annotations. Args: correlation_data…, Plot support and resistance levels on price charts. Args:…

### Community 24 - ".load_stock_data"
Cohesion: 0.19
Nodes (7): Find database-backed ticker handles, with CSV fallback., Extract ticker symbol from filename., Choose latest CSV source, or use DB source handle directly., Create a comprehensive chart for a single stock., Create comparison chart for multiple stocks., Create correlation matrix for multiple stocks., Load stock data from CSV file.

### Community 25 - "ClariFiCLI"
Cohesion: 0.17
Nodes (8): Back, ClariFiCLI, Fore, main(), Format and display analysis results, Test if the ClariFi API is accessible, Run comprehensive analysis for given tickers, Style

### Community 26 - "AnalysisResult"
Cohesion: 0.15
Nodes (7): AnalysisResult, Analysis results model, Save analysis results, Get analysis results for a ticker, Get analysis results for a portfolio, Get all analysis results, Update analysis status and add to history

### Community 27 - "clarifi_cli.py"
Cohesion: 0.44
Nodes (11): _apply_graph_defaults(), _delegate_to_legacy(), _emit(), _err(), _extract_json(), main(), _normalize_delegated_payload(), _ok() (+3 more)

### Community 28 - "._parse_event_date"
Cohesion: 0.17
Nodes (6): Identify unusual price movements that might correlate with events. Args:…, Find events within a window of the target date., Get all events within a specific period., Safely parse event date, handling malformed dates and yyyy-mm format., Correlate major events with stock movements. Args: stock_data_dict (dict):…, Analyze the impact of a specific event on a stock.

### Community 29 - ".download_stock_data"
Cohesion: 0.17
Nodes (6): Save stock data to CSV file., Persist OHLCV rows so SQLite is the authoritative source., Download data for multiple stock tickers. Args: tickers (list): List of ticker…, Validate data quality and completeness. Args: data (pd.DataFrame): Stock data…, Clean and prepare data for analysis. Args: data (pd.DataFrame): Raw stock data…, Download stock data for a specific ticker. Args: ticker (str): Stock ticker…

### Community 30 - "forecast_prices"
Cohesion: 0.25
Nodes (10): _features(), Forecast, forecast_prices(), Any, DataFrame, Series, Small, auditable forecasting engine with walk-forward evaluation. Models…, Evaluate only matured, forward observations with a simple expanding window. (+2 more)

### Community 31 - "ConnectionManager"
Cohesion: 0.24
Nodes (5): ConnectionManager, Manages WebSocket connections, WebSocket endpoint for real-time updates, websocket_endpoint(), WebSocket

### Community 32 - "EventCorrelator"
Cohesion: 0.22
Nodes (5): EventCorrelator, Generate a comprehensive summary of event-market correlations. Args:…, Add a custom event to the events database. Args: date (str): Event date in…, Load major historical events from the database. Returns a dict of event_date ->…, Get all events of a specific category.

### Community 33 - ".generate_investment_suggestion"
Cohesion: 0.20
Nodes (5): Generate portfolio-level investment suggestions. Args: portfolio_data (dict):…, Calculate suggested holding period based on historical positive trends. Args:…, Forecast when a ticker is expected to climb based on historical recovery…, Assess portfolio diversification based on correlation analysis., Generate investment suggestions based on comprehensive analysis. Args:…

### Community 34 - "setup_completion.sh"
Cohesion: 0.44
Nodes (9): detect_shell(), remove_completion(), setup_all_shells(), setup_bash_completion(), setup_current_shell(), setup_zsh_completion(), setup_completion.sh script, show_usage() (+1 more)

### Community 35 - "run_comprehensive_analysis"
Cohesion: 0.29
Nodes (7): AnalysisRequest, MonitorRequest, Run comprehensive analysis on tickers, Start live monitoring, run_comprehensive_analysis(), start_monitoring(), BackgroundTasks

### Community 36 - "import_events.py"
Cohesion: 0.53
Nodes (5): import_events_from_json(), main(), process_ingest_folder(), Import events from a JSON file into the database. Args: json_file_path: Path to…, Process all JSON files in the ingest folder and move them to ingested folder…

### Community 37 - "screen_market_v1"
Cohesion: 0.40
Nodes (5): Screen the market for stocks, Canonical market-screening response for frontend and API clients., screen_market(), screen_market_v1(), ScreenerRequest

### Community 38 - "_clarifi_completion.bash"
Cohesion: 0.67
Nodes (3): _clarifi_completion.bash script, _clarifi_completion(), _clarifi_python_completion()

### Community 39 - "remove_ticker_from_portfolio"
Cohesion: 0.67
Nodes (3): Remove ticker from portfolio, remove_ticker_from_portfolio(), delete

## Knowledge Gaps
- **22 isolated node(s):** `Back`, `Fore`, `Style`, `Fore`, `Style` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ClariFiEngine` connect `ClariFiEngine` to `EventCorrelator`, `OptionsAnalyzer`, `.comprehensive_analysis`, `MLAnalyzer`, `Portfolio`, `server.py`, `engine.py`, `PatternAnalyzer`, `AdvancedStockAnalysis`, `DatabaseManager`, `main.py`, `AdvancedVisualizer`, `AnalysisResult`?**
  _High betweenness centrality (0.299) - this node is a cross-community bridge._
- **Why does `main()` connect `AdvancedStockAnalysis` to `RLAnalyzer`, `StrategyAnalyzer`, `ClariFiEngine`, `AIAnalyzer`, `LiveStockMonitor`, `TransformerAnalyzer`, `MLAnalyzer`, `RNNAnalyzer`, `AlphaVantageAnalyzer`, `PatternAnalyzer`, `StockScreener`, `main.py`?**
  _High betweenness centrality (0.250) - this node is a cross-community bridge._
- **Why does `StrategyAnalyzer` connect `StrategyAnalyzer` to `AdvancedStockAnalysis`, `make_price_data`, `server.py`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `ClariFiEngine` (e.g. with `AdvancedVisualizer` and `EventCorrelator`) actually correct?**
  _`ClariFiEngine` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `AdvancedStockAnalysis` (e.g. with `AdvancedVisualizer` and `ClariFiEngine`) actually correct?**
  _`AdvancedStockAnalysis` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `DatabaseManager` (e.g. with `ClariFiEngine` and `EventCorrelator`) actually correct?**
  _`DatabaseManager` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `StrategyAnalyzer` (e.g. with `main()` and `analyzer()`) actually correct?**
  _`StrategyAnalyzer` has 4 INFERRED edges - model-reasoned connections that need verification._