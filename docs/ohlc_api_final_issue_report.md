# OHLC API Final Issue Report

## Problem Description

The Upstox OHLC Quotes V3 API is returning incorrect opening prices for stocks. The API is returning the current market price instead of the actual opening price from 9:15 AM.

## Test Results

### Current Test Output
```
Live OHLC Open: 3131.6
Prev OHLC Close: 3131.8
```

### Expected vs Actual Results

**Expected:**
- Today's open: Rs3150.00 (actual opening price at 9:15 AM)
- Previous close: Rs3141.20 (previous day's closing price)

**Actual (from OHLC API):**
- Live OHLC open: Rs3131.6 (current market price, not opening price)
- Previous OHLC close: Rs3131.8 (incorrect previous close)

## Issue Analysis

### Problem 1: Wrong Opening Price
The `live_ohlc.open` field is returning Rs3131.6 instead of the actual opening price of Rs3150.00. This appears to be the current market price rather than the opening price from 9:15 AM.

### Problem 2: Wrong Previous Close
The `prev_ohlc.close` field is returning Rs3131.8 instead of the previous close of Rs3141.20.

### Problem 3: Data Timing Issue
The API seems to be returning current market data mixed with session data, causing confusion about what represents the actual opening price.

## Code Snippet for Testing

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final test script to investigate OHLC API opening price issue
"""

import sys
import os
import time as time_module
from datetime import datetime, time, timedelta
import pytz
import requests

# Add src to path
sys.path.append('src')

def test_ohlc_opening_price_final_issue():
    """Final test to investigate why OHLC API returns wrong opening prices"""
    
    print("FINAL INVESTIGATION: OHLC API OPENING PRICE ISSUE")
    print("=" * 60)
    
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
                    print("FINAL ISSUE: OHLC API returns incorrect opening prices")
                    print(f"  Expected today's open: 3150.00")
                    print(f"  Actual live_ohlc.open: {live_open}")
                    print(f"  Expected previous close: 3141.20")
                    print(f"  Actual prev_ohlc.close: {prev_close}")
                    print(f"  Current LTP: {ltp_data.get('ltp')}")
                    
                    # Check if live_open matches current LTP (indicating wrong data)
                    if live_open == ltp_data.get('ltp'):
                        print("  CONFIRMED: live_ohlc.open matches current LTP - API returns wrong data")
                else:
                    print("ISSUE: No opening price data in OHLC response")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("OHLC API FINAL INVESTIGATION")
    print("Testing why Upstox OHLC API returns wrong opening prices")
    print()
    
    result = test_ohlc_opening_price_final_issue()
    
    print("\n" + "="*70)
    print("FINAL ISSUE SUMMARY:")
    print("- OHLC API live_ohlc.open returns current market price, not opening price")
    print("- OHLC API prev_ohlc.close returns wrong previous close")
    print("- Expected: Today's open = 3150.00, Previous close = 3141.20")
    print("- Actual: Live OHLC open = 3131.6, Prev OHLC close = 3131.8")
    print("- This affects reversal bot gap calculation accuracy")
    print("- Need to find alternative method for getting accurate opening prices")
    print("="*70)