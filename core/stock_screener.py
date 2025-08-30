#!/usr/bin/env python3
"""
Stock Screener Module
Market screening functionality for finding top gainers, losers, and new tickers
"""

import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

try:
    from colorama import Fore, Back, Style, init
except ImportError:
    # Fallback if colorama is not available
    class Fore:
        GREEN = ""
        RED = ""
        YELLOW = ""
        CYAN = ""
        MAGENTA = ""
        WHITE = ""
    class Style:
        RESET_ALL = ""
    def init():
        pass

# Initialize colorama for cross-platform color support
init(autoreset=True)


class StockScreener:
    """Stock market screener for finding gainers, losers, and new listings"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_market_movers(self, category: str = "gainers", limit: int = 20) -> List[Dict]:
        """
        Get market movers using yfinance data

        Args:
            category: "gainers", "losers", or "actives"
            limit: Number of results to return

        Returns:
            List of dictionaries with stock information
        """
        try:
            # Direct fallback to manual screening since yfinance Screener may not be available
            print(f"{Fore.YELLOW}Fetching market data using yfinance individual ticker approach...{Style.RESET_ALL}")
            return self._fallback_screening(category, limit)

        except Exception as e:
            print(f"Error fetching market movers: {e}")
            # Fallback to manual screening using popular tickers
            return self._fallback_screening(category, limit)

    def _fallback_screening(self, category: str, limit: int) -> List[Dict]:
        """Fallback screening method using a predefined list of popular tickers"""
        popular_tickers = [
            # Mega-cap stocks
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B',
            'UNH', 'JNJ', 'V', 'PG', 'HD', 'CVX', 'MA', 'PFE', 'ABBV', 'PEP',
            'KO', 'AVGO', 'TMO', 'COST', 'WMT', 'DHR', 'LIN', 'NEE', 'ACN',
            'TXN', 'HON', 'QCOM', 'UPS', 'LOW', 'T', 'IBM', 'MDT', 'AMD',
            # Additional growth and volatile stocks
            'NFLX', 'CRM', 'ADBE', 'PYPL', 'INTC', 'CMCSA', 'VZ', 'DIS',
            'CSCO', 'MRK', 'XOM', 'BAC', 'WFC', 'JPM', 'GS', 'MS',
            # Growth/tech stocks
            'PLTR', 'RBLX', 'COIN', 'HOOD', 'RIVN', 'LCID', 'U', 'SNOW',
            'ZM', 'DOCU', 'PTON', 'ROKU', 'SQ', 'SHOP', 'SPOT', 'UBER',
            'LYFT', 'TWTR', 'SNAP', 'PIN', 'DKNG', 'GME', 'AMC', 'BB',
            # Biotech and healthcare
            'MRNA', 'BNTX', 'GILD', 'BIIB', 'REGN', 'VRTX', 'ILMN', 'IQV',
            # Energy and utilities
            'COP', 'EOG', 'SLB', 'HAL', 'OXY', 'DVN', 'MPC', 'VLO',
            # Financial
            'BRK-A', 'C', 'AXP', 'SCHW', 'USB', 'TFC', 'PNC', 'COF'
        ]

        results = []
        print(f"{Fore.YELLOW}Screening {len(popular_tickers)} popular tickers for {category}...{Style.RESET_ALL}")

        processed_count = 0
        for ticker in popular_tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period="2d")

                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2]
                    change = current_price - previous_price
                    change_pct = (change / previous_price) * 100
                    volume = hist['Volume'].iloc[-1]

                    # Filter based on category with more lenient thresholds
                    if category == "gainers" and change_pct > 1.0:  # Lowered from 2.0%
                        results.append({
                            'symbol': ticker,
                            'shortName': info.get('shortName', ticker),
                            'regularMarketPrice': current_price,
                            'regularMarketChange': change,
                            'regularMarketChangePercent': change_pct,
                            'regularMarketVolume': volume,
                            'marketCap': info.get('marketCap', 0)
                        })
                    elif category == "losers" and change_pct < -1.0:  # Lowered from -2.0%
                        results.append({
                            'symbol': ticker,
                            'shortName': info.get('shortName', ticker),
                            'regularMarketPrice': current_price,
                            'regularMarketChange': change,
                            'regularMarketChangePercent': change_pct,
                            'regularMarketVolume': volume,
                            'marketCap': info.get('marketCap', 0)
                        })
                    elif category == "actives":
                        results.append({
                            'symbol': ticker,
                            'shortName': info.get('shortName', ticker),
                            'regularMarketPrice': current_price,
                            'regularMarketChange': change,
                            'regularMarketChangePercent': change_pct,
                            'regularMarketVolume': volume,
                            'marketCap': info.get('marketCap', 0)
                        })

                processed_count += 1
                if processed_count % 10 == 0:
                    print(f"{Fore.CYAN}  Processed {processed_count}/{len(popular_tickers)} tickers...{Style.RESET_ALL}")

                if len(results) >= limit * 2:  # Get more than needed to ensure good selection
                    break

            except Exception:
                continue

        print(f"{Fore.GREEN}  Completed screening. Found {len(results)} candidates.{Style.RESET_ALL}")

        # Sort results
        if category == "gainers":
            results.sort(key=lambda x: x.get('regularMarketChangePercent', 0), reverse=True)
        elif category == "losers":
            results.sort(key=lambda x: x.get('regularMarketChangePercent', 0))
        elif category == "actives":
            results.sort(key=lambda x: x.get('regularMarketVolume', 0), reverse=True)

        return results[:limit]

    def get_new_listings(self, days_back: int = 30, limit: int = 20) -> List[Dict]:
        """
        Get recently listed stocks (IPOs)
        This is a simplified version - in practice you'd use specialized APIs
        """
        print(f"{Fore.YELLOW}Searching for new listings in the past {days_back} days...{Style.RESET_ALL}")

        # Note: This is a simplified implementation
        # In practice, you'd use specialized APIs like:
        # - NASDAQ API for new listings
        # - SEC EDGAR API for new filings
        # - Financial data providers like Alpha Vantage, IEX Cloud, etc.

        # For now, we'll return some recently popular/trending tickers
        # that might represent newer or trending companies
        recent_trending = [
            {'symbol': 'RIVN', 'shortName': 'Rivian Automotive Inc', 'listingDate': '2021-11-10'},
            {'symbol': 'LCID', 'shortName': 'Lucid Group Inc', 'listingDate': '2021-07-26'},
            {'symbol': 'HOOD', 'shortName': 'Robinhood Markets Inc', 'listingDate': '2021-07-29'},
            {'symbol': 'COIN', 'shortName': 'Coinbase Global Inc', 'listingDate': '2021-04-14'},
            {'symbol': 'RBLX', 'shortName': 'Roblox Corporation', 'listingDate': '2021-03-10'},
            {'symbol': 'PLTR', 'shortName': 'Palantir Technologies Inc', 'listingDate': '2020-09-30'},
            {'symbol': 'SNOW', 'shortName': 'Snowflake Inc', 'listingDate': '2020-09-16'},
            {'symbol': 'U', 'shortName': 'Unity Software Inc', 'listingDate': '2020-09-18'},
            {'symbol': 'DKNG', 'shortName': 'DraftKings Inc', 'listingDate': '2020-04-24'},
            {'symbol': 'CRWD', 'shortName': 'CrowdStrike Holdings Inc', 'listingDate': '2019-06-12'},
        ]

        results = []
        for ticker_info in recent_trending[:limit]:
            try:
                ticker = ticker_info['symbol']
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period="2d")

                if len(hist) >= 1:
                    current_price = hist['Close'].iloc[-1]
                    volume = hist['Volume'].iloc[-1]

                    results.append({
                        'symbol': ticker,
                        'shortName': ticker_info['shortName'],
                        'regularMarketPrice': current_price,
                        'regularMarketVolume': volume,
                        'marketCap': info.get('marketCap', 0),
                        'listingDate': ticker_info['listingDate']
                    })
            except Exception:
                continue

        return results

    def format_screener_results(self, results: List[Dict], category: str) -> str:
        """Format screener results for display"""
        if not results:
            return f"{Fore.RED}No results found for {category}{Style.RESET_ALL}"

        # Header
        title_map = {
            'gainers': 'TOP GAINERS',
            'losers': 'TOP LOSERS',
            'actives': 'MOST ACTIVE',
            'new': 'NEW LISTINGS'
        }

        title = title_map.get(category, category.upper())
        output = [f"{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}"]
        output.append(f"{Fore.MAGENTA}📊 {title} - Market Screening Results{Style.RESET_ALL}")
        output.append(f"{Fore.CYAN}Found {len(results)} results{Style.RESET_ALL}")
        output.append(f"{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}")
        output.append("")

        # Table header
        if category == 'new':
            output.append("┌──────────┬─────────────────────────────────┬──────────────┬──────────────┬──────────────┐")
            output.append("│ Symbol   │ Company Name                    │ Price        │ Volume       │ Listing Date │")
            output.append("├──────────┼─────────────────────────────────┼──────────────┼──────────────┼──────────────┤")
        else:
            output.append("┌──────────┬─────────────────────────────────┬──────────────┬──────────────┬──────────────┐")
            output.append("│ Symbol   │ Company Name                    │ Price        │ Change       │ Volume       │")
            output.append("├──────────┼─────────────────────────────────┼──────────────┼──────────────┼──────────────┤")

        # Data rows
        for result in results:
            symbol = result.get('symbol', 'N/A')[:8]
            name = result.get('shortName', 'N/A')[:30]
            price = result.get('regularMarketPrice', 0)
            volume = result.get('regularMarketVolume', 0)

            if category == 'new':
                listing_date = result.get('listingDate', 'N/A')[:12]
                output.append(f"│ {symbol:8} │ {name:31} │ ${price:11.2f} │ {volume:12,} │ {listing_date:12} │")
            else:
                change = result.get('regularMarketChange', 0)
                change_pct = result.get('regularMarketChangePercent', 0)

                # Color code the change
                if change_pct > 0:
                    change_str = f"{Fore.GREEN}+{change:.2f} (+{change_pct:.1f}%){Style.RESET_ALL}"
                elif change_pct < 0:
                    change_str = f"{Fore.RED}{change:.2f} ({change_pct:.1f}%){Style.RESET_ALL}"
                else:
                    change_str = f"{Fore.YELLOW}{change:.2f} ({change_pct:.1f}%){Style.RESET_ALL}"

                # Format volume
                if volume >= 1_000_000:
                    volume_str = f"{volume/1_000_000:.1f}M"
                elif volume >= 1_000:
                    volume_str = f"{volume/1_000:.1f}K"
                else:
                    volume_str = str(volume)

                output.append(f"│ {symbol:8} │ {name:31} │ ${price:11.2f} │ {change_str:12} │ {volume_str:12} │")

        output.append("└──────────┴─────────────────────────────────────┴──────────────┴──────────────┴──────────────┘")
        output.append("")

        # Add summary statistics
        if category in ['gainers', 'losers'] and results:
            changes = [r.get('regularMarketChangePercent', 0) for r in results]
            avg_change = sum(changes) / len(changes)
            max_change = max(changes)
            min_change = min(changes)

            output.append(f"{Fore.CYAN}📈 Summary Statistics:{Style.RESET_ALL}")
            output.append(f"   Average Change: {avg_change:+.2f}%")
            output.append(f"   Best Performer: {max_change:+.2f}%")
            output.append(f"   Worst Performer: {min_change:+.2f}%")
            output.append("")

        return "\n".join(output)

    def screen_market(self, category: str, limit: int = 20, json_output: bool = False) -> dict:
        """
        Main screening function

        Args:
            category: "gainers", "losers", "actives", or "new"
            limit: Number of results to return
            json_output: Whether to return structured data instead of printing
        """
        if not json_output:
            print(f"{Fore.CYAN}🔍 Screening market for {category}...{Style.RESET_ALL}")
            print()

        if category == "new":
            results = self.get_new_listings(limit=limit)
        else:
            results = self.get_market_movers(category=category, limit=limit)

        result = {
            "command": "screen",
            "category": category,
            "limit": limit,
            "results": results
        }

        if not json_output:
            formatted_output = self.format_screener_results(results, category)
            print(formatted_output)

            # Additional insights
            if results and category != "new":
                print(f"{Fore.YELLOW}💡 Market Insights:{Style.RESET_ALL}")
                if category == "gainers":
                    print("   • Consider these stocks for momentum trading")
                    print("   • Check news and earnings for catalyst identification")
                    print("   • Monitor volume to confirm strength")
                elif category == "losers":
                    print("   • Potential value opportunities or falling knives")
                    print("   • Research fundamental reasons for decline")
                    print("   • Consider support levels before entry")
                elif category == "actives":
                    print("   • High volume indicates significant interest")
                    print("   • Check for news, earnings, or technical breakouts")
                    print("   • Monitor for continued momentum")
            elif results and category == "new":
                print(f"{Fore.YELLOW}💡 New Listings Insights:{Style.RESET_ALL}")
                print("   • Recently public companies may have high volatility")
                print("   • Research company fundamentals and business model")
                print("   • Consider lock-up period expiration dates")
        else:
            return result

        print()
        print(f"{Fore.GREEN}✅ Screening completed! Found {len(results)} {category}{Style.RESET_ALL}")


def main():
    """CLI for stock screener"""
    import argparse

    parser = argparse.ArgumentParser(description="Stock Market Screener")
    parser.add_argument('category', choices=['gainers', 'losers', 'actives', 'new'],
                       help='Screening category')
    parser.add_argument('--limit', '-l', type=int, default=20,
                       help='Number of results to return (default: 20)')

    args = parser.parse_args()

    screener = StockScreener()
    screener.screen_market(args.category, args.limit)


if __name__ == "__main__":
    main()
