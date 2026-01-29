#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Cache Data Mean Volume Calculation
Tests that we can get the 10-day mean volume from cache data
"""

import sys
import os
import logging
import pandas as pd

# Add src to path
sys.path.insert(0, 'src')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def test_cache_mean_volume():
    """Test getting mean volume from cache data"""
    print("CACHE DATA MEAN VOLUME TEST")
    print("=" * 40)
    print(f"Starting at: {pd.Timestamp.now().strftime('%H:%M:%S')}")
    print()
    
    # Test stock
    test_symbol = "RELIANCE"
    cache_file = os.path.join('data', 'cache', f'{test_symbol}.pkl')
    
    print(f"Testing cache file: {cache_file}")
    print(f"File exists: {os.path.exists(cache_file)}")
    
    if not os.path.exists(cache_file):
        print("❌ Cache file does not exist")
        return False
    
    try:
        # Load cache data
        import pickle
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        print(f"Cache data type: {type(cache_data)}")
        print(f"Cache data shape: {cache_data.shape if hasattr(cache_data, 'shape') else 'N/A'}")
        print(f"Cache data columns: {list(cache_data.columns) if hasattr(cache_data, 'columns') else 'N/A'}")
        print()
        
        # Check if volume column exists
        volume_columns = [col for col in cache_data.columns if 'volume' in col.lower()]
        print(f"Volume columns found: {volume_columns}")
        
        if not volume_columns:
            print("❌ No volume column found in cache data")
            return False
        
        # Get the main volume column (usually just 'volume')
        volume_col = volume_columns[0]
        print(f"Using volume column: {volume_col}")
        print()
        
        # Calculate 10-day mean volume
        if len(cache_data) >= 10:
            recent_data = cache_data.tail(10)
            mean_volume = recent_data[volume_col].mean()
            print(f"10-day mean volume: {mean_volume:,.0f} shares")
            print(f"7.5% threshold: {mean_volume * 0.075:,.0f} shares")
            print()
            
            # Show recent volume data
            print("Recent volume data (last 10 days):")
            for i, (date, row) in enumerate(recent_data.iterrows()):
                volume = row[volume_col]
                print(f"  {date.strftime('%Y-%m-%d')}: {volume:,.0f} shares")
            
            print()
            print("✅ Cache mean volume calculation successful")
            return True
        else:
            print(f"❌ Not enough data: only {len(cache_data)} days available, need 10")
            return False
            
    except Exception as e:
        print(f"❌ Error loading cache data: {e}")
        return False

def test_multiple_stocks_cache():
    """Test cache data for multiple stocks"""
    print("\nMULTIPLE STOCKS CACHE TEST")
    print("=" * 40)
    
    test_symbols = ["RELIANCE", "TATASTEEL", "INFY", "HDFCBANK"]
    results = {}
    
    for symbol in test_symbols:
        cache_file = os.path.join('data', 'cache', f'{symbol}.pkl')
        
        if os.path.exists(cache_file):
            try:
                import pickle
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                if hasattr(cache_data, 'shape') and len(cache_data) >= 10:
                    volume_columns = [col for col in cache_data.columns if 'volume' in col.lower()]
                    if volume_columns:
                        volume_col = volume_columns[0]
                        mean_volume = cache_data.tail(10)[volume_col].mean()
                        results[symbol] = {
                            'mean_volume': mean_volume,
                            'days_available': len(cache_data),
                            'threshold_7_5pct': mean_volume * 0.075
                        }
                        print(f"✅ {symbol}: Mean volume = {mean_volume:,.0f}, 7.5% threshold = {mean_volume * 0.075:,.0f}")
                    else:
                        print(f"❌ {symbol}: No volume column found")
                else:
                    print(f"❌ {symbol}: Insufficient data ({len(cache_data)} days)")
            except Exception as e:
                print(f"❌ {symbol}: Error - {e}")
        else:
            print(f"❌ {symbol}: Cache file not found")
    
    print(f"\nSummary: {len(results)} stocks have valid cache data")
    return results

def main():
    """Main test function"""
    print("Starting Cache Data Mean Volume Test")
    print("This test verifies we can get 10-day mean volume from cache data")
    print("for SVRO volume validation")
    print()
    
    # Test single stock
    single_result = test_cache_mean_volume()
    
    # Test multiple stocks
    multi_results = test_multiple_stocks_cache()
    
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    print(f"Single stock test: {'✅ PASS' if single_result else '❌ FAIL'}")
    print(f"Multiple stocks test: {len(multi_results)} stocks with valid data")
    
    if multi_results:
        print("\nValid cache data found for SVRO volume validation:")
        for symbol, data in multi_results.items():
            print(f"  {symbol}: Mean volume = {data['mean_volume']:,.0f} shares")
            print(f"           7.5% threshold = {data['threshold_7_5pct']:,.0f} shares")
            print(f"           Days available = {data['days_available']}")
    
    return single_result and len(multi_results) > 0

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Cache data test completed successfully")
    else:
        print("\n❌ Cache data test failed")