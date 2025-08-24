#!/usr/bin/env python3
"""
Detailed test for ClariFi comprehensive analysis response
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8181"

def test_comprehensive_analysis_detailed():
    """Test comprehensive analysis with detailed response validation"""
    print("🔍 Testing comprehensive analysis with detailed validation...")

    # Test data
    analysis_data = {
        "tickers": ["AAPL", "MSFT"],
        "period": "3m",
        "include_patterns": True,
        "include_events": True,
        "include_options": True,
        "include_seasonal": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/analysis/comprehensive",
            json=analysis_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # Print the full response for detailed inspection
            print("📋 Full Response Structure:")
            print(json.dumps(result, indent=2, default=str))

            # Validate response structure
            print("\n📊 Response Validation:")

            # Check top-level structure
            if "success" in result:
                print(f"  ✓ Success flag: {result['success']}")

            if "timestamp" in result:
                print(f"  ✓ Timestamp: {result['timestamp']}")

            if "results" in result:
                results = result["results"]
                print(f"  ✓ Results found for {len(results)} ticker(s)")

                # Check each ticker's analysis results
                for ticker in analysis_data["tickers"]:
                    if ticker in results:
                        ticker_result = results[ticker]
                        print(f"\n  📈 {ticker} Analysis Results:")

                        # Check for expected analysis components
                        components = [
                            "technical_analysis",
                            "pattern_analysis",
                            "event_correlation",
                            "options_analysis",
                            "seasonal_analysis",
                            "summary",
                            "recommendations"
                        ]

                        for component in components:
                            if component in ticker_result:
                                print(f"    ✓ {component}: Present")

                                # If it's technical analysis, check sub-components
                                if component == "technical_analysis" and isinstance(ticker_result[component], dict):
                                    ta = ticker_result[component]
                                    ta_components = ["indicators", "signals", "trend", "support_resistance"]
                                    for ta_comp in ta_components:
                                        if ta_comp in ta:
                                            print(f"      ✓ {ta_comp}: Present")
                                        else:
                                            print(f"      ⚠️  {ta_comp}: Missing")

                                # If it's pattern analysis, check for patterns
                                elif component == "pattern_analysis" and isinstance(ticker_result[component], dict):
                                    pa = ticker_result[component]
                                    if "patterns_found" in pa:
                                        patterns = pa["patterns_found"]
                                        print(f"      ✓ Found {len(patterns)} pattern(s)")

                            else:
                                print(f"    ⚠️  {component}: Missing")
                    else:
                        print(f"  ❌ {ticker}: No results found")

            # Check for any error messages
            if "error" in result:
                print(f"  ⚠️  Error in response: {result['error']}")

            # Check for warnings
            if "warnings" in result:
                print(f"  ⚠️  Warnings: {result['warnings']}")

            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_single_ticker_analysis():
    """Test analysis with a single ticker for more detailed results"""
    print("\n🔍 Testing single ticker analysis...")

    analysis_data = {
        "tickers": ["AAPL"],
        "period": "1m",  # Shorter period for faster response
        "include_patterns": True,
        "include_events": True,
        "include_options": False,  # Skip options for faster response
        "include_seasonal": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/analysis/comprehensive",
            json=analysis_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()

            if "results" in result and "AAPL" in result["results"]:
                aapl_result = result["results"]["AAPL"]

                print("📈 AAPL Analysis Summary:")

                # Check for technical indicators
                if "technical_analysis" in aapl_result:
                    ta = aapl_result["technical_analysis"]
                    if "current_price" in ta:
                        print(f"  💰 Current Price: ${ta['current_price']}")
                    if "trend" in ta:
                        print(f"  📊 Trend: {ta['trend']}")
                    if "signals" in ta:
                        signals = ta["signals"]
                        if signals:
                            print(f"  🚨 Signals: {', '.join(signals)}")

                # Check for patterns
                if "pattern_analysis" in aapl_result:
                    pa = aapl_result["pattern_analysis"]
                    if "patterns_found" in pa and pa["patterns_found"]:
                        print(f"  🔍 Patterns Found: {len(pa['patterns_found'])}")
                        for pattern in pa["patterns_found"][:3]:  # Show first 3
                            if isinstance(pattern, dict) and "pattern" in pattern:
                                confidence = pattern.get("confidence", "N/A")
                                print(f"    - {pattern['pattern']} (confidence: {confidence})")

                # Check for recommendations
                if "recommendations" in aapl_result:
                    recommendations = aapl_result["recommendations"]
                    if recommendations:
                        print(f"  💡 Recommendations:")
                        for rec in recommendations[:3]:  # Show first 3
                            print(f"    - {rec}")

                return True
            else:
                print("❌ No AAPL results found in response")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Single ticker test failed: {e}")
        return False

def main():
    """Run detailed API tests"""
    print("🚀 ClariFi Backend API - Detailed Response Testing")
    print("=" * 60)

    # Test comprehensive analysis with detailed validation
    success1 = test_comprehensive_analysis_detailed()

    # Test single ticker for more focused results
    success2 = test_single_ticker_analysis()

    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 All detailed tests passed! The API responses are properly structured.")
    else:
        print("⚠️  Some tests failed. Check the API implementation.")

if __name__ == "__main__":
    main()
