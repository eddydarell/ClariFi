#compdef clarifi run.sh python3 python

# Zsh completion script for ClariFi (core/main.py and run.sh)

_clarifi() {
    local context state line
    typeset -A opt_args

    # Check if we're calling the python script directly
    local is_python_call=0
    if [[ "$words[1]" == "python"* ]] && [[ "$words[2]" == *"main.py" ]]; then
        is_python_call=1
        # Shift the words to remove python and main.py
        shift words
        shift words
        (( CURRENT -= 2 ))
    fi

    _arguments -C \
        '1: :_clarifi_commands' \
        '*:: :->args'

    case $state in
        args)
            case $words[1] in
                quick)
                    _arguments \
                        '*:ticker symbols:_clarifi_tickers' \
                        '--period[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '-p[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '--no-download[Skip downloading]' \
                        '--no-visualize[Skip visualization]' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                analyze)
                    _arguments \
                        '*:ticker symbols:_clarifi_tickers' \
                        '--period[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '-p[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '--no-download[Skip downloading fresh data]' \
                        '--no-patterns[Skip pattern analysis]' \
                        '--no-events[Skip event correlation]' \
                        '--no-advanced-viz[Skip advanced visualizations]' \
                        '--no-options[Skip Black-Scholes options analysis]' \
                        '--no-investment-advice[Skip investment suggestions]' \
                        '--no-seasonal[Skip seasonal analysis]' \
                        '--include-deep[Include deep backtesting analysis]' \
                        '--deep-chunk-months[Chunk size in months]:months:' \
                        '--ai[Output condensed signal data (JSON) for an AI trading bot]' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                seasonal)
                    _arguments \
                        '*:ticker symbols:_clarifi_tickers' \
                        '--period[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '-p[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '--no-download[Skip downloading fresh data]' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                patterns|correlations)
                    _arguments \
                        '*:ticker symbols:_clarifi_tickers' \
                        '--period[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '-p[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '--window[Rolling window size]:window:' \
                        '-w[Rolling window size]:window:' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                events)
                    _arguments \
                        '*:ticker symbols:_clarifi_tickers' \
                        '--period[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '-p[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '--lookback[Days before event]:days:' \
                        '--lookahead[Days after event]:days:' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                volatility)
                    _arguments \
                        '*:ticker symbols:_clarifi_tickers' \
                        '--period[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '-p[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '--window[Volatility window]:window:' \
                        '-w[Volatility window]:window:' \
                        '--clustering[Create clustering plots]' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                download)
                    _arguments \
                        '*:ticker symbols:_clarifi_tickers' \
                        '--start[Start date (YYYY-MM-DD)]:date:' \
                        '-s[Start date (YYYY-MM-DD)]:date:' \
                        '--end[End date (YYYY-MM-DD)]:date:' \
                        '-e[End date (YYYY-MM-DD)]:date:' \
                        '--period[Period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '-p[Period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                visualize)
                    _arguments \
                        '*:ticker symbols:_clarifi_tickers' \
                        '--single[Individual charts only]' \
                        '--compare[Comparison chart]' \
                        '--correlation[Correlation matrix]' \
                        '--support-resistance[Support/resistance levels]' \
                        '--metric[Metric to plot]:metric:(Close High Low Open Volume)' \
                        '--show[Show plots instead of saving]' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                info)
                    _arguments \
                        '*:ticker symbols:_clarifi_tickers' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                list)
                    _arguments \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                live)
                    _arguments \
                        '*:ticker symbols:_clarifi_tickers' \
                        '--interval[Update interval in seconds]:seconds:' \
                        '-i[Update interval in seconds]:seconds:' \
                        '--no-graphs[Disable terminal graphs]' \
                        '--no-summary[Disable summary table]' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                screen)
                    _arguments \
                        '1:category:(gainers losers actives new)' \
                        '--limit[Number of results]:limit:' \
                        '-l[Number of results]:limit:' \
                        '--export[Export to CSV file]:file:_files' \
                        '-e[Export to CSV file]:file:_files' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                portfolio)
                    _clarifi_portfolio_commands
                    ;;
            esac
            ;;
    esac
}

_clarifi_commands() {
    local commands
    commands=(
        'quick:Quick basic analysis (legacy)'
        'analyze:Comprehensive market analysis'
        'seasonal:Seasonal & holiday analysis'
        'patterns:Advanced pattern analysis'
        'correlations:Correlation analysis'
        'events:Event correlation analysis'
        'volatility:Volatility clustering analysis'
        'download:Download stock data'
        'visualize:Create visualizations'
        'info:Show stock information'
        'list:List available data files'
        'live:Live real-time stock monitoring'
        'screen:Market screening for gainers, losers, and new listings'
        'portfolio:Portfolio management commands'
    )
    _describe 'command' commands
}

_clarifi_portfolio_commands() {
    local context state line
    _arguments -C \
        '1: :_clarifi_portfolio_subcommands' \
        '*:: :->portfolio_args'

    case $state in
        portfolio_args)
            case $words[1] in
                create)
                    _arguments \
                        '--name[Portfolio name]:name:' \
                        '-n[Portfolio name]:name:' \
                        '--description[Portfolio description]:description:' \
                        '-d[Portfolio description]:description:' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                list)
                    _arguments \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                add)
                    _arguments \
                        '1:portfolio_id:' \
                        '2:ticker symbol:_clarifi_tickers' \
                        '--quantity[Quantity]:quantity:' \
                        '-q[Quantity]:quantity:' \
                        '--avg-cost[Average cost]:cost:' \
                        '-c[Average cost]:cost:' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                remove)
                    _arguments \
                        '1:portfolio_id:' \
                        '2:ticker symbol:_clarifi_tickers' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                tickers)
                    _arguments \
                        '1:portfolio_id:' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                analyze)
                    _arguments \
                        '1:portfolio_id:' \
                        '--period[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '-p[Time period]:period:(1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max)' \
                        '--no-patterns[Skip pattern analysis]' \
                        '--no-events[Skip event correlation]' \
                        '--no-options[Skip options analysis]' \
                        '--no-seasonal[Skip seasonal analysis]' \
                        '--summary-only[Print only summary recommendations]' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                history)
                    _arguments \
                        '--portfolio-id[Portfolio ID]:portfolio_id:' \
                        '--ticker[Ticker symbol]:ticker:_clarifi_tickers' \
                        '--limit[Number of records]:limit:' \
                        '-l[Number of records]:limit:' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
                accuracy)
                    _arguments \
                        '--portfolio-id[Portfolio ID]:portfolio_id:' \
                        '--ticker[Ticker symbol]:ticker:_clarifi_tickers' \
                        '--help[Show help]' \
                        '-h[Show help]'
                    ;;
            esac
            ;;
    esac
}

_clarifi_portfolio_subcommands() {
    local subcommands
    subcommands=(
        'create:Create a new portfolio'
        'list:List all portfolios'
        'add:Add a ticker to a portfolio'
        'remove:Remove a ticker from a portfolio'
        'tickers:List tickers in a portfolio'
        'analyze:Run comprehensive analysis on portfolio tickers'
        'history:Show recent analysis history'
        'accuracy:Show accuracy trends for predictions'
    )
    _describe 'portfolio command' subcommands
}

_clarifi_tickers() {
    local tickers
    tickers=(
        'AAPL:Apple Inc.'
        'MSFT:Microsoft Corporation'
        'GOOGL:Alphabet Inc. Class A'
        'GOOG:Alphabet Inc. Class C'
        'AMZN:Amazon.com Inc.'
        'TSLA:Tesla Inc.'
        'NVDA:NVIDIA Corporation'
        'META:Meta Platforms Inc.'
        'NFLX:Netflix Inc.'
        'PYPL:PayPal Holdings Inc.'
        'ADBE:Adobe Inc.'
        'CRM:Salesforce Inc.'
        'ORCL:Oracle Corporation'
        'INTC:Intel Corporation'
        'AMD:Advanced Micro Devices Inc.'
        'UBER:Uber Technologies Inc.'
        'LYFT:Lyft Inc.'
        'PLTR:Palantir Technologies Inc.'
        'QBTS:D-Wave Quantum Inc.'
        'NIO:NIO Inc.'
        'SAAB:Saab AB'
    )
    _describe 'ticker symbol' tickers
}

# Handle different calling contexts
case "$service" in
    python3|python)
        # Check if calling clarifi main.py
        if [[ "$words[2]" == *"main.py" ]] || [[ "$words[2]" == *"core/main.py" ]]; then
            shift words
            shift words
            (( CURRENT -= 2 ))
            _clarifi "$@"
        fi
        ;;
    run.sh|./run.sh)
        _clarifi "$@"
        ;;
    clarifi)
        _clarifi "$@"
        ;;
esac
