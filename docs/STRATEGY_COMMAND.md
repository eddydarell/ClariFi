# Strategy Command Documentation

## Overview

The `strategy` command in ClariFi generates time-sensitive investment strategies based on comprehensive multi-dimensional analysis. Unlike simple buy/hold recommendations, this command provides actionable strategies with specific timeframes like "BUY now and SELL in 2 days" or "HOLD for 2 months."

## Features

The strategy analyzer combines:

1. **Multi-timeframe Trend Analysis**
   - Short-term (10 vs 20-day SMA)
   - Medium-term (20 vs 50-day SMA)
   - Long-term (50 vs 200-day SMA)
   - Recent price momentum (30-day slope)

2. **Technical Indicators**
   - RSI (Relative Strength Index) for overbought/oversold conditions
   - MACD (Moving Average Convergence Divergence) for momentum
   - ADX (Average Directional Index) for trend strength
   - Williams %R and CCI for additional confirmation
   - Market regime detection (Trending, Ranging, Volatile)

3. **Seasonal Patterns**
   - Monthly performance statistics
   - Best and worst performing months
   - Holiday effects analysis
   - Seasonal bias scoring

4. **Risk Metrics**
   - Maximum drawdown
   - Sharpe ratio (risk-adjusted returns)
   - Value at Risk (VaR 95%)
   - Historical volatility

5. **Deep Backtesting** (Optional)
   - Chunked historical analysis
   - Precision coefficient calculation
   - Strategy validation across multiple periods

6. **Optimal Timeframe Determination**
   - Analyzes historical performance across multiple holding periods
   - Calculates win rates for 2-day, 5-day, 1-week, 2-week, 1-month, and 2-month periods
   - Suggests optimal timeframe based on historical patterns

7. **Future Price Predictions**
   - Short-term (5 days ahead)
   - Mid-term (30 days / 1 month ahead)
   - Long-term (90 days / 3 months ahead)
   - Confidence levels and key reasoning for each prediction
   - Based on trend extrapolation, seasonal patterns, and momentum factors

8. **Optimal Buy/Sell Moment** (With --optimum flag)
   - Identifies the best possible moment to enter or exit a position
   - Analyzes seasonal patterns to find best/worst months
   - Evaluates technical indicators for optimal entry/exit points
   - Calculates risk-reward ratios
   - Considers support/resistance levels and historical patterns
   - Provides comprehensive reasoning and supporting analysis

## Usage

### Basic Usage

```bash
./clarifi.sh strategy AAPL --period 1y
```

### With Deep Backtesting

```bash
./clarifi.sh strategy TSLA --period 2y --include-deep
```

### Find Optimal Buy/Sell Moment

```bash
./clarifi.sh strategy MSFT --period 2y --optimum
```

### Complete Analysis (All Features)

```bash
./clarifi.sh strategy NVDA --period 2y --include-deep --optimum
```

### Using Existing Data (Skip Download)

```bash
./clarifi.sh strategy AAPL --period 6mo --no-download --optimum
```

### With Custom Deep Analysis Parameters

```bash
./clarifi.sh strategy TSLA --period 2y --include-deep --deep-chunk-months 6 --optimum
```

## Command Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `ticker` | - | Stock ticker symbol (single ticker only) | Required |
| `--period` | `-p` | Time period for analysis | `1y` |
| `--no-download` | - | Skip downloading fresh data | `false` |
| `--include-deep` | - | Include deep backtesting analysis | `false` |
| `--deep-chunk-months` | - | Chunk size in months for deep analysis | `3` |
| `--optimum` | - | Find optimal buy/sell moment based on all KPIs | `false` |

## Output

The strategy command provides:

### Strategy Recommendation

- **Action**: BUY, SELL, or HOLD
- **Timeframe**: Optimal holding period (e.g., "2 days", "1 week", "2 months")
- **Target Date**: Estimated date for action
- **Confidence**: HIGH, MEDIUM, or LOW
- **Risk Level**: LOW, MEDIUM, or HIGH
- **Expected Return**: Projected return percentage (if applicable)

### Rationale

- List of key factors driving the recommendation
- Specific technical signals and conditions
- Risk warnings if applicable

### Key Metrics

- Overall score (0-100)
- Trend directions (short/medium/long-term)
- Risk metrics (drawdown, Sharpe ratio, VaR)
- Market regime classification

### Future Price Predictions

For each timeframe (short/mid/long-term), the output includes:

- **Target Date**: When the prediction applies
- **Predicted Price**: Estimated price at target date
- **Predicted Change %**: Expected percentage change
- **Confidence**: LOW, MEDIUM, or HIGH
- **Key Factors**: Top 3 factors influencing the prediction

**Prediction Timeframes:**

- Short-term: 5 days ahead
- Mid-term: 30 days (1 month) ahead
- Long-term: 90 days (3 months) ahead

**Prediction Methodology:**

- Combines trend extrapolation with momentum indicators
- Adjusts for seasonal patterns and historical performance
- Factors in volatility for confidence adjustment
- Weighted by timeframe: short-term favors trends, long-term favors seasonality

### Optimal Buy/Sell Moment (--optimum flag)

When the `--optimum` flag is enabled, the output includes:

- **Recommended Action**: BUY or SELL based on comprehensive analysis
- **Optimal Date**: Best timing for the action
- **Timing**: Days from now or immediate action
- **Expected Price**: Price at optimal moment
- **Expected Return**: Projected return from the action
- **Confidence**: LOW, MEDIUM, or HIGH based on signal strength
- **Risk/Reward Ratio**: Calculated potential gain vs. potential loss
- **Key Reasoning**: Top factors supporting the timing recommendation
- **Supporting Analysis**:
  - Signal type (seasonal, technical, pattern-based, support/resistance)
  - Target month (if seasonal)
  - Optimal hold period (if pattern-based)
  - Historical win rate
  - Trend alignment (aligned or contrarian)

**Optimal Moment Analysis Factors:**

1. **Seasonal Patterns**: Identifies best/worst months historically
2. **Technical Indicators**: RSI oversold/overbought conditions
3. **Historical Patterns**: Best performing timeframes and win rates
4. **Deep Backtesting**: Recent chunk performance
5. **Support/Resistance**: Key price levels
6. **Risk Metrics**: Maximum drawdown and volatility considerations
7. **Multi-timeframe Trends**: Short/medium/long-term alignment

## Strategy Scoring

```text

The strategy analyzer uses a composite scoring system (-100 to +100):

### Trend Signals (40% weight)

- Short-term trend: ±15 points
- Medium-term trend: ±15 points
- Long-term trend: ±10 points

### Momentum Signals (25% weight)

- RSI oversold/overbought: ±15 points
- MACD crossover: ±10 points

### Seasonal Signals (15% weight)

- Entering strong/weak month: ±10 points
- Seasonal bias: ±5 points

### Deep Backtest Signals (10% weight)

- Latest performance > 5%: +10 points
- Latest performance < -5%: -10 points

### Volatility/Risk Signals (10% weight)

- High volatility: -10 points

### Action Thresholds

- **BUY**: Score ≥ 40
- **SELL**: Score ≤ -40
- **HOLD**: Score between -40 and 40

## Confidence Levels

- **HIGH**: |Score| ≥ 60 AND 2+ confirming factors (e.g., seasonal tailwind, backtest validation)
- **MEDIUM**: |Score| between 30-60 OR mixed short/medium trends
- **LOW**: |Score| < 30 OR insufficient data

## Examples

### Example 1: Strong Buy Signal

```bash
./clarifi.sh strategy NVDA --period 1y --include-deep
```

Output might show:

- 🟢 ACTION: BUY
- ⏱️ TIMEFRAME: 1 week
- 🎯 CONFIDENCE: HIGH
- Expected Return: +5.2%
- Rationale: Strong uptrend across all timeframes, oversold RSI, entering historically strong month

### Example 2: High Risk Sell Signal

```bash
./clarifi.sh strategy GME --period 1y
```

Output might show:

- 🔴 ACTION: SELL
- ⏱️ TIMEFRAME: 2 days
- 🎯 CONFIDENCE: MEDIUM
- ⚠️ RISK LEVEL: HIGH
- Rationale: Downtrend, overbought RSI, high volatility, significant drawdown risk

### Example 3: Mixed Signals Hold

```bash
./clarifi.sh strategy AAPL --period 1y
```

Output might show:

- 🟡 ACTION: HOLD
- ⏱️ TIMEFRAME: Current
- 🎯 CONFIDENCE: MEDIUM
- Rationale: Short-term uptrend but overbought conditions, awaiting clearer signals

## Best Practices

1. **Use Longer Periods**: For more reliable seasonal analysis, use periods of 2y or longer
2. **Enable Deep Backtesting**: Add `--include-deep` for higher confidence strategies
3. **Check Multiple Timeframes**: Compare strategies with different `--period` values
4. **Validate with Fresh Data**: Avoid using `--no-download` for critical decisions
5. **Consider Risk Level**: Always factor in the risk level with your strategy
6. **Multiple Analysis**: Run strategy command alongside `analyze` and `ai` commands for comprehensive view

## Limitations

1. **Single Ticker Only**: The strategy command analyzes one ticker at a time (by design for focused analysis)
2. **Historical Data Required**: Needs at least 60 data points (preferably 200+)
3. **Seasonal Analysis**: Requires longer periods (2y+) for accurate seasonal patterns
4. **Not Financial Advice**: Automated strategy recommendations should not replace professional financial advice
5. **Market Conditions**: Past performance does not guarantee future results

## Integration with Other Commands

The strategy command works well with other ClariFi commands:

```bash
# Step 1: Get comprehensive analysis
./clarifi.sh analyze AAPL --period 1y --include-deep

# Step 2: Get AI-powered recommendation
./clarifi.sh ai AAPL --period 1y

# Step 3: Get time-sensitive strategy
./clarifi.sh strategy AAPL --period 1y --include-deep

# Step 4: Monitor live
./clarifi.sh live AAPL
```

## Technical Implementation

The strategy analyzer:

1. Downloads/loads historical data
2. Calculates technical indicators using PatternAnalyzer
3. Runs seasonal analysis using SeasonalAnalyzer
4. Optionally runs deep backtesting using ClariFiEngine
5. Analyzes multiple timeframes (2-day to 2-month forward returns)
6. Synthesizes all signals into a composite score
7. Determines optimal timeframe based on historical win rates
8. Assigns confidence level based on signal strength and alignment
9. Generates actionable recommendation with rationale

## Troubleshooting

### "Insufficient data for analysis"

- Solution: Increase `--period` to at least 1 year or download more historical data

### "Seasonal analysis unavailable"

- Solution: Use periods of 2y or longer for reliable seasonal patterns

### "Deep analysis failed"

- Solution: Ensure ClariFiEngine is properly installed and period has sufficient data

### "Mixed signals / Low confidence"

- This is normal - the strategy is being conservative when market signals conflict
- Consider waiting for clearer signals or using a longer analysis period

## Future Enhancements

Planned improvements:

- Portfolio-level strategy recommendations
- Multi-ticker correlation strategies
- Options strategy suggestions
- Stop-loss and take-profit level recommendations
- Integration with ML models for enhanced predictions
- Real-time strategy updates with live monitoring
