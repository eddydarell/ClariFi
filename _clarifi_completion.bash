#!/bin/bash
# Bash completion script for ClariFi (core/main.py and run.sh)

_clarifi_completion() {
    local cur prev words cword
    _init_completion || return

    # Main commands
    local commands="quick analyze seasonal patterns correlations events volatility download visualize info list live screen portfolio"

    # Portfolio subcommands
    local portfolio_subcommands="create list add remove tickers analyze history accuracy"

    # Screen choices
    local screen_choices="gainers losers actives new"

    # Common options
    local common_options="--period -p --no-download --help -h"
    local period_values="1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max"

    case $cword in
        1)
            # First argument - main commands
            COMPREPLY=($(compgen -W "$commands" -- "$cur"))
            ;;
        2)
            case $prev in
                screen)
                    COMPREPLY=($(compgen -W "$screen_choices" -- "$cur"))
                    ;;
                portfolio)
                    COMPREPLY=($(compgen -W "$portfolio_subcommands" -- "$cur"))
                    ;;
                *)
                    # For other commands, complete with ticker symbols or common options
                    if [[ $cur == -* ]]; then
                        COMPREPLY=($(compgen -W "$common_options" -- "$cur"))
                    else
                        # Common ticker symbols for completion
                        local tickers="AAPL MSFT GOOGL GOOG AMZN TSLA NVDA META NFLX PYPL ADBE CRM ORCL INTC AMD UBER LYFT PLTR QBTS NIO SAAB"
                        COMPREPLY=($(compgen -W "$tickers" -- "$cur"))
                    fi
                    ;;
            esac
            ;;
        *)
            # For subsequent arguments
            if [[ $cur == -* ]]; then
                case ${words[1]} in
                    quick)
                        local quick_options="--period -p --no-download --no-visualize --help -h"
                        COMPREPLY=($(compgen -W "$quick_options" -- "$cur"))
                        ;;
                    analyze)
                        local analyze_options="--period -p --no-download --no-patterns --no-events --no-advanced-viz --no-options --no-investment-advice --no-seasonal --include-deep --deep-chunk-months --help -h"
                        COMPREPLY=($(compgen -W "$analyze_options" -- "$cur"))
                        ;;
                    seasonal)
                        local seasonal_options="--period -p --no-download --help -h"
                        COMPREPLY=($(compgen -W "$seasonal_options" -- "$cur"))
                        ;;
                    patterns|correlations)
                        local pattern_options="--period -p --window -w --help -h"
                        COMPREPLY=($(compgen -W "$pattern_options" -- "$cur"))
                        ;;
                    events)
                        local event_options="--period -p --lookback --lookahead --help -h"
                        COMPREPLY=($(compgen -W "$event_options" -- "$cur"))
                        ;;
                    volatility)
                        local vol_options="--period -p --window -w --clustering --help -h"
                        COMPREPLY=($(compgen -W "$vol_options" -- "$cur"))
                        ;;
                    download)
                        local download_options="--start -s --end -e --period -p --help -h"
                        COMPREPLY=($(compgen -W "$download_options" -- "$cur"))
                        ;;
                    visualize)
                        local viz_options="--single --compare --correlation --support-resistance --metric --show --help -h"
                        COMPREPLY=($(compgen -W "$viz_options" -- "$cur"))
                        ;;
                    live)
                        local live_options="--interval -i --no-graphs --no-summary --help -h"
                        COMPREPLY=($(compgen -W "$live_options" -- "$cur"))
                        ;;
                    screen)
                        local screen_options="--limit -l --export -e --help -h"
                        COMPREPLY=($(compgen -W "$screen_options" -- "$cur"))
                        ;;
                    portfolio)
                        case ${words[2]} in
                            create)
                                local p_create_options="--name -n --description -d --help -h"
                                COMPREPLY=($(compgen -W "$p_create_options" -- "$cur"))
                                ;;
                            add)
                                local p_add_options="--quantity -q --avg-cost -c --help -h"
                                COMPREPLY=($(compgen -W "$p_add_options" -- "$cur"))
                                ;;
                            analyze)
                                local p_analyze_options="--period -p --no-patterns --no-events --no-options --no-seasonal --summary-only --help -h"
                                COMPREPLY=($(compgen -W "$p_analyze_options" -- "$cur"))
                                ;;
                            history)
                                local p_history_options="--portfolio-id --ticker --limit -l --help -h"
                                COMPREPLY=($(compgen -W "$p_history_options" -- "$cur"))
                                ;;
                            accuracy)
                                local p_accuracy_options="--portfolio-id --ticker --help -h"
                                COMPREPLY=($(compgen -W "$p_accuracy_options" -- "$cur"))
                                ;;
                            *)
                                COMPREPLY=($(compgen -W "--help -h" -- "$cur"))
                                ;;
                        esac
                        ;;
                    *)
                        COMPREPLY=($(compgen -W "$common_options" -- "$cur"))
                        ;;
                esac
            elif [[ $prev == "--period" || $prev == "-p" ]]; then
                COMPREPLY=($(compgen -W "$period_values" -- "$cur"))
            elif [[ $prev == "--metric" ]]; then
                local metrics="Close High Low Open Volume"
                COMPREPLY=($(compgen -W "$metrics" -- "$cur"))
            else
                # Complete with ticker symbols for additional arguments
                local tickers="AAPL MSFT GOOGL GOOG AMZN TSLA NVDA META NFLX PYPL ADBE CRM ORCL INTC AMD UBER LYFT PLTR QBTS NIO"
                COMPREPLY=($(compgen -W "$tickers" -- "$cur"))
            fi
            ;;
    esac
}

# Register completion for both python script and run.sh
complete -F _clarifi_completion python3
complete -F _clarifi_completion python
complete -F _clarifi_completion ./run.sh
complete -F _clarifi_completion run.sh

# Also register for direct python execution of main.py
_clarifi_python_completion() {
    local cur prev words cword
    _init_completion || return

    # Check if we're calling core/main.py
    if [[ "${words[1]}" == *"main.py" ]] || [[ "${words[1]}" == *"core/main.py" ]]; then
        # Shift the words array to remove python and main.py
        local shifted_words=("${words[@]:2}")
        local shifted_cword=$((cword - 1))

        # Call the main completion function with adjusted parameters
        words=("clarifi" "${shifted_words[@]}")
        cword=$shifted_cword
        _clarifi_completion
    fi
}

complete -F _clarifi_python_completion python3
complete -F _clarifi_python_completion python
