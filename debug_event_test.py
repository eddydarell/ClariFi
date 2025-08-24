#!/usr/bin/env python3
"""
Direct test of event analysis to debug serialization issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clarifi_engine'))

from clarifi_engine.engine import ClariFiEngine

def test_event_analysis():
    """Test event analysis directly"""
    engine = ClariFiEngine()

    print("🧪 Testing Event Analysis Directly")

    try:
        result = engine.comprehensive_analysis(
            tickers=['AAPL'],
            period='2y',
            include_patterns=False,
            include_events=True,
            include_options=False,
            include_seasonal=False,
            save_to_db=False  # Disable database save to avoid pandas serialization issues
        )

        print("✅ Analysis completed successfully!")
        print(f"Result type: {type(result)}")
        if isinstance(result, dict):
            print(f"Result keys: {list(result.keys())}")
            print(f"Success: {result.get('success', 'N/A')}")
            if 'error' in result:
                print(f"Error: {result['error']}")
            if 'partial_results' in result:
                print(f"Partial results: {result['partial_results']}")
            if 'results' in result:
                print(f"Results keys: {list(result['results'].keys())}")
                for ticker, data in result['results'].items():
                    print(f"  {ticker} keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    if isinstance(data, dict) and 'events' in data:
                        print(f"    Events data type: {type(data['events'])}")
                        if data['events'] is not None:
                            print(f"    Events content preview: {str(data['events'])[:200]}...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_event_analysis()
