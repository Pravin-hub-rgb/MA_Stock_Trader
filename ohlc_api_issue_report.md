# OHLC API Issue Report

## Problem Description

The Upstox OHLC Quotes V3 API is returning incorrect opening prices for stocks. The API is returning the current day's opening price as the previous day's closing price instead of the actual opening price.

## Test Results

### Current Test Output
```
SUCCESS: Opening price for NETWEB: Rs3127.90
```

### Expected vs Actual Results

**Expected:**
- Today's open: Rs3150.00
- Previous close: Rs3141.20

**Actual (from OHLC API):**
- Live OHLC open: Rs3127.90 (incorrect)
- Previous OHLC close: Rs3127.9 (incorrect)

### API Response Data
```json
{
  "status": "success",
  "data": {
    "NSE_EQ:NETWEB": {
      "live_ohlc": {
        "open": 3127.9,    // ← ISSUE: Should be 3150.00
        "high": 3127.9,
        "low": 3126.0,
        "close": 3126.0,
        "volume": 83,
        "ts": 1769146680000
      },
      "prev_ohlc": {
        "open": 3129.8,    // ← ISSUE: Should be 3150.00
        "high": 3129.9,
        "low": 3126.5,
        "close": 3127.9,   // ← ISSUE: Should be 3141.20
        "volume": 2032,
        "ts": 1769146620000
      }
    }
  }
}
```

## Issue Analysis

### Problem 1: Wrong Opening Price
The `live_ohlc.open` field is returning Rs3127.90 instead of the actual opening price of Rs3150.00.

### Problem 2: Wrong Previous Close
The `prev_ohlc.close` field is returning Rs3127.9 instead of the previous close of Rs3141.20.

### Problem 3: Data Inconsistency
The API is returning current market data mixed with session data, causing confusion about what represents the actual opening price.

## Code Snippet for Testing

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to investigate OHLC API opening price issue
"""

import sys
import os
import time as time_module
from datetime import datetime, time, timedelta
import pytz
import requests

# Add src to path
sys.path.append('src')

def test_ohlc_opening_price_issue():
    """Test to investigate why OHLC API returns wrong opening prices"""
    
    print("INVESTIGATING OHLC API OPENING PRICE ISSUE")
    print("=" * 50)
    
    # Import Upstox fetcher
    from src.utils.upstox_fetcher import UpstoxFetcher
    
    # Create fetcher
    upstox_fetcher = UpstoxFetcher()
    IST = pytz.timezone('Asia/Kolkata')
    
    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()
    
    # Test with NETWEB
    test_symbol = "NETWEB"
    print(f"Testing OHLC opening price for: {test_symbol}")
    print()
    
    try:
        # Get instrument key
        instrument_key = upstox_fetcher.get_instrument_key(test_symbol)
        print(f"Instrument key: {instrument_key}")
        
        # Get LTP data for comparison
        ltp_data = upstox_fetcher.get_ltp_data(test_symbol)
        print(f"LTP data: {ltp_data}")
        
        # Get OHLC data
        url = f"https://api.upstox.com/v3/market-quote/ohlc?instrument_key={instrument_key}&interval=I1"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {upstox_fetcher.access_token}"
        }
        
        response = requests.get(url, headers=headers)
        print(f"OHLC API response: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('status') == 'success':
                data = response_data.get('data', {})
                symbol_data = data.get(f"NSE_EQ:{test_symbol}", {})
                
                live_ohlc = symbol_data.get('live_ohlc', {})
                prev_ohlc = symbol_data.get('prev_ohlc', {})
                
                print(f"Live OHLC: {live_ohlc}")
                print(f"Prev OHLC: {prev_ohlc}")
                
                # Check what we're getting
                live_open = live_ohlc.get('open')
                prev_close = prev_ohlc.get('close')
                
                print(f"Live OHLC Open: {live_open}")
                print(f"Prev OHLC Close: {prev_close}")
                
                # The issue: these values are wrong
                if live_open and prev_close:
                    print("ISSUE: OHLC API returns incorrect opening prices")
                    print(f"  Expected today's open: 3150.00")
                    print(f"  Actual live_ohlc.open: {live_open}")
                    print(f"  Expected previous close: 3141.20")
                    print(f"  Actual prev_ohlc.close: {prev_close}")
                else:
                    print("ISSUE: No opening price data in OHLC response")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("OHLC API OPENING PRICE INVESTIGATION")
    print("Testing why Upstox OHLC API returns wrong opening prices")
    print()
    
    result = test_ohlc_opening_price_issue()
    
    print("\n" + "="*60)
    print("ISSUE SUMMARY:")
    print("- OHLC API live_ohlc.open returns wrong opening price")
    print("- OHLC API prev_ohlc.close returns wrong previous close")
    print("- Expected: Today's open = 3150.00, Previous close = 3141.20")
    print("- Actual: Live OHLC open = 3127.9, Prev OHLC close = 3127.9")
    print("- This affects reversal bot gap calculation accuracy")
    print("- Need to investigate proper opening price API or data source")
    print("="*60)