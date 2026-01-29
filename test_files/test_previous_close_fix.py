#!/usr/bin/env python3
"""
Test script for Previous Close Fix
Tests the historical candle API approach to get accurate previous close prices
"""

import sys
import os
import logging
import requests
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, 'src')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_historical_candle_api():
    """Test the historical candle API for getting previous close"""
    
    print("🧪 Testing Historical Candle API for Previous Close")
    print("=" * 60)
    
    # Import Upstox fetcher
    try:
        from utils.upstox_fetcher import upstox_fetcher
        logger.info("✅ Upstox fetcher imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import upstox_fetcher: {e}")
        return False
    
    # Test symbols
    test_symbols = ['ASHAPURMIN', 'GODREJPROP', 'IIFL', 'BALUFORGE']
    
    print(f"\n📅 Current date: {datetime.now().date()}")
    print(f"📅 Expected previous trading day: {datetime.now().date() - timedelta(days=1)}")
    
    results = {}
    
    for symbol in test_symbols:
        print(f"\n🔍 Testing {symbol}...")
        
        try:
            # Get instrument key
            instrument_key = upstox_fetcher.get_instrument_key(symbol)
            if not instrument_key:
                logger.error(f"❌ No instrument key found for {symbol}")
                results[symbol] = None
                continue
            
            print(f"   Instrument key: {instrument_key}")
            
            # Use the existing fetch_historical_data method which works correctly
            today = datetime.now().date()
            start_date = today - timedelta(days=5)  # Get last 5 days
            end_date = today - timedelta(days=1)    # Up to yesterday
            
            print(f"   Date range: {start_date} to {end_date}")
            
            # Use the existing method that works
            df = upstox_fetcher.fetch_historical_data(symbol, start_date, end_date)
            
            if not df.empty:
                print(f"   ✅ Found {len(df)} days of data")
                
                # Show all available data
                for date_idx, row in df.iterrows():
                    print(f"   Data {date_idx}: O:{row['open']:.2f} H:{row['high']:.2f} L:{row['low']:.2f} C:{row['close']:.2f} V:{row['volume']}")
                
                # Get last close (most recent)
                last_close = float(df.iloc[-1]['close'])
                results[symbol] = last_close
                
                print(f"   ✅ Previous close: ₹{last_close:.2f}")
            else:
                logger.error(f"❌ No historical data found for {symbol}")
                results[symbol] = None
                
        except Exception as e:
            logger.error(f"❌ Error testing {symbol}: {e}")
            results[symbol] = None
    
    # Compare with current LTP method
    print(f"\n📊 Comparison with Current LTP Method")
    print("-" * 40)
    
    for symbol in test_symbols:
        print(f"\n📈 {symbol}:")
        
        # Get current LTP data
        try:
            ltp_data = upstox_fetcher.get_ltp_data(symbol)
            if ltp_data and 'cp' in ltp_data:
                ltp_close = float(ltp_data['cp'])
                print(f"   Current LTP 'cp': ₹{ltp_close:.2f}")
            else:
                print(f"   Current LTP 'cp': Not available")
                ltp_close = None
        except Exception as e:
            print(f"   Current LTP 'cp': Error - {e}")
            ltp_close = None
        
        # Get historical close
        hist_close = results.get(symbol)
        if hist_close:
            print(f"   Historical close: ₹{hist_close:.2f}")
            
            if ltp_close:
                diff = abs(hist_close - ltp_close)
                if diff > 0.01:  # More than 1 paisa difference
                    print(f"   ⚠️  Difference: ₹{diff:.2f} - Historical API gives different result!")
                else:
                    print(f"   ✅ Same result")
            else:
                print(f"   ⚠️  Cannot compare - LTP method failed")
        else:
            print(f"   Historical close: Not available")
    
    # Summary
    print(f"\n📋 Test Summary")
    print("=" * 30)
    
    successful_symbols = [s for s in test_symbols if results.get(s) is not None]
    print(f"✅ Successful: {len(successful_symbols)}/{len(test_symbols)} symbols")
    
    if successful_symbols:
        print(f"   Symbols with historical data: {', '.join(successful_symbols)}")
        
        # Check for discrepancies
        discrepancies = []
        for symbol in successful_symbols:
            ltp_data = upstox_fetcher.get_ltp_data(symbol)
            if ltp_data and 'cp' in ltp_data:
                ltp_close = float(ltp_data['cp'])
                hist_close = results[symbol]
                if abs(hist_close - ltp_close) > 0.01:
                    discrepancies.append(symbol)
        
        if discrepancies:
            print(f"⚠️  Discrepancies found in: {', '.join(discrepancies)}")
            print("   These symbols will benefit from the historical API fix!")
        else:
            print("✅ No discrepancies found - both methods give same results")
    
    return len(successful_symbols) > 0

def test_specific_problem_symbol():
    """Test the specific problem symbol ASHAPURMIN"""
    
    print(f"\n🎯 Testing Specific Problem: ASHAPURMIN")
    print("=" * 50)
    
    symbol = 'ASHAPURMIN'
    
    try:
        from utils.upstox_fetcher import upstox_fetcher
        
        # Current LTP method
        print("Current LTP method:")
        ltp_data = upstox_fetcher.get_ltp_data(symbol)
        if ltp_data and 'cp' in ltp_data:
            ltp_close = float(ltp_data['cp'])
            print(f"   ASHAPURMIN LTP 'cp': ₹{ltp_close:.2f}")
        else:
            print(f"   ASHAPURMIN LTP 'cp': Not available")
            ltp_close = None
        
        # Historical method
        print("\nHistorical method:")
        instrument_key = upstox_fetcher.get_instrument_key(symbol)
        if instrument_key:
            today = datetime.now().date()
            to_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
            from_date = (today - timedelta(days=5)).strftime('%Y-%m-%d')
            
            url = f"https://api.upstox.com/v3/historical-candle/{instrument_key}/1d/{to_date}/{from_date}"
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {upstox_fetcher.access_token}"
            }
            
            response = requests.get(url, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                if response_data.get('data', {}).get('candles'):
                    candles = response_data['data']['candles']
                    last_close = float(candles[0][4])
                    print(f"   ASHAPURMIN Historical close: ₹{last_close:.2f}")
                    
                    if ltp_close:
                        diff = abs(last_close - ltp_close)
                        print(f"   Difference: ₹{diff:.2f}")
                        if diff > 0.01:
                            print("   ✅ Historical API fixes the stale data issue!")
                        else:
                            print("   ✅ Both methods agree")
                else:
                    print("   ❌ No historical data available")
            else:
                print(f"   ❌ Historical API error: {response_data.get('error', 'Unknown error')}")
        else:
            print("   ❌ No instrument key found")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Previous Close Fix Test")
    print("=" * 60)
    
    # Test the historical candle API
    success = test_historical_candle_api()
    
    # Test the specific problem symbol
    test_specific_problem_symbol()
    
    print(f"\n🏁 Test completed")
    if success:
        print("✅ Historical API test successful - ready for implementation")
    else:
        print("❌ Historical API test failed - check token/API access")