#!/usr/bin/env python3
"""
Test script to fetch previous close from cache (scanner cache)
Tests the bhavcopy_cache system for getting previous close prices
"""

import sys
import os
import logging
import pandas as pd
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, 'src')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_cache_previous_close():
    """Test fetching previous close from pickle cache"""
    
    print("🔍 Testing Previous Close from Pickle Cache")
    print("=" * 50)
    
    # Test symbols
    test_symbols = ['ASHAPURMIN', 'GODREJPROP', 'IIFL', 'BALUFORGE', 'BHEL', 'DEVYANI']
    
    results = {}
    
    for symbol in test_symbols:
        print(f"\n🧪 Testing {symbol}...")
        
        try:
            # Build cache file path (pickle files in data/cache/)
            cache_file = os.path.join('data', 'cache', f'{symbol}.pkl')
            
            if not os.path.exists(cache_file):
                print(f"   ❌ Cache file not found: {cache_file}")
                results[symbol] = None
                continue
            
            print(f"   Cache file: {cache_file}")
            
            # Read the pickle file
            import pickle
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            if cache_data.empty:
                print(f"   ❌ Empty cache file")
                results[symbol] = None
                continue
            
            print(f"   ✅ Cache loaded: {len(cache_data)} rows")
            
            # Check if cache data has the expected structure
            if isinstance(cache_data, dict):
                # If it's a dict, it might be metadata
                print(f"   Cache type: Dictionary")
                print(f"   Keys: {list(cache_data.keys())}")
                
                # Look for close price in metadata
                if 'prev_close' in cache_data:
                    prev_close = cache_data['prev_close']
                    print(f"   Previous close: ₹{prev_close:.2f}")
                    results[symbol] = {
                        'previous_close': prev_close,
                        'status': 'SUCCESS',
                        'source': 'metadata'
                    }
                else:
                    print(f"   ❌ No previous close in metadata")
                    results[symbol] = None
                    
            elif isinstance(cache_data, pd.DataFrame):
                # If it's a DataFrame, get the latest close
                print(f"   Cache type: DataFrame")
                
                # Sort by date to ensure we get the latest
                if 'date' in cache_data.columns:
                    cache_data = cache_data.sort_values('date', ascending=False)
                else:
                    cache_data = cache_data.iloc[::-1]  # Reverse order
                
                # Get the most recent data
                latest_data = cache_data.iloc[0]
                
                if 'close' in cache_data.columns:
                    latest_close = latest_data['close']
                    print(f"   Previous close: ₹{latest_close:.2f}")
                    
                    # Show a few more recent dates for context
                    print(f"   Recent closes:")
                    for i, row in cache_data.head(3).iterrows():
                        date_str = row.get('date', 'N/A')
                        close_val = row['close']
                        print(f"     {date_str}: ₹{close_val:.2f}")
                    
                    results[symbol] = {
                        'previous_close': latest_close,
                        'status': 'SUCCESS',
                        'source': 'dataframe'
                    }
                else:
                    print(f"   ❌ No close column in DataFrame")
                    results[symbol] = None
            else:
                print(f"   ❌ Unknown cache data type: {type(cache_data)}")
                results[symbol] = None
            
        except Exception as e:
            logger.error(f"❌ Error testing {symbol}: {e}")
            results[symbol] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    # Summary
    print(f"\n📋 Cache Test Summary")
    print("=" * 30)
    
    successful = [s for s, r in results.items() if r and r.get('status') == 'SUCCESS']
    failed = [s for s, r in results.items() if r and r.get('status') == 'ERROR']
    not_found = [s for s, r in results.items() if r is None]
    
    print(f"✅ Successful: {len(successful)} - {', '.join(successful) if successful else 'None'}")
    print(f"❌ Failed: {len(failed)} - {', '.join(failed) if failed else 'None'}")
    print(f"❌ Not found: {len(not_found)} - {', '.join(not_found) if not_found else 'None'}")
    
    if successful:
        print(f"\n🎯 Cache Previous Close Results:")
        for symbol in successful:
            r = results[symbol]
            print(f"   {symbol}: ₹{r['previous_close']:.2f} (from {r['source']})")
    
    return len(successful) > 0

def test_cache_vs_upstox():
    """Compare cache previous close with Upstox LTP data"""
    
    print(f"\n📊 Comparing Cache vs Upstox Previous Close")
    print("=" * 50)
    
    try:
        from utils.upstox_fetcher import upstox_fetcher
        
        test_symbols = ['ASHAPURMIN', 'GODREJPROP', 'IIFL', 'BALUFORGE']
        
        for symbol in test_symbols:
            print(f"\n📈 {symbol}:")
            
            # Get cache data
            cache_file = os.path.join('bhavcopy_cache', f'{symbol.lower()}_daily.csv')
            cache_close = None
            
            if os.path.exists(cache_file):
                try:
                    df = pd.read_csv(cache_file, parse_dates=['date'])
                    if not df.empty:
                        df = df.sort_values('date', ascending=False)
                        cache_close = float(df.iloc[0]['close'])
                        print(f"   Cache close: ₹{cache_close:.2f}")
                except Exception as e:
                    print(f"   Cache error: {e}")
            
            # Get Upstox LTP data
            ltp_close = None
            try:
                ltp_data = upstox_fetcher.get_ltp_data(symbol)
                if ltp_data and 'cp' in ltp_data:
                    ltp_close = float(ltp_data['cp'])
                    print(f"   Upstox close: ₹{ltp_close:.2f}")
            except Exception as e:
                print(f"   Upstox error: {e}")
            
            # Compare
            if cache_close and ltp_close:
                diff = abs(cache_close - ltp_close)
                if diff > 0.01:
                    print(f"   ⚠️  Difference: ₹{diff:.2f}")
                else:
                    print(f"   ✅ Match")
            elif cache_close:
                print(f"   ⚠️  Only cache available")
            elif ltp_close:
                print(f"   ⚠️  Only Upstox available")
            else:
                print(f"   ❌ No data available")
                
    except ImportError as e:
        print(f"❌ Could not import upstox_fetcher: {e}")

def main():
    """Main execution function"""
    print("🚀 Cache Previous Close Test")
    print("=" * 60)
    
    # Test 1: Basic cache functionality
    success = test_cache_previous_close()
    
    # Test 2: Compare with Upstox
    test_cache_vs_upstox()
    
    # Save results
    if success:
        print(f"\n✅ Cache test successful - ready for implementation")
    else:
        print(f"\n❌ Cache test failed - check cache files")
    
    print(f"\n🏁 Test completed")

if __name__ == "__main__":
    main()