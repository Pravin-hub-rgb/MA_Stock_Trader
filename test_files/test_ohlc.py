#!/usr/bin/env python3
"""
Simple test script to check OHLC API responses during live market
"""

import sys
import os
sys.path.append('src')

from src.utils.upstox_fetcher import UpstoxFetcher
import json

def test_ohlc_api():
    """Test OHLC API with different stocks"""
    print("=== TESTING OHLC API ===")

    upstox_fetcher = UpstoxFetcher()

    # Test stocks
    test_stocks = ['BLISSGVS', 'CUPID', 'GRAPHITE']

    print(f"Testing with stocks: {test_stocks}")
    print()

    # Test 1: Individual stock calls
    print("=== TEST 1: Individual Stock Calls ===")
    for stock in test_stocks:
        print(f"\n--- Testing {stock} ---")
        try:
            result = upstox_fetcher.get_ohlc_data(stock)
            print(f"get_ohlc_data({stock}) result: {result}")
        except Exception as e:
            print(f"Error for {stock}: {e}")

    # Test 2: Batch API call with I1 interval (1-minute candles)
    print("\n=== TEST 2: Batch API Call (I1 - 1 Minute Candles) ===")
    print(f"Calling get_current_ohlc with I1 interval...")

    # Temporarily modify the URL to use I1 instead of 1d
    original_url = f"https://api.upstox.com/v3/market-quote/ohlc?instrument_key={{}}&interval=1d"
    test_url = f"https://api.upstox.com/v3/market-quote/ohlc?instrument_key={{}}&interval=I1"

    try:
        # Test with I1 interval
        import requests
        keys = [upstox_fetcher.get_instrument_key(stock) for stock in test_stocks]
        keys = [k for k in keys if k]  # Filter None values

        url = test_url.format(','.join(keys))
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {upstox_fetcher.access_token}"
        }

        print(f"Testing I1 URL: {url}")
        response = requests.get(url, headers=headers)
        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")

            if data.get('status') == 'success':
                ohlc_data = data.get('data', {})
                for key, instrument_data in ohlc_data.items():
                    print(f"\n{key}:")
                    live_ohlc = instrument_data.get('live_ohlc', {})
                    if live_ohlc:
                        print(f"  live_ohlc: {live_ohlc}")
                    ohlc_list = instrument_data.get('ohlc', [])
                    if ohlc_list:
                        print(f"  ohlc candles: {len(ohlc_list)}")
                        for i, candle in enumerate(ohlc_list[:3]):  # Show first 3 candles
                            print(f"    Candle {i}: {candle}")
        else:
            print(f"API Error: {response.text}")

    except Exception as e:
        print(f"Test error: {e}")

    # Test 3: LTP API for comparison
    print("\n=== TEST 3: LTP API for Comparison ===")
    for stock in test_stocks[:1]:  # Just test one
        print(f"\n--- LTP for {stock} ---")
        try:
            ltp_result = upstox_fetcher.get_ltp_data(stock)
            print(f"get_ltp_data({stock}) result: {ltp_result}")
        except Exception as e:
            print(f"LTP error for {stock}: {e}")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_ohlc_api()
