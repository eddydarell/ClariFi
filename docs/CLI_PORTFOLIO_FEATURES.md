# ClariFi Portfolio CLI Commands - New Features

## Overview

The ClariFi CLI has been enhanced with three new portfolio management commands:

1. **`portfolio update`** - Update portfolio name and/or description
2. **`portfolio delete`** - Safely delete portfolio with confirmation
3. **`portfolio sync`** - Fetch latest prices for all portfolio tickers

## Command Reference

### Portfolio Update

Update a portfolio's name and/or description.

```bash
# Update both name and description
./run.sh portfolio update <portfolio_id> --name "New Name" --description "New description"

# Update only the name
./run.sh portfolio update <portfolio_id> --name "New Portfolio Name"

# Update only the description
./run.sh portfolio update <portfolio_id> --description "Updated description"
```

**Example:**

```bash
./run.sh portfolio update a0a5a7ae-4d43-4387-90d4-89cd1ae894bd --name "My Tech Stocks" --description "Large cap technology investments"
```

**Output:**

```bash
✅ Portfolio updated successfully
   New name: My Tech Stocks
   New description: Large cap technology investments
```

### Portfolio Delete

Safely delete a portfolio with mandatory name confirmation to prevent accidental deletions.

```bash
./run.sh portfolio delete <portfolio_id> --confirm-name "Exact Portfolio Name"
```

**Features:**

- **Case-sensitive confirmation** - Must type exact portfolio name
- **Warning display** - Shows what will be deleted before proceeding
- **Cascading deletion** - Removes all associated tickers and analysis history

**Example:**

```bash
./run.sh portfolio delete a0a5a7ae-4d43-4387-90d4-89cd1ae894bd --confirm-name "My Tech Stocks"
```

**Output:**

```bash
⚠️  WARNING: You are about to delete portfolio 'My Tech Stocks'
   This action is IRREVERSIBLE and will:
   - Delete the portfolio permanently
   - Remove all 5 associated tickers
   - Remove all analysis history

✅ Portfolio 'My Tech Stocks' deleted successfully
   Deleted tickers: 5
```

**Error Example (wrong confirmation):**

```bash
./run.sh portfolio delete a0a5a7ae-4d43-4387-90d4-89cd1ae894bd --confirm-name "wrong name"
```

```bash
❌ Please type the exact portfolio name 'My Tech Stocks' to confirm deletion
   ⚠️  Portfolio deletion is irreversible and will remove all associated data!
```

### Portfolio Sync

Fetch the most recent market prices for all tickers in a portfolio and update the database.

```bash
./run.sh portfolio sync <portfolio_id>
```

**Features:**

- **Real-time price fetching** - Uses live market data
- **Batch processing** - Updates all tickers efficiently
- **Detailed reporting** - Shows price changes and sync status
- **Error handling** - Gracefully handles individual ticker failures

**Example:**

```bash
./run.sh portfolio sync a0a5a7ae-4d43-4387-90d4-89cd1ae894bd
```

**Output:**

```bash
🔄 Syncing prices for portfolio 'My Tech Stocks'...
📥 Fetching current price for AAPL...
✅ AAPL: $227.76
📥 Fetching current price for MSFT...
✅ MSFT: $507.23
📥 Fetching current price for GOOGL...
✅ GOOGL: $178.45

✅ Portfolio sync completed
   Portfolio: My Tech Stocks
   Total tickers: 3
   Successful syncs: 3
   Failed syncs: 0
   Execution time: 1.85s

📊 Price Update Details:
┌─────────┬─────────────┬─────────────┬─────────────┬──────────────┐
│ Ticker  │ Status      │ New Price   │ Change $    │ Change %     │
├─────────┼─────────────┼─────────────┼─────────────┼──────────────┤
│ AAPL    │ ✅ Updated   │ $227.76     │ +2.35       │ +1.04%       │
│ MSFT    │ ✅ Updated   │ $507.23     │ -1.87       │ -0.37%       │
│ GOOGL   │ ✅ Updated   │ $178.45     │ +5.23       │ +3.02%       │
└─────────┴─────────────┴─────────────┴─────────────┴──────────────┘
```

## Complete Portfolio Workflow Example

Here's a complete example showing how to use all the portfolio features:

```bash
# 1. Create a new portfolio
./run.sh portfolio create --name "My Investment Portfolio" --description "Long-term investments"
# Output: Created portfolio with ID: abc123...

# 2. Add some tickers
./run.sh portfolio add abc123... AAPL --quantity 10 --avg-cost 150
./run.sh portfolio add abc123... MSFT --quantity 5 --avg-cost 300
./run.sh portfolio add abc123... GOOGL --quantity 2 --avg-cost 2500

# 3. View portfolio contents
./run.sh portfolio tickers abc123...

# 4. Update portfolio details
./run.sh portfolio update abc123... --description "Diversified tech portfolio"

# 5. Sync latest prices
./run.sh portfolio sync abc123...

# 6. Run analysis
./run.sh portfolio analyze abc123... --period 6mo --summary-only

# 7. Check analysis history
./run.sh portfolio history --portfolio-id abc123... --limit 5

# 8. When ready to delete (be careful!)
./run.sh portfolio delete abc123... --confirm-name "My Investment Portfolio"
```

## Help Commands

Get help for any command:

```bash
# General portfolio help
./run.sh portfolio --help

# Specific command help
./run.sh portfolio update --help
./run.sh portfolio delete --help
./run.sh portfolio sync --help
```

## Error Handling

All commands provide clear error messages:

- **Portfolio not found**: Invalid portfolio ID
- **Missing confirmation**: Wrong or missing portfolio name for deletion
- **Validation errors**: Missing required parameters
- **Network errors**: Failed price fetching during sync
- **Database errors**: Connection or data issues

## Security Features

- **Confirmation required for deletion**: Prevents accidental data loss
- **Case-sensitive confirmation**: Reduces typo-related accidents
- **Clear warnings**: Explicit information about irreversible actions
- **Graceful error handling**: No crashes on invalid input

## Performance

- **Efficient database operations**: Optimized queries
- **Batch price fetching**: Parallel ticker processing
- **Progress reporting**: Real-time feedback during operations
- **Timeout handling**: Graceful handling of slow network responses

## Integration with Existing Features

These new commands work seamlessly with existing portfolio functionality:

- **Analysis integration**: Updated portfolios work with existing analysis commands
- **History tracking**: All operations are logged for audit trails
- **Data consistency**: Sync ensures accurate price data for analysis
- **Backward compatibility**: Existing commands continue to work unchanged
