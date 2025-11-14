# Future Price Predictions Feature

## Overview

The ClariFi strategy analyzer now includes future price predictions for short, mid, and long-term timeframes. These predictions complement the investment strategy recommendations by providing concrete price targets and expected changes.

## Prediction Timeframes

| Timeframe | Horizon | Description |
|-----------|---------|-------------|
| **Short-term** | 5 days | Near-term price movement based primarily on recent trends and momentum |
| **Mid-term** | 30 days (1 month) | Balanced prediction considering trends, momentum, and seasonal patterns |
| **Long-term** | 90 days (3 months) | Forward-looking prediction weighted toward seasonal patterns and fundamentals |

## Prediction Components

Each prediction includes:

1. **Target Date**: The date when the prediction applies
2. **Predicted Price**: Estimated stock price at the target date
3. **Predicted Change %**: Expected percentage change from current price
4. **Confidence Level**: LOW, MEDIUM, or HIGH
5. **Key Factors**: Top 3 factors influencing the prediction

## Methodology

### Weighting by Timeframe

Different timeframes use different weight distributions:

#### Short-term (5 days)

- Trend: 60% - Heavy emphasis on recent price movements
- Momentum: 30% - Technical indicators like RSI, MACD
- Seasonal: 10% - Minimal seasonal influence

#### Mid-term (30 days)

- Trend: 40% - Balanced trend analysis
- Momentum: 30% - Technical momentum signals
- Seasonal: 30% - Monthly seasonal patterns

#### Long-term (90 days)

- Trend: 30% - Long-term directional bias
- Momentum: 20% - Momentum as confirmation
- Seasonal: 50% - Strong seasonal influence

### Prediction Calculation

1. **Trend Component**
   - Short-term: Uses 10 vs 20-day SMA crossover
   - Mid-term: Uses 20 vs 50-day SMA crossover
   - Long-term: Uses 50 vs 200-day SMA crossover
   - Historical return rates from multi-timeframe analysis

2. **Momentum Component**
   - RSI levels (oversold <30 suggests bounce, overbought >70 suggests pullback)
   - MACD crossovers (bullish/bearish signals)
   - Rate of Change (ROC) for velocity

3. **Seasonal Component**
   - Monthly average returns
   - Best/worst month identification
   - Seasonal bias scoring
   - Holiday effects (when applicable)

4. **Volatility Adjustment**
   - High volatility (>40): Wider prediction range, lower confidence
   - Medium volatility (25-40): Standard prediction, medium confidence
   - Low volatility (<25): Tighter prediction, higher confidence

### Confidence Levels

- **HIGH**: Strong score (≥60), low volatility, aligned signals
- **MEDIUM**: Moderate score (30-60), normal volatility, or mixed signals
- **LOW**: Weak score (<30), high volatility, or insufficient data

## Example Output

```text
🔮 FUTURE PRICE PREDICTIONS:

  📅 SHORT-TERM (5 days):
     Target Date: 2025-11-19
     📈 Predicted Price: $275.50 (+2.35%)
     🎯 Confidence: MEDIUM
     💡 Key Factors: Short-term bullish trend, MACD bullish crossover, Strong momentum

  📅 MID-TERM (30 days / ~1 month):
     Target Date: 2025-12-14
     📈 Predicted Price: $282.10 (+4.80%)
     🎯 Confidence: MEDIUM
     💡 Key Factors: Medium-term bullish trend, Entering historically strong period

  📅 LONG-TERM (90 days / ~3 months):
     Target Date: 2026-02-12
     📈 Predicted Price: $295.00 (+9.58%)
     🎯 Confidence: HIGH
     💡 Key Factors: Long-term bullish trend, Strong seasonal bias, Historical outperformance
```

## Interpretation Guidelines

### Understanding the Predictions

1. **Directional Bias**: Up (📈) or Down (📉) arrows indicate predicted direction
2. **Magnitude**: Percentage change shows expected move size
3. **Confidence**: Consider this when evaluating reliability
4. **Key Factors**: Review these to understand the prediction drivers

### Best Practices

1. **Use Multiple Timeframes**: Compare short, mid, and long-term predictions for consistency
2. **Check Confidence**: Higher confidence predictions are more reliable
3. **Review Key Factors**: Understand what's driving each prediction
4. **Consider Context**: Combine with strategy recommendation and risk metrics
5. **Longer Periods = Better Data**: Use 2y+ periods for more reliable seasonal components

### Limitations

- **Not Financial Advice**: These are statistical projections, not guarantees
- **Data Quality**: Predictions depend on historical data availability and quality
- **Market Changes**: Unexpected events can invalidate predictions
- **Volatility**: High volatility environments reduce prediction accuracy
- **Seasonality**: Requires 2+ years of data for reliable seasonal components

## Integration with Strategy

Predictions complement the strategy recommendation:

- **BUY Signal** + **Positive Predictions** = Strong alignment
- **SELL Signal** + **Negative Predictions** = Confirmed downside
- **HOLD Signal** + **Mixed Predictions** = Wait for clearer direction
- **Conflicting Signals** = Review confidence levels and key factors

## Technical Implementation

### Data Classes

```python
@dataclass
class PricePrediction:
    timeframe: str           # 'short_term', 'mid_term', 'long_term'
    horizon_days: int        # Number of days ahead
    target_date: str         # Target date (YYYY-MM-DD)
    predicted_price: float   # Predicted stock price
    predicted_change_pct: float  # Expected % change
    confidence: str          # 'LOW', 'MEDIUM', 'HIGH'
    reasoning: List[str]     # Top 3 factors
```

### Algorithm Flow

1. Gather current signals (trend, momentum, seasonal, risk)
2. For each timeframe (short/mid/long):
   - Calculate trend-based prediction
   - Calculate momentum-based prediction
   - Calculate seasonal-based prediction
   - Combine with timeframe-specific weights
   - Apply volatility adjustment
   - Determine confidence level
   - Generate reasoning
3. Return dictionary of predictions

## Usage

Predictions are automatically generated with every strategy command:

```bash
# Basic usage
./clarifi.sh strategy AAPL --period 1y

# With deep analysis
./clarifi.sh strategy TSLA --period 2y --include-deep

# Using existing data
./clarifi.sh strategy MSFT --no-download
```

No additional flags are needed - predictions are always included in the output.

## Future Enhancements

Potential improvements for future versions:

- Machine learning integration for adaptive weighting
- Sentiment analysis from news and social media
- Economic indicator correlation
- Sector-specific adjustments
- Volatility surface modeling
- Monte Carlo simulation ranges
- Backtesting of prediction accuracy

## Disclaimer

**Important**: Price predictions are statistical estimates based on historical patterns and technical analysis. They should not be used as the sole basis for investment decisions. Always:

- Conduct your own research
- Consider your risk tolerance
- Diversify your portfolio
- Consult with financial professionals
- Stay informed about market conditions

Past performance does not guarantee future results.
