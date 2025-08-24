#!/usr/bin/env python3
"""
Direct test of the ClariFi Engine to isolate the investment advice issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from clarifi_engine.engine import ClariFiEngine

def test_engine_direct():
    """Test the engine directly to see where the Series boolean issue occurs"""

    print("🚀 Testing ClariFi Engine Direct Analysis")
    print("="*50)

    # Initialize engine
    engine = ClariFiEngine()

    # Test with a single ticker
    test_ticker = "AAPL"
    test_period = "1y"

    print(f"📊 Testing comprehensive analysis for {test_ticker}")
    print(f"📅 Period: {test_period}")
    print(f"🔧 Options: patterns=True, events=False, options=True, seasonal=False")
    print("-" * 50)

    # Run analysis with minimal components to isolate the issue
    result = engine.comprehensive_analysis(
        tickers=[test_ticker],
        period=test_period,
        save_to_db=False,  # Don't save to DB for testing
        include_patterns=True,
        include_events=False,  # Disable events for now
        include_options=True,   # This is where the issue occurs
        include_seasonal=False  # Disable seasonal for now
    )

    print("\n📋 ANALYSIS RESULTS:")
    print("="*50)

    if result["success"]:
        print("✅ Analysis completed successfully!")
        print(f"⏱️  Execution time: {result['execution_time']:.2f}s")
        print(f"📊 Analyzed tickers: {result['analyzed_tickers']}")

        # Check each ticker's results
        for ticker, data in result["results"].items():
            print(f"\n🔍 {ticker} Results:")
            for component, component_data in data.items():
                if isinstance(component_data, dict) and "error" in component_data:
                    print(f"   ❌ {component}: {component_data['error']}")
                else:
                    print(f"   ✅ {component}: OK")

    else:
        print("❌ Analysis failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")

        # Show partial results if available
        if "partial_results" in result:
            print("\n📋 Partial Results:")
            for ticker, data in result["partial_results"].items():
                print(f"🔍 {ticker}:")
                for component, component_data in data.items():
                    if isinstance(component_data, dict) and "error" in component_data:
                        print(f"   ❌ {component}: {component_data['error']}")
                    else:
                        print(f"   ✅ {component}: OK")

if __name__ == "__main__":
    test_engine_direct()
