#!/usr/bin/env python3
"""
Live Stock Monitor
Real-time streaming stock data with terminal visualization
"""

import asyncio
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

try:
    import yfinance as yf
    import matplotlib.pyplot as plt
    import numpy as np
    from colorama import Fore, Back, Style, init
    import plotext as plt_terminal
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Install missing packages:")
    print("pip install yfinance matplotlib numpy colorama plotext")
    sys.exit(1)

# Initialize colorama for cross-platform color support
init(autoreset=True)


class LiveStockMonitor:
    """Real-time stock monitoring with terminal visualization"""

    def __init__(self):
        self.tickers: List[str] = []
        self.current_prices: Dict[str, float] = {}
        self.previous_prices: Dict[str, float] = {}
        self.price_history: Dict[str, List[Tuple[datetime, float]]] = {}
        self.start_time = datetime.now()
        self.update_interval = 5  # seconds
        self.max_history_points = 100
        self.running = False

    def add_ticker(self, ticker: str):
        """Add a ticker to monitor"""
        ticker = ticker.upper()
        if ticker not in self.tickers:
            self.tickers.append(ticker)
            self.current_prices[ticker] = 0.0
            self.previous_prices[ticker] = 0.0
            self.price_history[ticker] = []

    def add_tickers(self, tickers: List[str]):
        """Add multiple tickers to monitor"""
        for ticker in tickers:
            self.add_ticker(ticker)

    def get_real_time_price(self, ticker: str) -> Optional[float]:
        """Get real-time price for a ticker using yfinance"""
        try:
            stock = yf.Ticker(ticker)
            # Get the most recent price from 1-minute data
            data = stock.history(period="1d", interval="1m")
            if not data.empty:
                return float(data['Close'].iloc[-1])
            else:
                # Fallback to regular info
                info = stock.info
                return float(info.get('regularMarketPrice', 0.0))
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            return None

    def format_price_change(self, ticker: str, current_price: float, previous_price: float) -> str:
        """Format price with color coding based on change"""
        if previous_price == 0:
            color = Fore.WHITE
            arrow = "●"
            change_text = "NEW"
        elif current_price > previous_price:
            color = Fore.GREEN
            arrow = "▲"
            change = current_price - previous_price
            change_pct = (change / previous_price) * 100
            change_text = f"+{change:.2f} (+{change_pct:.1f}%)"
        elif current_price < previous_price:
            color = Fore.RED
            arrow = "▼"
            change = previous_price - current_price
            change_pct = (change / previous_price) * 100
            change_text = f"-{change:.2f} (-{change_pct:.1f}%)"
        else:
            color = Fore.YELLOW
            arrow = "●"
            change_text = "UNCHANGED"

        timestamp = datetime.now().strftime("%H:%M:%S")
        return f"{color}{arrow} {ticker:6} ${current_price:8.2f} {change_text:15} [{timestamp}]{Style.RESET_ALL}"

    def update_prices(self):
        """Update prices for all monitored tickers"""
        print(f"{Fore.CYAN}📡 Fetching real-time data...{Style.RESET_ALL}")

        for ticker in self.tickers:
            price = self.get_real_time_price(ticker)
            if price is not None:
                # Store previous price
                self.previous_prices[ticker] = self.current_prices[ticker]
                self.current_prices[ticker] = price

                # Add to history
                now = datetime.now()
                self.price_history[ticker].append((now, price))

                # Limit history size
                if len(self.price_history[ticker]) > self.max_history_points:
                    self.price_history[ticker] = self.price_history[ticker][-self.max_history_points:]

                # Display the price update
                print(self.format_price_change(ticker, price, self.previous_prices[ticker]))

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_header(self):
        """Display monitoring header"""
        runtime = datetime.now() - self.start_time
        runtime_str = str(runtime).split('.')[0]  # Remove microseconds

        print(f"{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}🚀 ClariFi Live Monitor - Real-time Stock Tracking{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 Monitoring: {', '.join(self.tickers)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}⏱️  Runtime: {runtime_str} | Update interval: {self.update_interval}s{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}")
        print()

    def display_terminal_graph(self, ticker: str):
        """Display a simple terminal-based graph for a ticker"""
        if ticker not in self.price_history or len(self.price_history[ticker]) < 2:
            return

        history = self.price_history[ticker]
        times = [entry[0] for entry in history]
        prices = [entry[1] for entry in history]

        # Use plotext for terminal plotting
        plt_terminal.clear_figure()
        plt_terminal.plot_size(60, 15)
        plt_terminal.title(f"{ticker} Price Chart (Last {len(prices)} points)")

        # Convert times to relative minutes
        start_time = times[0] if times else datetime.now()
        time_points = [(t - start_time).total_seconds() / 60 for t in times]

        plt_terminal.plot(time_points, prices, marker="braille")
        plt_terminal.xlabel("Minutes ago")
        plt_terminal.ylabel("Price ($)")

        # Add some basic stats
        if len(prices) >= 2:
            min_price = min(prices)
            max_price = max(prices)
            current_price = prices[-1]
            start_price = prices[0]
            change = current_price - start_price
            change_pct = (change / start_price) * 100 if start_price > 0 else 0

            plt_terminal.text(f"Range: ${min_price:.2f} - ${max_price:.2f}", 5, 13)
            plt_terminal.text(f"Change: {change:+.2f} ({change_pct:+.1f}%)", 5, 12)

        plt_terminal.show()
        print()

    def display_summary_table(self):
        """Display a summary table of all monitored stocks"""
        if not self.tickers:
            return

        print(f"{Fore.YELLOW}📋 CURRENT POSITIONS SUMMARY{Style.RESET_ALL}")
        print("┌─────────┬──────────┬──────────┬─────────────────┬─────────────┐")
        print("│ Ticker  │ Current  │ Previous │ Change          │ Trend       │")
        print("├─────────┼──────────┼──────────┼─────────────────┼─────────────┤")

        for ticker in self.tickers:
            current = self.current_prices.get(ticker, 0.0)
            previous = self.previous_prices.get(ticker, 0.0)

            if previous > 0:
                change = current - previous
                change_pct = (change / previous) * 100
                change_str = f"{change:+.2f} ({change_pct:+.1f}%)"

                if change > 0:
                    trend = f"{Fore.GREEN}▲ UP{Style.RESET_ALL}"
                elif change < 0:
                    trend = f"{Fore.RED}▼ DOWN{Style.RESET_ALL}"
                else:
                    trend = f"{Fore.YELLOW}● FLAT{Style.RESET_ALL}"
            else:
                change_str = "NEW"
                trend = f"{Fore.WHITE}● NEW{Style.RESET_ALL}"

            print(f"│ {ticker:7} │ ${current:7.2f} │ ${previous:7.2f} │ {change_str:15} │ {trend:11} │")

        print("└─────────┴──────────┴──────────┴─────────────────┴─────────────┘")
        print()

    def display_performance_metrics(self):
        """Display session performance metrics"""
        if not self.price_history:
            return

        print(f"{Fore.CYAN}📊 SESSION PERFORMANCE{Style.RESET_ALL}")

        session_stats = []
        for ticker in self.tickers:
            if ticker in self.price_history and len(self.price_history[ticker]) >= 2:
                history = self.price_history[ticker]
                start_price = history[0][1]
                current_price = history[-1][1]
                session_change = current_price - start_price
                session_change_pct = (session_change / start_price) * 100 if start_price > 0 else 0

                prices = [entry[1] for entry in history]
                session_high = max(prices)
                session_low = min(prices)
                volatility = np.std(prices) if len(prices) > 1 else 0

                session_stats.append({
                    'ticker': ticker,
                    'session_change': session_change,
                    'session_change_pct': session_change_pct,
                    'session_high': session_high,
                    'session_low': session_low,
                    'volatility': volatility
                })

        if session_stats:
            print("┌─────────┬─────────────────┬──────────┬──────────┬────────────┐")
            print("│ Ticker  │ Session Change  │ High     │ Low      │ Volatility │")
            print("├─────────┼─────────────────┼──────────┼──────────┼────────────┤")

            for stats in session_stats:
                change_color = Fore.GREEN if stats['session_change'] >= 0 else Fore.RED
                change_str = f"{change_color}{stats['session_change']:+.2f} ({stats['session_change_pct']:+.1f}%){Style.RESET_ALL}"

                print(f"│ {stats['ticker']:7} │ {change_str:15} │ ${stats['session_high']:7.2f} │ ${stats['session_low']:7.2f} │ ${stats['volatility']:9.2f} │")

            print("└─────────┴─────────────────┴──────────┴──────────┴────────────┘")
            print()

    async def monitor_async(self, show_graphs: bool = True, show_summary: bool = True):
        """Main monitoring loop (async version)"""
        self.running = True
        self.start_time = datetime.now()

        print(f"{Fore.GREEN}🚀 Starting live monitoring for {len(self.tickers)} tickers...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop monitoring{Style.RESET_ALL}")
        print()

        try:
            while self.running:
                self.clear_screen()
                self.display_header()

                # Update prices
                self.update_prices()
                print()

                if show_summary:
                    self.display_summary_table()

                self.display_performance_metrics()

                # Show terminal graphs for each ticker
                if show_graphs and self.price_history:
                    print(f"{Fore.YELLOW}📈 TERMINAL CHARTS{Style.RESET_ALL}")
                    for ticker in self.tickers:
                        if len(self.price_history.get(ticker, [])) >= 3:
                            self.display_terminal_graph(ticker)

                # Wait for next update
                print(f"{Fore.CYAN}Next update in {self.update_interval} seconds... (Ctrl+C to stop){Style.RESET_ALL}")
                await asyncio.sleep(self.update_interval)

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}🛑 Monitoring stopped by user{Style.RESET_ALL}")
            self.running = False
        except Exception as e:
            print(f"\n{Fore.RED}❌ Error during monitoring: {e}{Style.RESET_ALL}")
            self.running = False

    def monitor(self, show_graphs: bool = True, show_summary: bool = True):
        """Main monitoring loop (sync version)"""
        asyncio.run(self.monitor_async(show_graphs, show_summary))


def main():
    """CLI for live monitoring"""
    import argparse

    parser = argparse.ArgumentParser(description="Live Stock Monitor")
    parser.add_argument('tickers', nargs='+', help='Stock ticker symbols to monitor')
    parser.add_argument('--interval', '-i', type=int, default=5, help='Update interval in seconds (default: 5)')
    parser.add_argument('--no-graphs', action='store_true', help='Disable terminal graphs')
    parser.add_argument('--no-summary', action='store_true', help='Disable summary table')

    args = parser.parse_args()

    monitor = LiveStockMonitor()
    monitor.update_interval = args.interval
    monitor.add_tickers(args.tickers)

    monitor.monitor(
        show_graphs=not args.no_graphs,
        show_summary=not args.no_summary
    )


if __name__ == "__main__":
    main()
