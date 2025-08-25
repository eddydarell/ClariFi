# Portfolio Management Features Update

## Overview

This update adds three key portfolio management features to the ClariFi Engine:

1. **Portfolio Update** - Modify portfolio name and description
2. **Portfolio Deletion** - Safe deletion with confirmation
3. **Portfolio Price Sync** - Fetch latest prices for all tickers

## Features Added

### 1. Portfolio Update

Update a portfolio's name and/or description.

```python
# Update both name and description
result = engine.update_portfolio(
    portfolio_id="your-portfolio-id",
    name="New Portfolio Name",
    description="New description"
)

# Update only the name
result = engine.update_portfolio(
    portfolio_id="your-portfolio-id",
    name="New Name Only"
)

# Update only the description
result = engine.update_portfolio(
    portfolio_id="your-portfolio-id",
    description="New description only"
)
```

**Response Format:**

```python
{
    "success": True,
    "message": "Portfolio updated successfully",
    "portfolio_id": "uuid-here"
}
```

### 2. Portfolio Deletion

Safely delete a portfolio with name confirmation to prevent accidental deletions.

```python
# Delete portfolio (requires exact name match - case sensitive)
result = engine.delete_portfolio(
    portfolio_id="your-portfolio-id",
    confirmation_name="Exact Portfolio Name"  # Must match exactly!
)
```

**Features:**

- **Case-sensitive confirmation** - Must type exact portfolio name
- **Warning message** - Shows clear warning about irreversible action
- **Cascading delete** - Removes all associated tickers
- **Count reporting** - Reports how many tickers were deleted

**Response Format:**

```python
{
    "success": True,
    "message": "Portfolio 'Portfolio Name' deleted successfully",
    "deleted_tickers": 5,
    "portfolio_id": "uuid-here"
}
```

**Error Response (wrong confirmation):**

```python
{
    "success": False,
    "error": "Name confirmation failed",
    "message": "Please type the exact portfolio name 'Portfolio Name' to confirm deletion",
    "warning": "⚠️  Portfolio deletion is irreversible and will remove all associated data!"
}
```

### 3. Portfolio Price Sync

Fetch the most recent prices for all tickers in a portfolio and update the database.

```python
# Sync all ticker prices in a portfolio
result = engine.sync_portfolio_prices(portfolio_id="your-portfolio-id")
```

**Features:**

- **Real-time price fetching** - Uses the stock downloader to get latest prices
- **Batch processing** - Handles multiple tickers efficiently
- **Error handling** - Gracefully handles individual ticker failures
- **Progress reporting** - Shows sync progress and results
- **Performance metrics** - Reports execution time and success rates

**Response Format:**

```python
{
    "success": True,
    "message": "Portfolio sync completed",
    "portfolio_name": "My Portfolio",
    "portfolio_id": "uuid-here",
    "total_tickers": 5,
    "successful_syncs": 4,
    "failed_syncs": 1,
    "sync_results": {
        "AAPL": {
            "success": True,
            "previous_price": 220.50,
            "current_price": 227.76,
            "price_change": 7.26,
            "price_change_pct": 3.29
        },
        "INVALID": {
            "success": False,
            "error": "No price data available"
        }
    },
    "execution_time": 2.45,
    "timestamp": "2025-08-25T08:00:00"
}
```

## Database Changes

### Schema Updates

Added new columns to `portfolio_tickers` table:

- `current_price REAL DEFAULT 0.0` - Stores the most recent price
- `updated_at TIMESTAMP` - Tracks when the price was last updated

### New Methods in Portfolio Model

- `update(portfolio_id, name=None, description=None)` - Update portfolio
- `delete(portfolio_id)` - Delete portfolio and associated tickers
- `update_ticker_price(portfolio_id, ticker, current_price)` - Update ticker price
- `get_by_name(name)` - Find portfolio by name

## Usage Examples

### Complete Workflow Example

```python
from core.engine import ClariFiEngine

# Initialize engine
engine = ClariFiEngine()

# Create a portfolio
result = engine.create_portfolio("My Tech Stocks", "Technology sector investments")
portfolio_id = result["portfolio_id"]

# Add some tickers
engine.add_ticker_to_portfolio(portfolio_id, "AAPL", 10, 150.0)
engine.add_ticker_to_portfolio(portfolio_id, "MSFT", 5, 300.0)
engine.add_ticker_to_portfolio(portfolio_id, "GOOGL", 2, 2500.0)

# Update portfolio details
engine.update_portfolio(
    portfolio_id,
    description="Updated: Focus on large-cap tech stocks"
)

# Sync prices to get latest values
sync_result = engine.sync_portfolio_prices(portfolio_id)
print(f"Synced {sync_result['successful_syncs']} out of {sync_result['total_tickers']} tickers")

# Later, if you want to delete the portfolio
portfolio = engine.portfolio_model.get_by_id(portfolio_id)
delete_result = engine.delete_portfolio(portfolio_id, portfolio["name"])
```

### Helper Methods

```python
# Get portfolio by name instead of ID
portfolio = engine.get_portfolio_by_name("My Tech Stocks")

# List all portfolios
portfolios = engine.get_portfolios()
for p in portfolios:
    print(f"{p['name']}: {len(engine.get_portfolio_tickers(p['id']))} tickers")
```

## Error Handling

All methods return standardized response formats with:

- `success`: Boolean indicating if operation succeeded
- `message`: Human-readable status message
- `error`: Error details (when success=False)
- Additional context-specific fields

### Common Error Scenarios

1. **Portfolio not found** - Invalid portfolio ID
2. **Name confirmation failed** - Incorrect deletion confirmation
3. **Database errors** - Connection or query issues
4. **Price fetch failures** - Network or data source issues

## Security Features

- **Confirmation required for deletion** - Prevents accidental data loss
- **Case-sensitive confirmation** - Reduces chance of typos causing deletion
- **Warning messages** - Clear communication about irreversible actions
- **Graceful error handling** - No crashes on invalid input

## Performance Considerations

- **Efficient database operations** - Single queries where possible
- **Batch price fetching** - Optimized for multiple tickers
- **Error isolation** - Individual ticker failures don't stop the process
- **Progress reporting** - User feedback during long operations

## Testing

Run the test script to verify all features work correctly:

```bash
cd /path/to/ClariFi
source venv/bin/activate
python3 test_portfolio_features.py
```

The test script demonstrates:

- Portfolio creation and updates
- Ticker management
- Price synchronization
- Safe deletion with confirmation
- Error handling scenarios
