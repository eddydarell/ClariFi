#!/usr/bin/env python3
"""
Direct test of options analysis to debug Series ambiguity issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clarifi_engine'))

from clarifi_engine.engine import ClariFiEngine

def test_options_analysis():
    """Test options analysis directly"""
    engine = ClariFiEngine()

    print("🧪 Testing Options Analysis Directly")

    try:
        result = engine.comprehensive_analysis(
            tickers=['AAPL'],
            period='2y',
            include_patterns=False,
            include_events=False,
            include_options=True,
            include_seasonal=False,
            save_to_db=False
        )

        print("✅ Analysis completed successfully!")
        print(f"Result type: {type(result)}")
        if isinstance(result, dict):
            print(f"Result keys: {list(result.keys())}")
            print(f"Success: {result.get('success', 'N/A')}")
            if 'error' in result:
                print(f"Error: {result['error']}")
            if 'results' in result:
                print(f"Results keys: {list(result['results'].keys())}")
                for ticker, data in result['results'].items():
                    print(f"  {ticker} keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    if isinstance(data, dict) and 'options' in data:
                        print(f"    Options data: {data['options']}")
                    if isinstance(data, dict) and 'investment_advice' in data:
                        print(f"    Investment advice: {data['investment_advice']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_options_analysis()
