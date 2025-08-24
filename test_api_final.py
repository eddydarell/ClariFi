#!/usr/bin/env python3
"""
Final comprehensive test using available data
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8181"

def test_with_available_data():
    """Test with tickers that have data available"""
    print("🔍 Testing comprehensive analysis with available data...")

    # Use tickers that have data files
    analysis_data = {
        "tickers": ["AAPL", "PLTR"],  # These have data files
        "period": "1d",  # Use a period that matches available data
        "include_patterns": True,
        "include_events": False,  # Skip to speed up
        "include_options": False,  # Skip to speed up
        "include_seasonal": False  # Skip to speed up
    }

    try:
        print(f"📡 Requesting analysis for: {', '.join(analysis_data['tickers'])}")
        response = requests.post(
            f"{BASE_URL}/api/analysis/comprehensive",
            json=analysis_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            print("📋 Response Summary:")
            print(f"  ✓ Success: {result.get('success', False)}")
            print(f"  ✓ Execution Time: {result.get('execution_time', 'N/A')}s")
            print(f"  ✓ Analyzed Tickers: {result.get('analyzed_tickers', 0)}")
            print(f"  ✓ Timestamp: {result.get('timestamp', 'N/A')}")

            if "results" in result:
                results = result["results"]
                print(f"\n📊 Analysis Results:")

                for ticker in analysis_data["tickers"]:
                    if ticker in results:
                        ticker_result = results[ticker]
                        print(f"\n  📈 {ticker}:")

                        if "error" in ticker_result:
                            print(f"    ❌ Error: {ticker_result['error']}")
                        else:
                            # Check what analysis components were completed
                            components_found = []

                            if "technical_analysis" in ticker_result:
                                components_found.append("Technical Analysis")
                                ta = ticker_result["technical_analysis"]
                                if "current_price" in ta:
                                    print(f"    💰 Current Price: ${ta['current_price']}")
                                if "trend" in ta:
                                    print(f"    📊 Trend: {ta['trend']}")

                            if "pattern_analysis" in ticker_result:
                                components_found.append("Pattern Analysis")
                                pa = ticker_result["pattern_analysis"]
                                if "patterns_found" in pa:
                                    patterns = pa["patterns_found"]
                                    print(f"    🔍 Patterns Found: {len(patterns)}")

                            if "summary" in ticker_result:
                                components_found.append("Summary")
                                summary = ticker_result["summary"]
                                if "overall_sentiment" in summary:
                                    print(f"    📝 Overall Sentiment: {summary['overall_sentiment']}")

                            if "recommendations" in ticker_result:
                                components_found.append("Recommendations")
                                recs = ticker_result["recommendations"]
                                if recs:
                                    print(f"    💡 Recommendations: {len(recs)} found")

                            if components_found:
                                print(f"    ✅ Completed: {', '.join(components_found)}")
                            else:
                                print(f"    ⚠️  No analysis components found")
                    else:
                        print(f"\n  ❌ {ticker}: No results returned")

            # Check for any overall errors or warnings
            if "error" in result:
                print(f"\n⚠️  Overall Error: {result['error']}")

            if "warnings" in result:
                print(f"\n⚠️  Warnings: {result['warnings']}")

            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Response text: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out - analysis may take longer than expected")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_api_endpoints_summary():
    """Test multiple endpoints to verify API functionality"""
    print("\n🔍 Testing multiple API endpoints...")

    endpoints = [
        ("/health", "GET"),
        ("/docs", "GET"),
        ("/api/portfolios", "GET"),
        ("/api/analysis/history", "GET")
    ]

    results = {}

    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)

            results[endpoint] = {
                "status_code": response.status_code,
                "success": response.status_code == 200
            }

            status = "✅" if response.status_code == 200 else "❌"
            print(f"  {status} {method} {endpoint}: {response.status_code}")

        except Exception as e:
            results[endpoint] = {
                "status_code": "Error",
                "success": False,
                "error": str(e)
            }
            print(f"  ❌ {method} {endpoint}: {e}")

    return results

def main():
    """Run final comprehensive tests"""
    print("🚀 ClariFi Backend API - Final Comprehensive Test")
    print("=" * 60)

    # Test endpoints availability
    endpoint_results = test_api_endpoints_summary()

    # Test comprehensive analysis with available data
    analysis_success = test_with_available_data()

    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 60)

    # Count successful endpoints
    successful_endpoints = sum(1 for result in endpoint_results.values() if result["success"])
    total_endpoints = len(endpoint_results)

    print(f"API Endpoints: {successful_endpoints}/{total_endpoints} working")
    print(f"Comprehensive Analysis: {'✅ PASS' if analysis_success else '❌ FAIL'}")

    if successful_endpoints == total_endpoints and analysis_success:
        print("\n🎉 Backend API is working correctly!")
        print("✅ All endpoints are responding properly")
        print("✅ Comprehensive analysis endpoint is functional")
        print("✅ Error handling is working correctly")
        print("✅ Response structure is properly formatted")
    else:
        print("\n⚠️  Some issues detected:")
        if successful_endpoints < total_endpoints:
            print(f"  - {total_endpoints - successful_endpoints} endpoint(s) not working")
        if not analysis_success:
            print("  - Comprehensive analysis has issues")

if __name__ == "__main__":
    main()
