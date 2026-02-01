#!/usr/bin/env python3
"""
Test to identify the exact date issue causing MMFL and TENNIND to appear
in results when they should be filtered out.
"""

import sys
import os
from datetime import date, datetime
import pandas as pd

# Add src to path
sys.path.append('src')

from src.scanner.scanner import scanner
from src.utils.data_fetcher import data_fetcher

def test_different_dates():
    """Test the scanner with different dates to see when MMFL/TENNIND appear"""
    print("🔍 TESTING DIFFERENT DATES")
    print("=" * 60)
    
    # Test dates
    test_dates = [
        date(2026, 1, 30),  # Friday before 1st Feb
        date(2026, 2, 1),   # Saturday (non-trading)
        date(2026, 2, 2),   # Sunday (non-trading)
        date(2026, 2, 3),   # Monday
    ]
    
    # Apply frontend parameters
    scanner.update_price_filters(100, 10000)
    scanner.update_near_ma_threshold(6)
    scanner.update_max_body_percentage(4)
    
    target_stocks = ['MMFL', 'TENNIND']
    
    for test_date in test_dates:
        print(f"\n{'='*20} TESTING DATE: {test_date} {'='*20}")
        
        try:
            # Test each target stock individually
            for symbol in target_stocks:
                print(f"\n--- {symbol} on {test_date} ---")
                
                # Get data for this specific date
                data = data_fetcher.get_data_for_date_range(
                    symbol,
                    test_date - pd.Timedelta(days=100),
                    test_date
                )
                
                if data.empty:
                    print(f"   ❌ No data for {symbol}")
                    continue
                
                # Calculate technical indicators
                data = data_fetcher.calculate_technical_indicators(data)
                latest = data.iloc[-1]
                
                # Check if the date exists in the data
                target_timestamp = pd.Timestamp(test_date)
                has_date = target_timestamp in data.index
                
                if not has_date:
                    print(f"   ❌ Date {test_date} not found in data")
                    continue
                
                # Get the row for the specific date
                date_row = data.loc[target_timestamp]
                
                print(f"   Close: {date_row['close']:.2f}")
                print(f"   SMA20: {date_row['ma_20']:.2f}")
                print(f"   Above MA: {date_row['close'] > date_row['ma_20']}")
                
                if date_row['close'] > date_row['ma_20']:
                    dist_pct = (date_row['close'] - date_row['ma_20']) / date_row['ma_20'] * 100
                    print(f"   Distance: +{dist_pct:.2f}%")
                else:
                    dist_pct = (date_row['ma_20'] - date_row['close']) / date_row['ma_20'] * 100
                    print(f"   Distance: -{dist_pct:.2f}%")
                
                # Check if this stock would pass the scanner
                close_above_ma = date_row['close'] > date_row['ma_20']
                dist_to_ma_pct = abs(date_row['close'] - date_row['ma_20']) / date_row['close']
                near_or_above_ma = close_above_ma and (dist_to_ma_pct <= 0.06)  # 6% threshold
                
                print(f"   Would pass scanner: {near_or_above_ma}")
                
        except Exception as e:
            print(f"   ❌ Error testing {symbol}: {e}")

def test_scanner_auto_date():
    """Test what date the scanner automatically detects"""
    print("\n" + "="*60)
    print("🔍 TESTING SCANNER AUTO-DATE DETECTION")
    print("=" * 60)
    
    try:
        # Run scanner to see what date it uses
        print("Running scanner to see auto-detected date...")
        
        # Create a custom progress callback to capture the date
        detected_date = None
        
        def progress_callback(value, message):
            nonlocal detected_date
            if message.startswith("SCAN_DATE:"):
                detected_date = message.split(":", 1)[1]
                print(f"   📅 Scanner detected date: {detected_date}")
        
        results = scanner.run_continuation_scan(
            scan_date=None,  # Auto-detect
            progress_callback=progress_callback
        )
        
        if detected_date:
            print(f"✅ Scanner used date: {detected_date}")
        else:
            print("❌ Could not detect scanner date")
        
        print(f"   Found {len(results)} candidates")
        
        # Check if MMFL/TENNIND are in results
        target_stocks = ['MMFL', 'TENNIND']
        found_stocks = []
        
        for stock in results:
            symbol = stock.get('symbol', '')
            if symbol in target_stocks:
                found_stocks.append(symbol)
                print(f"   🎯 FOUND {symbol} in results!")
                print(f"      Close: {stock.get('close', 'N/A')}")
                print(f"      SMA20: {stock.get('sma20', 'N/A')}")
                print(f"      Dist to MA: {stock.get('dist_to_ma_pct', 'N/A')}%")
        
        if found_stocks:
            print(f"\n❌ PROBLEM: Scanner returned {found_stocks}")
        else:
            print(f"\n✅ GOOD: Scanner correctly filtered out {target_stocks}")
        
    except Exception as e:
        print(f"❌ Error testing scanner auto-date: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("🔍 DATE ISSUE INVESTIGATION")
    print("=" * 60)
    print("Testing to identify the exact date causing the 20 MA bug")
    
    # Test different dates
    test_different_dates()
    
    # Test scanner auto-date detection
    test_scanner_auto_date()
    
    print("\n" + "="*60)
    print("DATE INVESTIGATION COMPLETE")
    print("=" * 60)
    print("This will help identify if the issue is:")
    print("1. Scanner using wrong date (e.g., 30 Jan instead of 1 Feb)")
    print("2. Data timing issues")
    print("3. Cache data being from different dates")

if __name__ == "__main__":
    main()