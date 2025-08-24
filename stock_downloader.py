#!/usr/bin/env python3
"""
Stock Data Downloader
Downloads stock data for specified tickers and time periods using yfinance.
"""

import yfinance as yf
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
import argparse


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
            print(f"Downloading data for {ticker}...")

            if period:
                data = yf.download(ticker, period=period)
            else:
                data = yf.download(ticker, start=start_date, end=end_date)

            if data.empty:
                print(f"Warning: No data found for ticker {ticker}")
                return None

            # Add ticker column for identification
            data['Ticker'] = ticker

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
                print(f"\n{ticker} - {info['longName']}")
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
    print(f"\nDownloading data for: {', '.join(args.tickers)}")

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

    print(f"\nDownload completed. Files saved:")
    for ticker, filepath in results.items():
        if filepath:
            print(f"  {ticker}: {filepath}")


if __name__ == "__main__":
    main()
