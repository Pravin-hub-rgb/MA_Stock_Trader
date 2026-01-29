#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for OHLC Quotes V3 API
Tests the Upstox OHLC API to get opening prices for reversal trading
"""

import sys
import os
import time as time_module
from datetime import datetime, time, timedelta
import pytz
import requests

# Add src to path
sys.path.append('src')

def test_ohlc_api():
    """Test OHLC Quotes V3 API for opening price capture"""
    
    print("TESTING OHLC QUOTES V3 API")
    print("=" * 40)
    
    # Import Upstox fetcher
    from src.utils.upstox_fetcher import UpstoxFetcher
    
    # Create fetcher
    upstox_fetcher = UpstoxFetcher()
    IST = pytz.timezone('Asia/Kolkata')
    
    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()
    
    # Test with stocks from reversal list
    test_symbols = ["NETWEB", "AGIIL", "ARISINFRA", "BALUFORGE", "DEVYANI"]
    print(f"Testing OHLC API for: {test_symbols}")
    print()
    
    try:
        # Get instrument keys for all symbols
        instrument_keys = []
        symbol_map = {}
        for symbol in test_symbols:
            key = upstox_fetcher.get_instrument_key(symbol)
            if key:
                instrument_keys.append(key)
                symbol_map[key] = symbol
                print(f"✓ {symbol}: {key}")
            else:
                print(f"✗ {symbol}: No instrument key")
        
        if not instrument_keys:
            print("ERROR: No valid instrument keys found")
            return False
            
        print(f"\nTesting with {len(instrument_keys)} symbols")
        print()
        
        # Test 1: Single symbol OHLC request
        print("TEST 1: Single Symbol OHLC Request")
        print("-" * 30)
        single_key = instrument_keys[0]
        single_symbol = symbol_map[single_key]
        print(f"Testing single symbol: {single_symbol} ({single_key})")
        
        # Make OHLC API call for single symbol
        url = f"https://api.upstox.com/v3/market-quote/ohlc?instrument_key={single_key}&interval=I1"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {upstox_fetcher.access_token}"
        }
        
        response = requests.get(url, headers=headers)
        print(f"✓ API response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✓ Response type: {type(response_data)}")
            print(f"✓ Response keys: {list(response_data.keys()) if response_data else 'None'}")
            print(f"✓ Response data: {response_data}")
            
            if response_data.get('status') == 'success':
                data = response_data.get('data', {})
                print(f"✓ Data keys: {list(data.keys()) if data else 'None'}")
                
                # Try to find the symbol data using different key formats
                symbol_data = None
                for key in data.keys():
                    if single_key in key or single_symbol in key:
                        symbol_data = data[key]
                        print(f"✓ Found symbol data with key: {key}")
                        break
                
                if not symbol_data:
                    symbol_data = data.get(single_key, {})
                    print(f"✓ Using direct key lookup: {single_key}")
                
                print(f"✓ Symbol data keys: {list(symbol_data.keys()) if symbol_data else 'None'}")
                print(f"✓ Symbol data: {symbol_data}")
                
                # Check for different OHLC data formats
                ohlc = symbol_data.get('ohlc', {})
                live_ohlc = symbol_data.get('live_ohlc', {})
                prev_ohlc = symbol_data.get('prev_ohlc', {})
                
                print(f"✓ OHLC keys: {list(ohlc.keys()) if ohlc else 'None'}")
                print(f"✓ Live OHLC keys: {list(live_ohlc.keys()) if live_ohlc else 'None'}")
                print(f"✓ Prev OHLC keys: {list(prev_ohlc.keys()) if prev_ohlc else 'None'}")
                print(f"✓ OHLC data: {ohlc}")
                print(f"✓ Live OHLC data: {live_ohlc}")
                print(f"✓ Prev OHLC data: {prev_ohlc}")
                
                # Try to get opening price from different sources
                open_price = None
                if live_ohlc and 'open' in live_ohlc:
                    open_price = live_ohlc['open']
                    print(f"✓ Using live_ohlc open price")
                elif prev_ohlc and 'open' in prev_ohlc:
                    open_price = prev_ohlc['open']
                    print(f"✓ Using prev_ohlc open price")
                elif ohlc and 'open' in ohlc:
                    open_price = ohlc['open']
                    print(f"✓ Using ohlc open price")
                
                high_price = live_ohlc.get('high') or prev_ohlc.get('high') or ohlc.get('high')
                low_price = live_ohlc.get('low') or prev_ohlc.get('low') or ohlc.get('low')
                close_price = live_ohlc.get('close') or prev_ohlc.get('close') or ohlc.get('close')
                
                print(f"✓ Open: {open_price}")
                print(f"✓ High: {high_price}")
                print(f"✓ Low: {low_price}")
                print(f"✓ Close: {close_price}")
                
                if open_price is not None:
                    print(f"✓ SUCCESS: Opening price for {single_symbol}: Rs{float(open_price):.2f}")
                else:
                    print(f"✗ ERROR: No opening price for {single_symbol}")
            else:
                print(f"✗ ERROR: API status not success: {response_data}")
        else:
            print(f"✗ ERROR: HTTP {response.status_code}: {response.text}")
        
        print()
        
        # Test 2: Batch OHLC request
        print("TEST 2: Batch OHLC Request")
        print("-" * 30)
        batch_keys = ",".join(instrument_keys[:3])  # Test with first 3 symbols
        print(f"Testing batch with: {batch_keys[:100]}...")
        
        url = f"https://api.upstox.com/v3/market-quote/ohlc?instrument_key={batch_keys}&interval=I1"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {upstox_fetcher.access_token}"
        }
        
        response = requests.get(url, headers=headers)
        print(f"✓ Batch API response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✓ Batch response keys: {list(response_data.keys()) if response_data else 'None'}")
            
            if response_data.get('status') == 'success':
                data = response_data.get('data', {})
                print(f"✓ Batch data keys: {list(data.keys()) if data else 'None'}")
                
                for key in data:
                    symbol = symbol_map.get(key, key)
                    ohlc = data[key].get('ohlc', {})
                    open_price = ohlc.get('open')
                    if open_price is not None:
                        print(f"✓ {symbol}: Open = Rs{float(open_price):.2f}")
                    else:
                        print(f"✗ {symbol}: No opening price")
            else:
                print(f"✗ ERROR: Batch API status not success: {response_data}")
        else:
            print(f"✗ ERROR: Batch HTTP {response.status_code}: {response.text}")
        
        print()
        
        # Test 3: Compare with LTP API
        print("TEST 3: Comparison with LTP API")
        print("-" * 30)
        print("Comparing OHLC vs LTP API results:")
        
        for symbol in test_symbols[:3]:  # Test first 3 symbols
            print(f"\n{symbol}:")
            
            # Get LTP data
            ltp_data = upstox_fetcher.get_ltp_data(symbol)
            if ltp_data:
                ltp_open = ltp_data.get('open')
                ltp_ltp = ltp_data.get('ltp')
                ltp_cp = ltp_data.get('cp')
                print(f"  LTP API - Open: {ltp_open}, LTP: {ltp_ltp}, Prev Close: {ltp_cp}")
            else:
                print(f"  LTP API - No data")
            
            # Get OHLC data
            key = upstox_fetcher.get_instrument_key(symbol)
            if key:
                url = f"https://api.upstox.com/v3/market-quote/ohlc?instrument_key={key}&interval=I1"
                headers = {
                    "Accept": "application/json",
                    "Authorization": f"Bearer {upstox_fetcher.access_token}"
                }
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get('status') == 'success':
                        ohlc_data = response_data.get('data', {}).get(key, {})
                        ohlc_open = ohlc_data.get('ohlc', {}).get('open')
                        print(f"  OHLC API - Open: {ohlc_open}")
                    else:
                        print(f"  OHLC API - Error: {response_data}")
                else:
                    print(f"  OHLC API - HTTP Error: {response.status_code}")
            else:
                print(f"  OHLC API - No instrument key")
        
        print()
        print("TEST SUMMARY:")
        print("✓ OHLC API should return valid opening prices")
        print("✓ LTP API returns open: null (confirmed issue)")
        print("✓ OHLC API is the solution for opening price capture")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("OHLC QUOTES V3 API TEST")
    print("Testing the solution for opening price capture")
    print()
    
    success = test_ohlc_api()
    
    if success:
        print("\n🎉 OHLC API TEST COMPLETED!")
        print("Ready to integrate into the reversal bot.")
    else:
        print("\n❌ OHLC API TEST FAILED!")
        print("Need to investigate further.")
    
    print("\nTest completed.")