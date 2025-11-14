#!/usr/bin/env python3
"""
Stock Data Downloader
Downloads stock data for specified tickers and time periods using yfinance.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta
import argparse

# Initialize colorama for cross-platform colored output
try:
    import colorama
    colorama.init(autoreset=True)
    from colorama import Fore, Back, Style
    HAS_COLORAMA = True
except ImportError:
    # Fallback if colorama not available
    class Fore:
        GREEN = ''
        RED = ''
        YELLOW = ''
        BLUE = ''
        MAGENTA = ''
        CYAN = ''
        WHITE = ''
        BLACK = ''
    class Back:
        GREEN = ''
        RED = ''
        YELLOW = ''
        BLUE = ''
    class Style:
        BRIGHT = ''
        DIM = ''
        NORMAL = ''
    HAS_COLORAMA = False


class StockDownloader:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.ensure_data_directory()

    def ensure_data_directory(self):
        """Create data directory if it doesn't exist."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def download_stock_data(self, ticker, start_date, end_date, period=None):
        """
        Download stock data for a specific ticker.

        Args:
            ticker (str): Stock ticker symbol (e.g., 'PLTR', 'QBTS')
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            period (str): Alternative to start/end dates. Options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max

        Returns:
            pandas.DataFrame: Stock data
        """
        try:
            print(f"{Fore.BLUE}Downloading data for {ticker}...{Style.RESET_ALL}")

            if period:
                data = yf.download(ticker, period=period)
            else:
                data = yf.download(ticker, start=start_date, end=end_date)

            if data.empty:
                print(f"{Fore.YELLOW}Warning: No data found for ticker {ticker}{Style.RESET_ALL}")
                return None

            # Flatten MultiIndex columns if present (happens with single ticker downloads)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # Add ticker column for identification
            data['Ticker'] = ticker

            # Validate and clean data
            quality_issues = self.validate_data_quality(data, ticker)
            if quality_issues:
                print(f"⚠️  Data quality issues for {ticker}:")
                for issue in quality_issues:
                    print(f"   - {issue}")

            # Clean the data
            data = self.clean_data(data)

            print(f"Successfully downloaded {len(data)} records for {ticker}")
            return data

        except Exception as e:
            print(f"Error downloading data for {ticker}: {str(e)}")
            return None

    def save_to_csv(self, data, ticker, start_date=None, end_date=None):
        """Save stock data to CSV file."""
        if data is None or data.empty:
            print(f"No data to save for {ticker}")
            return None

        # Generate filename
        if start_date and end_date:
            filename = f"{ticker}_{start_date}_{end_date}.csv"
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"{ticker}_{today}.csv"

        filepath = os.path.join(self.data_dir, filename)

        try:
            data.to_csv(filepath)
            print(f"Data saved to: {filepath}")
            return filepath
        except Exception as e:
            print(f"Error saving data to {filepath}: {str(e)}")
            return None

    def get_available_files(self):
        """Get list of available CSV files."""
        if not os.path.exists(self.data_dir):
            return []

        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        return sorted(csv_files)

    def download_multiple_stocks(self, tickers, start_date, end_date=None, period=None):
        """
        Download data for multiple stock tickers.

        Args:
            tickers (list): List of ticker symbols
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            period (str): Period string (alternative to dates)

        Returns:
            dict: Dictionary of ticker -> filepath mappings
        """
        results = {}

        for ticker in tickers:
            data = self.download_stock_data(ticker, start_date, end_date, period)
            if data is not None:
                filepath = self.save_to_csv(data, ticker, start_date, end_date)
                results[ticker] = filepath

        return results

    def get_stock_info(self, ticker):
        """Get basic information about a stock."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            return {
                'symbol': info.get('symbol', ticker),
                'longName': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'marketCap': info.get('marketCap', 'N/A'),
                'currency': info.get('currency', 'N/A')
            }
        except Exception as e:
            print(f"Error getting info for {ticker}: {str(e)}")
            return None

    def validate_data_quality(self, data, ticker):
        """
        Validate data quality and completeness.

        Args:
            data (pd.DataFrame): Stock data to validate
            ticker (str): Ticker symbol for logging

        Returns:
            list: List of quality issues found
        """
        issues = []

        if data is None or data.empty:
            return ["No data to validate"]

        # Check for missing values
        missing_pct = (data.isnull().sum() / len(data)) * 100
        for col, pct in missing_pct.items():
            if pct > 5:  # More than 5% missing
                issues.append(f"{col}: {pct:.1f}% missing values")

        # Check for price anomalies (sudden large jumps that might be errors)
        if 'Close' in data.columns:
            price_changes = data['Close'].pct_change()
            large_moves = price_changes[price_changes.abs() > 0.5]  # 50% single-day move
            if len(large_moves) > 0:
                issues.append(f"Detected {len(large_moves)} suspicious price spike(s) >50%")

        # Check for zero or negative prices
        price_cols = ['Open', 'High', 'Low', 'Close']
        for col in price_cols:
            if col in data.columns:
                invalid_prices = (data[col] <= 0).sum()
                if invalid_prices > 0:
                    issues.append(f"{col}: {invalid_prices} invalid (zero/negative) prices")

        # Check for volume anomalies
        if 'Volume' in data.columns:
            zero_volume_count = (data['Volume'] == 0).sum()
            if zero_volume_count > len(data) * 0.1:  # More than 10% zero volume
                issues.append(f"Excessive zero-volume days: {zero_volume_count} ({zero_volume_count/len(data)*100:.1f}%)")

        # Check for date gaps (weekends excluded)
        if isinstance(data.index, pd.DatetimeIndex):
            expected_trading_days = pd.bdate_range(start=data.index.min(), end=data.index.max())
            actual_days = len(data)
            expected_days = len(expected_trading_days)

            if actual_days < expected_days * 0.7:  # Less than 70% of expected trading days
                missing_days = expected_days - actual_days
                issues.append(f"Significant date gaps: {missing_days} missing trading days ({missing_days/expected_days*100:.1f}%)")

        # Check for High < Low inconsistencies
        if 'High' in data.columns and 'Low' in data.columns:
            inconsistent = (data['High'] < data['Low']).sum()
            if inconsistent > 0:
                issues.append(f"Data inconsistency: {inconsistent} rows where High < Low")

        return issues

    def clean_data(self, data):
        """
        Clean and prepare data for analysis.

        Args:
            data (pd.DataFrame): Raw stock data

        Returns:
            pd.DataFrame: Cleaned data
        """
        if data is None or data.empty:
            return data

        data = data.copy()

        # Remove any completely duplicate rows
        data = data[~data.index.duplicated(keep='first')]

        # Forward fill small gaps (max 3 days) for price data
        price_cols = ['Open', 'High', 'Low', 'Close']
        for col in price_cols:
            if col in data.columns:
                data[col] = data[col].ffill(limit=3)

        # Remove rows with remaining NaN in critical columns
        critical_cols = [col for col in ['Open', 'High', 'Low', 'Close'] if col in data.columns]
        if critical_cols:
            data = data.dropna(subset=critical_cols)

        # Cap extreme outliers (returns beyond 3 std devs) - likely data errors
        if 'Close' in data.columns and len(data) > 30:
            returns = data['Close'].pct_change()
            mean_ret = returns.mean()
            std_ret = returns.std()

            # Identify outliers
            outlier_threshold = 3
            outliers = returns.abs() > (abs(mean_ret) + outlier_threshold * std_ret)

            if outliers.sum() > 0 and outliers.sum() < len(data) * 0.02:  # Less than 2% outliers
                # Replace outlier prices with interpolated values
                data.loc[outliers, 'Close'] = np.nan
                data['Close'] = data['Close'].interpolate(method='linear')

                # Also fix OHLC for outlier days
                for col in ['Open', 'High', 'Low']:
                    if col in data.columns:
                        data.loc[outliers, col] = data.loc[outliers, 'Close']

        # Ensure High >= Low
        if 'High' in data.columns and 'Low' in data.columns:
            inconsistent = data['High'] < data['Low']
            if inconsistent.sum() > 0:
                # Swap High and Low for inconsistent rows
                data.loc[inconsistent, ['High', 'Low']] = data.loc[inconsistent, ['Low', 'High']].values

        # Fill zero volumes with forward fill or median
        if 'Volume' in data.columns:
            zero_vol = data['Volume'] == 0
            if zero_vol.sum() > 0:
                median_vol = data.loc[data['Volume'] > 0, 'Volume'].median()
                data.loc[zero_vol, 'Volume'] = median_vol

        return data


def main():
    parser = argparse.ArgumentParser(description='Download stock data using yfinance')
    parser.add_argument('tickers', nargs='+', help='Stock ticker symbols (e.g., PLTR QBTS AAPL)')
    parser.add_argument('--start', '-s', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', '-e', help='End date (YYYY-MM-DD)')
    parser.add_argument('--period', '-p', help='Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)')
    parser.add_argument('--info', '-i', action='store_true', help='Show stock information')

    args = parser.parse_args()

    # Initialize downloader
    downloader = StockDownloader()

    # Show stock info if requested
    if args.info:
        for ticker in args.tickers:
            info = downloader.get_stock_info(ticker)
            if info:
                print(f"\n{Fore.CYAN}{ticker} - {info['longName']}{Style.RESET_ALL}")
                print(f"Sector: {info['sector']}")
                print(f"Industry: {info['industry']}")
                print(f"Market Cap: {info['marketCap']}")
                print(f"Currency: {info['currency']}")

    # Set default dates if not provided and no period specified
    if not args.period and not args.start:
        args.start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")  # 1 year ago

    if not args.period and not args.end:
        args.end = datetime.now().strftime("%Y-%m-%d")  # Today

    # Download data
    print(f"\n{Fore.GREEN}Downloading data for: {', '.join(args.tickers)}{Style.RESET_ALL}")

    if args.period:
        print(f"Period: {args.period}")
    else:
        print(f"Date range: {args.start} to {args.end}")

    results = downloader.download_multiple_stocks(
        args.tickers,
        args.start,
        args.end,
        args.period
    )

    print(f"\n{Fore.GREEN}Download completed. Files saved:{Style.RESET_ALL}")
    for ticker, filepath in results.items():
        if filepath:
            print(f"  {Fore.BLUE}{ticker}: {filepath}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
