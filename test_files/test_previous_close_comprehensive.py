#!/usr/bin/env python3
"""
Comprehensive test for Previous Close Bug
Tests various scenarios where the LTP API might return stale data
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

def test_ltp_vs_historical():
    """Test LTP vs Historical for potential discrepancies"""
    
    print("🔍 Comprehensive Previous Close Test")
    print("=" * 50)
    
    try:
        from utils.upstox_fetcher import upstox_fetcher
        logger.info("✅ Upstox fetcher imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import upstox_fetcher: {e}")
        return False
    
    # Test symbols from the bug report
    test_symbols = ['ASHAPURMIN', 'GODREJPROP', 'IIFL', 'BALUFORGE', 'BHEL', 'DEVYANI']
    
    print(f"\n📅 Current date: {datetime.now().date()}")
    print(f"📅 Current time: {datetime.now().strftime('%H:%M:%S')}")
    
    results = {}
    
    for symbol in test_symbols:
        print(f"\n🧪 Testing {symbol}...")
        
        try:
            # 1. Get LTP data
            ltp_data = upstox_fetcher.get_ltp_data(symbol)
            if ltp_data and 'cp' in ltp_data:
                ltp_close = float(ltp_data['cp'])
                print(f"   LTP 'cp': ₹{ltp_close:.2f}")
            else:
                print(f"   LTP 'cp': Not available")
                ltp_close = None
            
            # 2. Get historical data (last 3 days to see the pattern)
            today = datetime.now().date()
            start_date = today - timedelta(days=3)
            end_date = today - timedelta(days=1)
            
            df = upstox_fetcher.fetch_historical_data(symbol, start_date, end_date)
            
            if not df.empty:
                print(f"   Historical data found: {len(df)} days")
                
                # Show all historical closes
                for date_idx, row in df.iterrows():
                    print(f"   {date_idx}: Close ₹{row['close']:.2f}")
                
                # Get most recent close
                hist_close = float(df.iloc[-1]['close'])
                print(f"   Historical close: ₹{hist_close:.2f}")
                
                # Compare
                if ltp_close:
                    diff = abs(hist_close - ltp_close)
                    if diff > 0.01:
                        print(f"   ⚠️  DISCREPANCY: ₹{diff:.2f}")
                        results[symbol] = {
                            'ltp': ltp_close,
                            'historical': hist_close,
                            'discrepancy': diff,
                            'status': 'DISCREPANCY'
                        }
                    else:
                        print(f"   ✅ MATCH")
                        results[symbol] = {
                            'ltp': ltp_close,
                            'historical': hist_close,
                            'discrepancy': diff,
                            'status': 'MATCH'
                        }
                else:
                    results[symbol] = {
                        'ltp': None,
                        'historical': hist_close,
                        'discrepancy': None,
                        'status': 'LTP_FAILED'
                    }
            else:
                print(f"   ❌ No historical data")
                results[symbol] = {
                    'ltp': ltp_close,
                    'historical': None,
                    'discrepancy': None,
                    'status': 'HISTORICAL_FAILED'
                }
                
        except Exception as e:
            logger.error(f"❌ Error testing {symbol}: {e}")
            results[symbol] = {
                'ltp': None,
                'historical': None,
                'discrepancy': None,
                'status': 'ERROR'
            }
    
    # Summary
    print(f"\n📋 Comprehensive Test Summary")
    print("=" * 40)
    
    discrepancies = [s for s, r in results.items() if r['status'] == 'DISCREPANCY']
    matches = [s for s, r in results.items() if r['status'] == 'MATCH']
    ltp_failed = [s for s, r in results.items() if r['status'] == 'LTP_FAILED']
    historical_failed = [s for s, r in results.items() if r['status'] == 'HISTORICAL_FAILED']
    errors = [s for s, r in results.items() if r['status'] == 'ERROR']
    
    print(f"✅ Matches: {len(matches)} - {', '.join(matches) if matches else 'None'}")
    print(f"⚠️  Discrepancies: {len(discrepancies)} - {', '.join(discrepancies) if discrepancies else 'None'}")
    print(f"❌ LTP Failed: {len(ltp_failed)} - {', '.join(ltp_failed) if ltp_failed else 'None'}")
    print(f"❌ Historical Failed: {len(historical_failed)} - {', '.join(historical_failed) if historical_failed else 'None'}")
    print(f"❌ Errors: {len(errors)} - {', '.join(errors) if errors else 'None'}")
    
    if discrepancies:
        print(f"\n🔍 Discrepancy Details:")
        for symbol in discrepancies:
            r = results[symbol]
            print(f"   {symbol}: LTP={r['ltp']:.2f}, Historical={r['historical']:.2f}, Diff={r['discrepancy']:.2f}")
    
    return len(discrepancies) == 0

def test_api_endpoints():
    """Test different API endpoints to see which one has issues"""
    
    print(f"\n🌐 Testing Different API Endpoints")
    print("=" * 40)
    
    symbol = 'ASHAPURMIN'
    
    try:
        from utils.upstox_fetcher import upstox_fetcher
        
        instrument_key = upstox_fetcher.get_instrument_key(symbol)
        print(f"Symbol: {symbol}")
        print(f"Instrument Key: {instrument_key}")
        
        # Test 1: LTP API (current method)
        print(f"\n1️⃣ LTP API (current method):")
        ltp_data = upstox_fetcher.get_ltp_data(symbol)
        if ltp_data and 'cp' in ltp_data:
            print(f"   Previous close: ₹{ltp_data['cp']:.2f}")
            print(f"   LTP: ₹{ltp_data['ltp']:.2f}")
        else:
            print(f"   ❌ Failed")
        
        # Test 2: Historical API (proposed fix)
        print(f"\n2️⃣ Historical API (proposed fix):")
        today = datetime.now().date()
        start_date = today - timedelta(days=3)
        end_date = today - timedelta(days=1)
        
        df = upstox_fetcher.fetch_historical_data(symbol, start_date, end_date)
        if not df.empty:
            latest_close = float(df.iloc[-1]['close'])
            print(f"   Previous close: ₹{latest_close:.2f}")
            print(f"   Data source: {df.index[-1]}")
        else:
            print(f"   ❌ Failed")
        
        # Test 3: Direct HTTP LTP (fallback method)
        print(f"\n3️⃣ Direct HTTP LTP (fallback):")
        fallback_data = upstox_fetcher._get_ltp_data_fallback(symbol)
        if fallback_data and 'cp' in fallback_data:
            print(f"   Previous close: ₹{fallback_data['cp']:.2f}")
        else:
            print(f"   ❌ Failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Previous Close Test")
    print("=" * 60)
    
    # Run comprehensive test
    success = test_ltp_vs_historical()
    
    # Test different endpoints
    test_api_endpoints()
    
    print(f"\n🏁 Comprehensive test completed")
    if success:
        print("✅ No discrepancies found - LTP API is working correctly")
    else:
        print("⚠️  Discrepancies found - historical API fix may be needed")