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

async def test_live_monitor():
    """Test the live monitor for a few cycles"""
    print("🧪 Testing Live Stock Monitor")
    print("=" * 50)

    # Create monitor
    monitor = LiveStockMonitor()
    monitor.update_interval = 3  # 3 seconds for testing
    monitor.add_tickers(['AAPL', 'MSFT'])

    print(f"✅ Monitor created with tickers: {monitor.tickers}")

    # Test a few update cycles
    print("\n🔄 Testing price updates...")
    for i in range(3):
        print(f"\n--- Update cycle {i+1} ---")
        monitor.update_prices()

        # Show summary
        monitor.display_summary_table()

        if i < 2:  # Don't wait after the last iteration
            print(f"⏳ Waiting {monitor.update_interval} seconds...")
            await asyncio.sleep(monitor.update_interval)

    print("\n✅ Test completed successfully!")
    print("🚀 Live monitoring is ready to use!")

if __name__ == "__main__":
    asyncio.run(test_live_monitor())
