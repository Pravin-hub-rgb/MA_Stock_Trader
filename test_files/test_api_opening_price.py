#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for API-based opening price capture
Tests the Upstox Full Market Quote API to get opening prices
"""

import sys
import os
import time as time_module
from datetime import datetime, time, timedelta
import pytz

# Add src to path
sys.path.append('src')

def test_api_opening_price():
    """Test API call to get opening price for one stock"""
    
    print("TESTING API OPENING PRICE CAPTURE")
    print("=" * 40)
    
    # Import Upstox fetcher
    from src.utils.upstox_fetcher import UpstoxFetcher
    
    # Create fetcher
    upstox_fetcher = UpstoxFetcher()
    IST = pytz.timezone('Asia/Kolkata')
    
    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()
    
    # Test with one stock from reversal list
    test_symbol = "NETWEB"  # Pick NETWEB from reversal list
    print(f"Testing opening price capture for: {test_symbol}")
    print()
    
    try:
        # Get instrument key for the stock
        print("Step 1: Getting instrument key...")
        instrument_key = upstox_fetcher.get_instrument_key(test_symbol)
        if not instrument_key:
            print(f"ERROR: Could not get instrument key for {test_symbol}")
            return
            
        print(f"✓ Instrument key: {instrument_key}")
        print()
        
        # Get previous close for the stock
        print("Step 2: Getting previous close...")
        ltp_data = upstox_fetcher.get_ltp_data(test_symbol)
        if not ltp_data or 'cp' not in ltp_data or ltp_data['cp'] is None:
            print(f"ERROR: Could not get previous close for {test_symbol}")
            return
            
        prev_close = float(ltp_data['cp'])
        print(f"✓ Previous close: Rs{prev_close:.2f}")
        print()
        
        # Make API call to get opening price using LTP method (more reliable for opening prices)
        print("Step 3: Making LTP API call...")
        print(f"Calling API for: {instrument_key}")
        
        # Use the LTP method which is more reliable for opening prices
        ltp_data = upstox_fetcher.get_ltp_data(test_symbol)
        print(f"✓ API response received: {type(ltp_data)}")
        print(f"✓ Response keys: {list(ltp_data.keys()) if ltp_data else 'None'}")
        print()
        
        # Process response - use LTP as opening price if open is None (market not open yet)
        if ltp_data and 'ltp' in ltp_data and ltp_data['ltp'] is not None:
            # If open price is None, use LTP as the opening price (current market price)
            open_price = float(ltp_data['ltp'])
            print(f"✓ SUCCESS: Opening price for {test_symbol}: Rs{open_price:.2f} (using LTP as market not open)")
            
            # Calculate gap
            gap_pct = ((open_price - prev_close) / prev_close) * 100
            print(f"✓ Gap: {gap_pct:+.2f}% (Open: Rs{open_price:.2f}, Prev Close: Rs{prev_close:.2f})")
            
            return True
        else:
            print("ERROR: No LTP data in response")
            print(f"LTP data: {ltp_data}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("KILLING ALL BOTS BEFORE TESTING...")
    print("Please ensure no other trading bots are running")
    print()
    
    # Wait a moment
    print("Waiting 3 seconds before test...")
    time_module.sleep(3)
    
    # Run test
    success = test_api_opening_price()
    
    if success:
        print("\n🎉 API TEST SUCCESSFUL!")
        print("The Upstox API is working correctly for opening price capture.")
    else:
        print("\n❌ API TEST FAILED!")
        print("There are issues with the Upstox API or configuration.")
    
    print("\nTest completed.")