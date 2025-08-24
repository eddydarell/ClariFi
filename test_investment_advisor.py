#!/usr/bin/env python3
"""
Test investment advisor directly to find Series ambiguity issue
"""

import sys
import os
import pandas as pd
import numpy as np
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clarifi_engine'))

from clarifi_engine.options_analyzer import InvestmentAdvisor

def test_investment_advisor():
    """Test investment advisor directly"""
    print("🧪 Testing Investment Advisor Directly")

    # Create simple test data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.01)

    stock_data = pd.DataFrame({
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)

    print(f"Created stock_data: {type(stock_data)}, shape: {stock_data.shape}")
    print(f"stock_data columns: {list(stock_data.columns)}")
    print(f"stock_data index type: {type(stock_data.index)}")

    advisor = InvestmentAdvisor()

    try:
        print("About to call generate_investment_suggestion...")
        result = advisor.generate_investment_suggestion(stock_data)
        print(f"✅ Success! Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_investment_advisor()
