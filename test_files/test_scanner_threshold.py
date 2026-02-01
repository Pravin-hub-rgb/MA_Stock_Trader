
#!/usr/bin/env python3
"""
Test script to check what threshold the scanner is actually using
and verify the exact 20 MA logic being applied.
"""

import sys
import os
from datetime import date
import pandas as pd

# Add src to path
sys.path.append('src')

from src.scanner.scanner import scanner
from src.utils.cache_manager import cache_manager
from src.utils.data_fetcher import data_fetcher

def test_actual_scanner_threshold(symbol: str, scan_date: date):
    """Test what threshold the actual scanner is using"""
    print(f"\n{'='*60}")
    print(f"TESTING ACTUAL SCANNER THRESHOLD FOR: {symbol}")
    print(f"{'='*60}")
    
    try:
        # Get the actual scanner parameters
        print(f"\n1. CHECKING SCANNER PARAMETERS:")
        print(f"   Continuation params: {scanner.continuation_params}")
        print(f"   Near MA threshold: {scanner.continuation_params.get('near_ma_threshold', 'NOT SET')}")
        
        # Get cached data and run actual scanner
        print(f"\n2. RUNNING ACTUAL SCANNER:")
        cached_data = cache_manager.load_cached_data(symbol)
        
        if cached_data is None or cached_data.empty:
            print(f"   ❌ No cached data found")
            return None
        
        # Get data for date range
        scanner_data = data_fetcher.get_data_for_date_range(
            symbol,
            None,
            scan_date
        )
        
        if scanner_data.empty:
            print(f"   ❌ Scanner data fetch returned empty")
            return None
        
        # Calculate technical indicators
        scanner_data = data_fetcher.calculate_technical_indicators(scanner_data)
        latest = scanner_data.iloc[-1]
        
        print(f"   📈 Latest data:")
        print(f"      Date: {latest.name}")
        print(f"      Close: {latest['close']:.2f}")
        print(f"      20 MA: {latest['ma_20']:.2f}")
        
        # Calculate distance from MA
        distance_pct = abs(latest['close'] - latest['ma_20']) / latest['close']
        print(f"      Distance from MA: {distance_pct*100:.2f}%")
        
        # Test different thresholds
        print(f"\n3. TESTING DIFFERENT THRESHOLDS:")
        
        thresholds_to_test = [0.05, 0.06, 0.10, 0.15, 0.20, 0.25, 0.30, 0.50]
        
        for threshold in thresholds_to_test:
            # Test the exact logic from continuation_analyzer
            above_ma = latest['close'] > latest['ma_20']
            within_threshold = distance_pct <= threshold
            near_or_above = above_ma and within_threshold
            
            print(f"   Threshold {threshold*100:2.0f}%: Above_MA={above_ma}, Within_Threshold={within_threshold}, Near_or_Above_MA={near_or_above}")
        
        # Test if the issue is with the "OR" logic
        print(f"\n4. TESTING 'NEAR OR ABOVE' LOGIC:")
        print(f"   Current logic: (Close > 20MA) AND (Distance <= Threshold)")
        print(f"   Close > 20MA: {latest['close'] > latest['ma_20']}")
        print(f"   Distance <= 6%: {distance_pct <= 0.06}")
        print(f"   Result: {latest['close'] > latest['ma_20'] and distance_pct <= 0.06}")
        
        print(f"\n   Alternative logic: (Close > 20MA) OR (Distance <= Threshold)")
        print(f"   Close > 20MA: {latest['close'] > latest['ma_20']}")
        print(f"   Distance <= 6%: {distance_pct <= 0.06}")
        print(f"   Result: {latest['close'] > latest['ma_20'] or distance_pct <= 0.06}")
        
        # Test what would make the stock pass
        print(f"\n5. WHAT WOULD MAKE {symbol} PASS:")
        required_threshold = distance_pct
        print(f"   Required threshold for pass: {required_threshold*100:.2f}%")
        
        if latest['close'] < latest['ma_20']:
            print(f"   Current issue: Close ({latest['close']:.2f}) < 20 MA ({latest['ma_20']:.2f})")
            print(f"   Stock is {distance_pct*100:.2f}% below 20 MA")
        
        return {
            'symbol': symbol,
            'close': latest['close'],
            'ma_20': latest['ma_20'],
            'distance_pct': distance_pct * 100,
            'above_ma': latest['close'] > latest['ma_20']
        }
        
    except Exception as e:
        print(f"\n❌ Error testing {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main test function"""
    print("🔍 SCANNER THRESHOLD TEST")
    print("=" * 60)
    
    # Test for 1st Feb 2026
    scan_date = date(2026, 2, 1)
    print(f"Testing scanner threshold for scan date: {scan_date}")
    
    # Test stocks
    test_stocks = ['MMFL', 'TENNIND']
    
    all_results = {}
    
    for symbol in test_stocks:
        result = test_actual_scanner_threshold(symbol, scan_date)
        all_results[symbol] = result
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    for symbol in test_stocks:
        result = all_results[symbol]
        if result is not None:
            print(f"{symbol}:")
            print(f"   Close: {result['close']:.2f}, 20 MA: {result['ma_20']:.2f}")
            print(f"   Distance from MA: {result['distance_pct']:.2f}%")
            print(f"   Above 20 MA: {result['above_ma']}")
            print(f"   Required threshold to pass: {result['distance_pct']:.2f}%")

if __name__ == "__main__":
    main()