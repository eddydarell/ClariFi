# ClariFi Tab Completion

This directory contains tab completion scripts for ClariFi commands, making it easier to use the financial analysis tool with auto-completion support.

## Quick Setup

### Automatic Installation

1. **Install for your current shell:**
   ```bash
   ./setup_completion.sh --install
   ```

2. **Install for all shells (bash and zsh):**
   ```bash
   ./setup_completion.sh --all
   ```

3. **Activate in current session:**
   ```bash
   # For zsh
   source ~/.zshrc

   # For bash
   source ~/.bashrc
   ```

### Manual Installation

#### For Zsh (recommended for macOS)

1. Copy the completion file:
   ```bash
   mkdir -p ~/.local/share/zsh/site-functions
   cp _clarifi_completion.zsh ~/.local/share/zsh/site-functions/_clarifi
   ```

2. Add to your `~/.zshrc`:
   ```bash
   echo 'fpath=(~/.local/share/zsh/site-functions $fpath)' >> ~/.zshrc
   echo 'autoload -U compinit && compinit' >> ~/.zshrc
   ```

3. Reload your shell:
   ```bash
   source ~/.zshrc
   ```

#### For Bash

1. Copy the completion file:
   ```bash
   mkdir -p ~/.local/share/bash-completion/completions
   cp _clarifi_completion.bash ~/.local/share/bash-completion/completions/clarifi
   ```

2. Add to your `~/.bashrc`:
   ```bash
   echo 'source ~/.local/share/bash-completion/completions/clarifi' >> ~/.bashrc
   ```

3. Reload your shell:
   ```bash
   source ~/.bashrc
   ```

## Features

### Main Commands Completion
Type `./run.sh ` and press TAB to see all available commands:
- `quick` - Quick basic analysis
- `analyze` - Comprehensive market analysis
- `seasonal` - Seasonal & holiday analysis
- `patterns` - Advanced pattern analysis
- `correlations` - Correlation analysis
- `events` - Event correlation analysis
- `volatility` - Volatility clustering analysis
- `download` - Download stock data
- `visualize` - Create visualizations
- `info` - Show stock information
- `list` - List available data files
- `live` - Live real-time monitoring
- `screen` - Market screening
- `portfolio` - Portfolio management

### Command-Specific Completion

#### Analyze Command
```bash
./run.sh analyze [TAB]
# Completes with:
# - Ticker symbols (AAPL, MSFT, GOOGL, etc.)
# - Options: --period, --no-download, --no-patterns, etc.
```

#### Portfolio Subcommands
```bash
./run.sh portfolio [TAB]
# Completes with: create, list, add, remove, tickers, analyze, history, accuracy
```

#### Screen Categories
```bash
./run.sh screen [TAB]
# Completes with: gainers, losers, actives, new
```

#### Period Values
```bash
./run.sh analyze AAPL --period [TAB]
# Completes with: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
```

#### Ticker Symbols
Common ticker symbols are provided for completion:
- Tech: AAPL, MSFT, GOOGL, GOOG, AMZN, TSLA, NVDA, META
- Others: PLTR, QBTS, NIO, SAAB, NFLX, PYPL, ADBE, CRM, etc.

### Completion for Python Script

Tab completion also works when calling the Python script directly:
```bash
python3 core/main.py [TAB]
# Same completion as ./run.sh
```

## Examples

### Basic Usage
```bash
./run.sh ana[TAB]           # → ./run.sh analyze
./run.sh analyze --pe[TAB]  # → ./run.sh analyze --period
./run.sh screen [TAB]       # Shows: gainers losers actives new
```

### Advanced Usage
```bash
./run.sh portfolio [TAB]              # Shows portfolio subcommands
./run.sh portfolio create --na[TAB]   # → --name
./run.sh analyze AAPL --no-[TAB]      # Shows all --no-* options
```

## Testing

Test your completion setup:
```bash
./test_completion.sh
```

Or manually test:
1. Type `./run.sh ` and press TAB twice - should show all commands
2. Type `./run.sh ana` and press TAB - should complete to `analyze`
3. Type `./run.sh analyze --pe` and press TAB - should complete to `--period`

## Troubleshooting

### Completion Not Working

1. **Check if completion is loaded:**
   ```bash
   # For zsh
   compdef -d clarifi

   # For bash
   complete -p | grep clarifi
   ```

2. **Reload shell configuration:**
   ```bash
   # For zsh
   source ~/.zshrc

   # For bash
   source ~/.bashrc
   ```

3. **Re-run setup:**
   ```bash
   ./setup_completion.sh --install
   ```

### Remove Completion

To remove tab completion:
```bash
./setup_completion.sh --remove
```

## Files

- `_clarifi_completion.bash` - Bash completion script
- `_clarifi_completion.zsh` - Zsh completion script
- `setup_completion.sh` - Automatic setup script
- `test_completion.sh` - Test completion functionality
- `COMPLETION_README.md` - This documentation

## Supported Shells

- ✅ Zsh (macOS default)
- ✅ Bash 4.0+
- ❌ Fish (not currently supported)
- ❌ PowerShell (not currently supported)

For other shells, you may need to adapt the completion scripts manually.
