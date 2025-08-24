#!/usr/bin/env python3
"""
ClariFi CLI Comprehensive Analysis Tool
Command-line interface for testing comprehensive stock analysis
"""

import requests
import json
import argparse
import sys
from datetime import datetime
from typing import List

class ClariFiCLI:
    def __init__(self, base_url: str = "http://localhost:8181"):
        self.base_url = base_url

    def test_connection(self) -> bool:
        """Test if the ClariFi API is accessible"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def comprehensive_analysis(self, tickers: List[str], period: str = "1d",
                             include_patterns: bool = True, include_events: bool = True,
                             include_options: bool = True, include_seasonal: bool = True,
                             verbose: bool = False) -> dict:
        """Run comprehensive analysis for given tickers"""

        analysis_data = {
            "tickers": tickers,
            "period": period,
            "include_patterns": include_patterns,
            "include_events": include_events,
            "include_options": include_options,
            "include_seasonal": include_seasonal
        }

        if verbose:
            print(f"📡 Requesting analysis for: {', '.join(tickers)}")
            print(f"   Period: {period}")
            print(f"   Components: Patterns={include_patterns}, Events={include_events}, Options={include_options}, Seasonal={include_seasonal}")

        start_time = datetime.now()

        try:
            response = requests.post(
                f"{self.base_url}/api/analysis/comprehensive",
                json=analysis_data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if verbose:
                print(f"⏱️  Request completed in {duration:.2f} seconds")
                print(f"📊 HTTP Status: {response.status_code}")

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}

        except requests.exceptions.Timeout:
            return {"error": "Request timed out (>60 seconds)"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

    def format_analysis_results(self, result: dict, detailed: bool = False) -> None:
        """Format and display analysis results"""

        if "error" in result:
            print(f"❌ Analysis failed: {result['error']}")
            return

        print("\n📈 ANALYSIS SUMMARY")
        print("-" * 40)
        print(f"Success: {result.get('success', False)}")
        print(f"Execution Time: {result.get('execution_time', 'N/A'):.3f}s")
        print(f"Tickers Analyzed: {result.get('analyzed_tickers', 0)}")
        print(f"Timestamp: {result.get('timestamp', 'N/A')}")

        if "results" not in result:
            print("❌ No results found in response")
            return

        results = result["results"]
        print(f"\n🔍 TICKER ANALYSIS RESULTS")
        print("=" * 50)

        for ticker, ticker_data in results.items():
            print(f"\n📊 {ticker}:")
            print("-" * 20)

            # Check for errors first
            if "error" in ticker_data:
                print(f"  ❌ Error: {ticker_data['error']}")
                continue

            # Core recommendation
            if "overall_recommendation" in ticker_data:
                rec = ticker_data["overall_recommendation"]
                conf = ticker_data.get("confidence_level", "N/A")
                risk = ticker_data.get("risk_level", "N/A")
                print(f"  💡 Recommendation: {rec}")
                print(f"  🎯 Confidence: {conf}")
                print(f"  ⚠️  Risk Level: {risk}")

            if detailed:
                # Analysis ID
                if "analysis_id" in ticker_data:
                    aid = ticker_data["analysis_id"][:12]
                    print(f"  🆔 Analysis ID: {aid}...")

                # Pattern Analysis
                if "patterns" in ticker_data:
                    patterns = ticker_data["patterns"]
                    if isinstance(patterns, dict):
                        pattern_count = len([k for k, v in patterns.items() if v])
                        print(f"  🔍 Pattern Analysis: {len(patterns)} type(s)")
                        if detailed and patterns:
                            for pattern_type in list(patterns.keys())[:3]:
                                print(f"      - {pattern_type}")

                # Event Analysis
                if "events" in ticker_data:
                    events = ticker_data["events"]
                    if isinstance(events, dict):
                        print(f"  📅 Event Analysis: {len(events)} events")
                        if detailed and events:
                            sample_event = list(events.values())[0]
                            if "event_info" in sample_event:
                                event_name = sample_event["event_info"]["event"]
                                print(f"      Sample: {event_name[:40]}...")

                # Options Analysis
                if "options" in ticker_data:
                    options = ticker_data["options"]
                    if isinstance(options, dict):
                        if "error" in options:
                            print(f"  📈 Options: Error")
                        else:
                            print(f"  📈 Options: Available")

                # Seasonal Analysis
                if "seasonal" in ticker_data:
                    seasonal = ticker_data["seasonal"]
                    status = "Available" if seasonal else "No data"
                    print(f"  🌍 Seasonal: {status}")

                # Investment Advice
                if "investment_advice" in ticker_data:
                    advice = ticker_data["investment_advice"]
                    if isinstance(advice, dict):
                        suggestion = advice.get("suggestion", "N/A")
                        reasoning = advice.get("reasoning", "N/A")
                        print(f"  💭 Advice: {suggestion}")
                        if detailed:
                            print(f"      Reasoning: {reasoning[:50]}...")

            # Component count
            component_count = len([k for k in ticker_data.keys()
                                 if k not in ["overall_recommendation", "confidence_level", "risk_level", "analysis_id"]])
            print(f"  📋 Components: {component_count}")

def main():
    parser = argparse.ArgumentParser(description="ClariFi CLI Comprehensive Analysis Tool")
    parser.add_argument("tickers", nargs="+", help="Stock ticker symbols (e.g., AAPL MSFT PLTR)")
    parser.add_argument("--period", "-p", default="1d", help="Analysis period (default: 1d)")
    parser.add_argument("--no-patterns", action="store_true", help="Skip pattern analysis")
    parser.add_argument("--no-events", action="store_true", help="Skip event analysis")
    parser.add_argument("--no-options", action="store_true", help="Skip options analysis")
    parser.add_argument("--no-seasonal", action="store_true", help="Skip seasonal analysis")
    parser.add_argument("--detailed", "-d", action="store_true", help="Show detailed results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--url", default="http://localhost:8181", help="ClariFi API base URL")

    args = parser.parse_args()

    # Initialize CLI
    cli = ClariFiCLI(args.url)

    # Test connection
    if not cli.test_connection():
        print(f"❌ Cannot connect to ClariFi API at {args.url}")
        print("   Make sure the backend server is running")
        sys.exit(1)

    if args.verbose:
        print(f"✅ Connected to ClariFi API at {args.url}")

    # Prepare analysis parameters
    include_patterns = not args.no_patterns
    include_events = not args.no_events
    include_options = not args.no_options
    include_seasonal = not args.no_seasonal

    # Run analysis
    print(f"🚀 ClariFi Comprehensive Analysis")
    print(f"Tickers: {', '.join(args.tickers)}")

    result = cli.comprehensive_analysis(
        tickers=args.tickers,
        period=args.period,
        include_patterns=include_patterns,
        include_events=include_events,
        include_options=include_options,
        include_seasonal=include_seasonal,
        verbose=args.verbose
    )

    # Display results
    cli.format_analysis_results(result, detailed=args.detailed)

    # Exit with appropriate code
    if "error" in result:
        sys.exit(1)
    else:
        print(f"\n✅ Analysis completed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
