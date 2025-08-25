#!/usr/bin/env python3
"""
Demo script for market screening functionality
"""

import sys
import os

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from stock_screener import StockScreener
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def demo_market_screening():
    """Demo the market screening functionality"""
    print(f"{Fore.MAGENTA}🎬 ClariFi Market Screening Demo{Style.RESET_ALL}")
    print("=" * 60)
    print("📊 This demo shows market screening capabilities:")
    print("   • Top gainers screening")
    print("   • Top losers screening")
    print("   • Most active stocks")
    print("   • New listings discovery")
    print("=" * 60)
    print()

    screener = StockScreener()

    categories = [
        ("gainers", "📈 Top Gainers"),
        ("losers", "📉 Top Losers"),
        ("actives", "🔥 Most Active"),
        ("new", "🆕 New Listings")
    ]

    for category, title in categories:
        print(f"{Fore.CYAN}{title}{Style.RESET_ALL}")
        print("-" * 40)
        screener.screen_market(category, limit=3)
        print()

    print("🎉 Demo completed!")
    print()
    print("💡 To use market screening:")
    print("   ./run.sh screen gainers")
    print("   ./run.sh screen losers --limit 10")
    print("   ./run.sh screen actives --limit 15")
    print("   ./run.sh screen new")
    print()
    print("📖 Available categories:")
    print("   gainers  - Stocks with highest percentage gains")
    print("   losers   - Stocks with highest percentage losses")
    print("   actives  - Stocks with highest trading volume")
    print("   new      - Recently listed/IPO stocks")

if __name__ == "__main__":
    demo_market_screening()
