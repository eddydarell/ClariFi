#!/usr/bin/env python3
"""
Test script for ClariFi Backend API
Tests various endpoints to ensure proper responses
"""

import requests
import json
import time
from datetime import datetime

# API Base URL
BASE_URL = "http://localhost:8181"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_comprehensive_analysis():
    """Test the comprehensive analysis endpoint"""
    print("\n🔍 Testing comprehensive analysis endpoint...")

    # Test data
    analysis_data = {
        "tickers": ["AAPL", "MSFT", "GOOG"],
        "period": "6m",
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
            print("✅ Comprehensive analysis successful!")

            # Check if the response has expected structure
            expected_keys = ["success", "analysis_id", "timestamp", "results"]
            for key in expected_keys:
                if key in result:
                    print(f"  ✓ Found expected key: {key}")
                else:
                    print(f"  ⚠️  Missing expected key: {key}")

            # Print summary of results
            if "results" in result:
                results = result["results"]
                print(f"  📊 Analysis results summary:")

                for ticker in analysis_data["tickers"]:
                    if ticker in results:
                        ticker_data = results[ticker]
                        print(f"    {ticker}:")
                        if "technical_analysis" in ticker_data:
                            print(f"      ✓ Technical analysis included")
                        if "pattern_analysis" in ticker_data:
                            print(f"      ✓ Pattern analysis included")
                        if "event_correlation" in ticker_data:
                            print(f"      ✓ Event correlation included")
                        if "options_analysis" in ticker_data:
                            print(f"      ✓ Options analysis included")
                        if "seasonal_analysis" in ticker_data:
                            print(f"      ✓ Seasonal analysis included")
                    else:
                        print(f"    ⚠️  {ticker}: Missing from results")

            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"Response text: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Comprehensive analysis test failed: {e}")
        return False

def test_portfolio_operations():
    """Test portfolio creation and operations"""
    print("\n🔍 Testing portfolio operations...")

    portfolio_id = None

    try:
        # Create a test portfolio
        portfolio_data = {
            "name": f"Test Portfolio {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "Test portfolio for API testing"
        }

        response = requests.post(
            f"{BASE_URL}/api/portfolios",
            json=portfolio_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"Create Portfolio - Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            portfolio_id = result.get("portfolio_id")
            print(f"✅ Portfolio created with ID: {portfolio_id}")

            # Add a ticker to the portfolio
            if portfolio_id:
                ticker_data = {
                    "ticker": "AAPL",
                    "quantity": 10.0,
                    "avg_cost": 150.0
                }

                response = requests.post(
                    f"{BASE_URL}/api/portfolios/{portfolio_id}/tickers",
                    json=ticker_data,
                    headers={"Content-Type": "application/json"}
                )

                print(f"Add Ticker - Status Code: {response.status_code}")
                if response.status_code == 200:
                    print("✅ Ticker added to portfolio successfully")
                else:
                    print(f"❌ Failed to add ticker: {response.text}")

                # Test portfolio analysis
                response = requests.post(
                    f"{BASE_URL}/api/analysis/portfolio/{portfolio_id}",
                    params={"period": "3m"}
                )

                print(f"Portfolio Analysis - Status Code: {response.status_code}")
                if response.status_code == 200:
                    print("✅ Portfolio analysis completed successfully")
                    result = response.json()
                    if "success" in result and result["success"]:
                        print("  ✓ Analysis marked as successful")
                    if "portfolio_summary" in result:
                        print("  ✓ Portfolio summary included")
                    if "analysis_results" in result:
                        print("  ✓ Analysis results included")
                else:
                    print(f"❌ Portfolio analysis failed: {response.text}")

            return True
        else:
            print(f"❌ Portfolio creation failed: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Portfolio operations test failed: {e}")
        return False

def test_analysis_history():
    """Test analysis history endpoint"""
    print("\n🔍 Testing analysis history endpoint...")

    try:
        response = requests.get(f"{BASE_URL}/api/analysis/history?limit=5")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Analysis history retrieved successfully")

            if "success" in result and result["success"]:
                print("  ✓ Response marked as successful")

            if "history" in result:
                history = result["history"]
                print(f"  📜 Found {len(history)} history entries")

                if history:
                    # Check structure of first entry
                    first_entry = history[0]
                    expected_fields = ["analysis_id", "timestamp", "tickers", "analysis_type"]
                    for field in expected_fields:
                        if field in first_entry:
                            print(f"    ✓ History entry has {field}")
                        else:
                            print(f"    ⚠️  History entry missing {field}")

            return True
        else:
            print(f"❌ Analysis history failed: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Analysis history test failed: {e}")
        return False

def test_api_documentation():
    """Test if API documentation is accessible"""
    print("\n🔍 Testing API documentation...")

    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("✅ API documentation is accessible")
            return True
        else:
            print(f"❌ API documentation not accessible")
            return False

    except Exception as e:
        print(f"❌ API documentation test failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("🚀 Starting ClariFi Backend API Tests")
    print("=" * 50)

    test_results = []

    # Run all tests
    test_results.append(("Health Check", test_health_check()))
    test_results.append(("API Documentation", test_api_documentation()))
    test_results.append(("Comprehensive Analysis", test_comprehensive_analysis()))
    test_results.append(("Portfolio Operations", test_portfolio_operations()))
    test_results.append(("Analysis History", test_analysis_history()))

    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The API is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the backend implementation.")

if __name__ == "__main__":
    main()
