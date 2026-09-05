#!/usr/bin/env python3
"""
Quick test of live monitoring functionality
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

async def _run_live_monitor_test():
    """Test the live monitor for a few cycles"""
    print("🧪 Testing Live Stock Monitor")
    print("=" * 50)

    # Create monitor
    monitor = LiveStockMonitor()
    monitor.update_interval = 1  # 1 second for fast testing
    monitor.add_tickers(['AAPL', 'MSFT'])

    print(f"✅ Monitor created with tickers: {monitor.tickers}")

    # Test a few update cycles
    print("\n🔄 Testing price updates...")
    for i in range(2):
        print(f"\n--- Update cycle {i+1} ---")
        monitor.update_prices()

        # Show summary
        monitor.display_summary_table()

    print("\n✅ Test completed successfully!")
    print("🚀 Live monitoring is ready to use!")


def test_live_monitor():
    """Synchronous test wrapper for pytest."""
    asyncio.run(_run_live_monitor_test())


if __name__ == "__main__":
    test_live_monitor()
