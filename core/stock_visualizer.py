#!/usr/bin/env python3
"""
Stock Data Visualizer
Creates charts and graphs for stock data analysis.
Supports individual stock charts and comparison charts.
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import os
import argparse
from datetime import datetime
import glob


class StockVisualizer:
    def __init__(self, data_dir="data", output_dir="graphs"):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.ensure_output_directory()

        # Set style for better-looking plots
        plt.style.use('default')
        try:
            sns.set_palette("husl")
        except:
            pass  # Fallback if seaborn style fails

    def ensure_output_directory(self):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def load_stock_data(self, filepath):
        """Load stock data from CSV file."""
        try:
            # Read the CSV file and handle the multi-level column structure
            data = pd.read_csv(filepath, skiprows=[1, 2], index_col=0, parse_dates=True)

            # Clean up column names (remove multi-level if present)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # Ensure we have the required columns
            required_columns = ['Close', 'High', 'Low', 'Open', 'Volume']
            for col in required_columns:
                if col not in data.columns:
                    print(f"Warning: Column {col} not found in {filepath}")
                    return None

            return data
        except Exception as e:
            print(f"Error loading data from {filepath}: {str(e)}")
            return None

    def find_stock_files(self, ticker=None):
        """Find CSV files for specific ticker or all tickers."""
        if ticker:
            pattern = os.path.join(self.data_dir, f"{ticker}_*.csv")
        else:
            pattern = os.path.join(self.data_dir, "*.csv")

        files = glob.glob(pattern)
        return files

    def extract_ticker_from_filename(self, filepath):
        """Extract ticker symbol from filename."""
        filename = os.path.basename(filepath)
        return filename.split('_')[0]

    def plot_single_stock(self, ticker, save=True, show=False):
        """Create a comprehensive chart for a single stock."""
        files = self.find_stock_files(ticker)

        if not files:
            print(f"No data files found for ticker: {ticker}")
            return None

        # Use the most recent file
        latest_file = max(files, key=os.path.getctime)
        data = self.load_stock_data(latest_file)

        if data is None:
            return None

        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'{ticker} Stock Analysis', fontsize=16, fontweight='bold')

        # 1. Price chart with volume
        ax1 = axes[0, 0]
        ax1.plot(data.index, data['Close'], label='Close Price', linewidth=2)
        ax1.plot(data.index, data['Open'], label='Open Price', alpha=0.7)
        ax1.set_title(f'{ticker} - Price Chart')
        ax1.set_ylabel('Price ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Volume chart
        ax2 = axes[0, 1]
        ax2.bar(data.index, data['Volume'], alpha=0.7, color='orange')
        ax2.set_title(f'{ticker} - Volume')
        ax2.set_ylabel('Volume')
        ax2.grid(True, alpha=0.3)

        # 3. Candlestick-style high/low chart
        ax3 = axes[1, 0]
        ax3.fill_between(data.index, data['Low'], data['High'], alpha=0.3, label='High-Low Range')
        ax3.plot(data.index, data['Close'], label='Close Price', linewidth=2)
        ax3.set_title(f'{ticker} - High/Low Range')
        ax3.set_ylabel('Price ($)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. Daily returns
        ax4 = axes[1, 1]
        data['Daily_Return'] = data['Close'].pct_change() * 100
        ax4.plot(data.index, data['Daily_Return'], alpha=0.7, color='green')
        ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax4.set_title(f'{ticker} - Daily Returns (%)')
        ax4.set_ylabel('Return (%)')
        ax4.grid(True, alpha=0.3)

        # Format x-axes
        for ax in axes.flat:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        if save:
            filename = f"{ticker}_analysis_{datetime.now().strftime('%Y%m%d')}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Chart saved: {filepath}")

        if show:
            plt.show()
        else:
            plt.close()

        return filepath if save else None

    def plot_comparison(self, tickers, metric='Close', save=True, show=False):
        """Create comparison chart for multiple stocks."""
        stock_data = {}

        # Load data for each ticker
        for ticker in tickers:
            files = self.find_stock_files(ticker)
            if files:
                latest_file = max(files, key=os.path.getctime)
                data = self.load_stock_data(latest_file)
                if data is not None:
                    stock_data[ticker] = data

        if not stock_data:
            print("No data found for any of the specified tickers")
            return None

        # Create comparison plots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Stock Comparison: {", ".join(tickers)}', fontsize=16, fontweight='bold')

        # 1. Price comparison (normalized)
        ax1 = axes[0, 0]
        for ticker, data in stock_data.items():
            normalized_price = (data[metric] / data[metric].iloc[0]) * 100
            ax1.plot(data.index, normalized_price, label=ticker, linewidth=2)
        ax1.set_title(f'{metric} Price Comparison (Normalized to 100)')
        ax1.set_ylabel('Normalized Price')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Absolute price comparison
        ax2 = axes[0, 1]
        for ticker, data in stock_data.items():
            ax2.plot(data.index, data[metric], label=ticker, linewidth=2)
        ax2.set_title(f'{metric} Price Comparison (Absolute)')
        ax2.set_ylabel('Price ($)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. Volume comparison
        ax3 = axes[1, 0]
        for ticker, data in stock_data.items():
            ax3.plot(data.index, data['Volume'], label=ticker, alpha=0.7)
        ax3.set_title('Volume Comparison')
        ax3.set_ylabel('Volume')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. Daily returns comparison
        ax4 = axes[1, 1]
        for ticker, data in stock_data.items():
            daily_returns = data['Close'].pct_change() * 100
            ax4.plot(data.index, daily_returns, label=ticker, alpha=0.7)
        ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax4.set_title('Daily Returns Comparison (%)')
        ax4.set_ylabel('Return (%)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        # Format x-axes
        for ax in axes.flat:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        if save:
            filename = f"comparison_{'_'.join(tickers)}_{datetime.now().strftime('%Y%m%d')}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Comparison chart saved: {filepath}")

        if show:
            plt.show()
        else:
            plt.close()

        return filepath if save else None

    def create_correlation_matrix(self, tickers, save=True, show=False):
        """Create correlation matrix for multiple stocks."""
        stock_data = {}

        # Load closing prices for each ticker
        for ticker in tickers:
            files = self.find_stock_files(ticker)
            if files:
                latest_file = max(files, key=os.path.getctime)
                data = self.load_stock_data(latest_file)
                if data is not None:
                    stock_data[ticker] = data['Close']

        if len(stock_data) < 2:
            print("Need at least 2 stocks for correlation analysis")
            return None

        # Create DataFrame with all closing prices
        df = pd.DataFrame(stock_data)

        # Calculate correlation matrix
        correlation_matrix = df.corr()

        # Create heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": .8})
        plt.title(f'Stock Price Correlation Matrix\n{", ".join(tickers)}', fontsize=14, fontweight='bold')
        plt.tight_layout()

        if save:
            filename = f"correlation_{'_'.join(tickers)}_{datetime.now().strftime('%Y%m%d')}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Correlation matrix saved: {filepath}")

        if show:
            plt.show()
        else:
            plt.close()

        return filepath if save else None


def main():
    parser = argparse.ArgumentParser(description='Visualize stock data')
    parser.add_argument('--tickers', '-t', nargs='+', help='Stock ticker symbols')
    parser.add_argument('--single', '-s', help='Create individual chart for single ticker')
    parser.add_argument('--compare', '-c', nargs='+', help='Compare multiple tickers')
    parser.add_argument('--correlation', '-r', nargs='+', help='Create correlation matrix')
    parser.add_argument('--metric', '-m', default='Close', help='Metric to plot (Close, Open, High, Low)')
    parser.add_argument('--show', action='store_true', help='Show plots instead of saving')
    parser.add_argument('--list', '-l', action='store_true', help='List available data files')

    args = parser.parse_args()

    visualizer = StockVisualizer()

    if args.list:
        files = visualizer.find_stock_files()
        if files:
            print("Available data files:")
            for file in files:
                ticker = visualizer.extract_ticker_from_filename(file)
                print(f"  {ticker}: {os.path.basename(file)}")
        else:
            print("No data files found in the data directory")
        return

    if args.single:
        visualizer.plot_single_stock(args.single, save=not args.show, show=args.show)

    if args.compare:
        visualizer.plot_comparison(args.compare, args.metric, save=not args.show, show=args.show)

    if args.correlation:
        visualizer.create_correlation_matrix(args.correlation, save=not args.show, show=args.show)

    if not any([args.single, args.compare, args.correlation, args.list]):
        print("Please specify an action: --single, --compare, --correlation, or --list")
        print("Use --help for more information")


if __name__ == "__main__":
    main()
