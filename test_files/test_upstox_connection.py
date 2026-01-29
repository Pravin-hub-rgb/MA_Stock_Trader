#!/usr/bin/env python3
"""
Test Upstox Connection and LTP Fetching
Verifies that access token works and can fetch real-time data for continuation stocks
"""

import sys
import os
import json
from datetime import datetime
import pytz

# Add src to path for imports
sys.path.append('src')

from utils.upstox_fetcher import UpstoxFetcher

# Setup IST timezone
IST = pytz.timezone('Asia/Kolkata')

def load_continuation_stocks():
    """Load stocks from continuation_list.txt"""
    try:
        with open('src/trading/continuation_list.txt', 'r') as f:
            content = f.read().strip()
            if not content:
                print("❌ continuation_list.txt is empty")
                return []

            symbols = [s.strip() for s in content.split(',') if s.strip()]
            print(f"📋 Loaded {len(symbols)} stocks: {symbols}")
            return symbols

    except FileNotFoundError:
        print("❌ continuation_list.txt not found")
        return []
    except Exception as e:
        print(f"❌ Error loading continuation stocks: {e}")
        return []

def test_connection():
    """Test basic Upstox connection"""
    print("🔌 Testing Upstox connection...")

    try:
        fetcher = UpstoxFetcher()

        # Try to get profile (tests API key and access token)
        profile_response = fetcher.user_api.get_profile(api_version='2.0')
        email = profile_response.data.email
        print(f"✅ Connected to Upstox account: {email}")

        return True, fetcher

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False, None

def test_instrument_keys(fetcher, symbols):
    """Test instrument key resolution"""
    print("\n🔑 Testing instrument key resolution...")

    results = {}
    for symbol in symbols:
        try:
            instrument_key = fetcher.get_instrument_key(symbol)
            if instrument_key and 'NSE_EQ' in instrument_key:
                print(f"✅ {symbol} → {instrument_key}")
                results[symbol] = {'instrument_key': instrument_key, 'status': 'success'}
            else:
                print(f"❌ {symbol} → No valid instrument key found")
                results[symbol] = {'instrument_key': None, 'status': 'no_key'}

        except Exception as e:
            print(f"❌ {symbol} → Error: {e}")
            results[symbol] = {'instrument_key': None, 'status': 'error', 'error': str(e)}

    return results

def test_ltp_fetch(fetcher, instrument_results):
    """Test LTP fetching for stocks with valid instrument keys"""
    print("\n💰 Testing LTP fetch...")

    ltp_results = {}

    # Filter to only stocks with valid instrument keys
    valid_stocks = {symbol: data for symbol, data in instrument_results.items()
                   if data['status'] == 'success'}

    if not valid_stocks:
        print("❌ No valid instrument keys to test LTP")
        return {}

    for symbol, data in valid_stocks.items():
        try:
            instrument_key = data['instrument_key']

            # Try to fetch latest data (this will get yesterday's close, but tests API)
            latest_data = fetcher.get_latest_data(symbol)

            if latest_data and 'close' in latest_data:
                prev_close = latest_data['close']
                print(f"✅ {symbol} → Previous close: ₹{prev_close:.2f}")
                ltp_results[symbol] = {
                    'status': 'success',
                    'prev_close': prev_close,
                    'date': latest_data.get('date')
                }
            else:
                print(f"❌ {symbol} → No data received")
                ltp_results[symbol] = {'status': 'no_data'}

        except Exception as e:
            print(f"❌ {symbol} → LTP fetch error: {e}")
            ltp_results[symbol] = {'status': 'error', 'error': str(e)}

    return ltp_results

def main():
    """Main test function"""
    print("🧪 UPSTOX CONNECTION TEST")
    print("=" * 50)
    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()

    # Load continuation stocks
    symbols = load_continuation_stocks()
    if not symbols:
        print("❌ No stocks to test")
        return 1

    # Test connection
    connection_ok, fetcher = test_connection()
    if not connection_ok:
        return 1

    # Test instrument keys
    instrument_results = test_instrument_keys(fetcher, symbols)

    # Test LTP fetch
    ltp_results = test_ltp_fetch(fetcher, instrument_results)

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")

    total_stocks = len(symbols)
    valid_keys = sum(1 for r in instrument_results.values() if r['status'] == 'success')
    successful_ltp = sum(1 for r in ltp_results.values() if r['status'] == 'success')

    print(f"Total stocks: {total_stocks}")
    print(f"Valid instrument keys: {valid_keys}")
    print(f"Successful LTP fetches: {successful_ltp}")

    if valid_keys == total_stocks and successful_ltp == valid_keys:
        print("🎉 ALL TESTS PASSED - Upstox connection is working!")
        return 0
    else:
        print("⚠️ Some tests failed - check the output above")
        return 1

if __name__ == "__main__":
    sys.exit(main())