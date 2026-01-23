# Opening Price Issue Report

## Problem Description

The Upstox API is returning `open: None` for stocks even when the market is open, which prevents proper opening price capture for the reversal trading bot.

## Test Results

### Current Test Output
```
SUCCESS: Opening price for NETWEB: Rs3150.00 (using LTP as market not open)
Gap: +0.28% (Open: Rs3150.00, Prev Close: Rs3141.20)
```

### API Response Data
```json
{
  "symbol": "NETWEB",
  "ltp": 3150.0,
  "cp": 3141.2,
  "open": null,    // ISSUE: This should have the opening price
  "high": null,
  "low": null,
  "volume": 310665,
  "ltq": 1
}
```

## Code Snippet for Testing

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to investigate opening price issue
"""

import sys
import os
import time as time_module
from datetime import datetime, time, timedelta
import pytz

# Add src to path
sys.path.append('src')

def test_opening_price_issue():
    """Test to investigate why opening price is None"""
    
    print("INVESTIGATING OPENING PRICE ISSUE")
    print("=" * 40)
    
    # Import Upstox fetcher
    from src.utils.upstox_fetcher import UpstoxFetcher
    
    # Create fetcher
    upstox_fetcher = UpstoxFetcher()
    IST = pytz.timezone('Asia/Kolkata')
    
    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()
    
    # Test with one stock from reversal list
    test_symbol = "NETWEB"
    print(f"Testing opening price for: {test_symbol}")
    print()
    
    try:
        # Get instrument key
        instrument_key = upstox_fetcher.get_instrument_key(test_symbol)
        print(f"Instrument key: {instrument_key}")
        
        # Get LTP data
        ltp_data = upstox_fetcher.get_ltp_data(test_symbol)
        print(f"LTP data: {ltp_data}")
        
        # Check market status
        current_time = datetime.now(IST).time()
        print(f"Current time: {current_time}")
        
        # Check if market should be open
        from config import MARKET_OPEN
        market_open_time = MARKET_OPEN
        print(f"Market open time: {market_open_time}")
        
        if current_time >= market_open_time:
            print("Market should be open")
        else:
            print("Market should be closed")
        
        # The issue: open price is None even when market is open
        if ltp_data and 'open' in ltp_data:
            if ltp_data['open'] is None:
                print("ISSUE: Opening price is None even though market is open")
                print("   This prevents proper gap calculation for reversal trading")
            else:
                print(f"Opening price: {ltp_data['open']}")
        
        return ltp_data
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("OPENING PRICE INVESTIGATION")
    print("Testing why Upstox API returns open: None")
    print()
    
    result = test_opening_price_issue()
    
    print("\n" + "="*50)
    print("ISSUE SUMMARY:")
    print("- Upstox API LTP endpoint returns open: null")
    print("- Even when market is open and trading is happening")
    print("- This affects reversal bot gap calculation")
    print("- Current workaround: Use LTP as opening price")
    print("- Need to investigate proper opening price API")
    print("="*50)
