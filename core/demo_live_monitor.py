#!/usr/bin/env python3
"""
Demo script for live monitoring with automatic exit after showing functionality
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from live_monitor import LiveStockMonitor
except ImportError as e:
    print(f"Error importing live_monitor: {e}")
    sys.exit(1)

async def demo_live_monitor():
    """Demo the live monitor with automatic exit"""
    print("🎬 ClariFi Live Monitoring Demo")
    print("=" * 60)
    print("📡 This demo shows real-time stock monitoring with:")
    print("   • Color-coded price changes (🟢 up, 🔴 down, 🟡 unchanged)")
    print("   • Summary tables with trends")
    print("   • Performance metrics")
    print("   • Terminal-based graphs")
    print("=" * 60)
    print()

    # Create monitor
    monitor = LiveStockMonitor()
    monitor.update_interval = 4  # 4 seconds for demo
    monitor.add_tickers(['AAPL', 'MSFT', 'GOOGL'])

    print(f"🚀 Starting live demo for: {', '.join(monitor.tickers)}")
    print(f"⏱️  Update interval: {monitor.update_interval} seconds")
    print(f"🎯 Demo will run for 3 update cycles, then exit automatically")
    print()

    # Demo header
    monitor.display_header()

    # Run 3 update cycles
    for cycle in range(3):
        print(f"{Fore.CYAN}🔄 Update Cycle {cycle + 1}/3{Style.RESET_ALL}")
        print("-" * 40)

        # Update prices
        monitor.update_prices()
        print()

        # Show summary
        monitor.display_summary_table()

        # Show performance metrics
        monitor.display_performance_metrics()

        # Show a simple graph for the first ticker if we have enough data
        if cycle >= 1:  # Need at least 2 data points for a graph
            print(f"{Fore.YELLOW}📈 Sample Terminal Chart for {monitor.tickers[0]}:{Style.RESET_ALL}")
            monitor.display_terminal_graph(monitor.tickers[0])

        if cycle < 2:  # Don't wait after the last cycle
            print(f"{Fore.CYAN}⏳ Waiting {monitor.update_interval} seconds for next update...{Style.RESET_ALL}")
            await asyncio.sleep(monitor.update_interval)

    print()
    print("🎉 Demo completed!")
    print()
    print("💡 To start live monitoring manually, run:")
    print("   ./run.sh live AAPL MSFT TSLA")
    print("   ./run.sh live PLTR QBTS --interval 10")
    print("   ./run.sh live AAPL --no-graphs --interval 5")
    print()
    print("📖 Available options:")
    print("   --interval, -i : Update interval in seconds (default: 5)")
    print("   --no-graphs    : Disable terminal graphs")
    print("   --no-summary   : Disable summary table")
    print()
    print("⚠️  Press Ctrl+C anytime to stop live monitoring")

if __name__ == "__main__":
    # Import colorama for the demo
    try:
        from colorama import Fore, Style
    except ImportError:
        # Fallback if colorama is not available
        class Fore:
            CYAN = ""
            YELLOW = ""
        class Style:
            RESET_ALL = ""

    asyncio.run(demo_live_monitor())
