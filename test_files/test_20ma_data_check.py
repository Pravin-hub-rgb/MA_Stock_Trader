#!/usr/bin/env python3
"""
Test script to check data availability and 20 MA calculation for MMFL and TENNIND
This script will help us understand exactly how many days of data we have
and verify if the 20 MA calculation is using sufficient data.
"""

import sys
import os
from datetime import date, timedelta
import pandas as pd

# Add src to path
sys.path.append('src')

from src.utils.cache_manager import cache_manager
from src.utils.data_fetcher import data_fetcher

def check_stock_data(symbol: str, scan_date: date):
    """Check data availability and 20 MA calculation for a specific stock"""
    print(f"\n{'='*60}")
    print(f"CHECKING DATA FOR: {symbol}")
    print(f"{'='*60}")
    
    # 1. Check cache data availability
    print(f"\n1. CACHE DATA AVAILABILITY:")
    cached_data = cache_manager.load_cached_data(symbol)
    
    if cached_data is None or cached_data.empty:
        print(f"   ❌ No cached data found for {symbol}")
        return
    
    print(f"   ✅ Found cached data: {len(cached_data)} days")
    
    # Show date range of cached data
    if isinstance(cached_data.index, pd.DatetimeIndex):
        first_date = cached_data.index[0]
        last_date = cached_data.index[-1]
        print(f"   📅 Date range: {first_date.date()} to {last_date.date()}")
        
        # Calculate total days
        total_days = (last_date.date() - first_date.date()).days + 1
        print(f"   📊 Total calendar days: {total_days}")
        print(f"   📈 Trading days in cache: {len(cached_data)}")
    
    # 2. Check data for scan date
    print(f"\n2. DATA FOR SCAN DATE ({scan_date}):")
    target_timestamp = pd.Timestamp(scan_date)
    has_scan_date = target_timestamp in cached_data.index
    
    if not has_scan_date:
        # Alternative check
        for idx_date in cached_data.index:
            if hasattr(idx_date, 'date'):
                idx_date_only = idx_date.date()
            else:
                idx_date_only = idx_date
            if idx_date_only == scan_date:
                has_scan_date = True
                break
    
    if has_scan_date:
        print(f"   ✅ Data available for scan date: {scan_date}")
    else:
        print(f"   ❌ No data available for scan date: {scan_date}")
        return
    
    # 3. Check data fetching for scanner
    print(f"\n3. SCANNER DATA FETCHING:")
    print(f"   Fetching data from earliest available to {scan_date}")
    
    # This mimics what the scanner does
    scanner_data = data_fetcher.get_data_for_date_range(
        symbol,
        None,  # From earliest available
        scan_date
    )
    
    if scanner_data.empty:
        print(f"   ❌ Scanner data fetch returned empty")
        return
    
    print(f"   ✅ Scanner data fetched: {len(scanner_data)} days")
    
    # Show date range of scanner data
    if isinstance(scanner_data.index, pd.DatetimeIndex):
        first_date = scanner_data.index[0]
        last_date = scanner_data.index[-1]
        print(f"   📅 Scanner data range: {first_date.date()} to {last_date.date()}")
    
    # 4. Check technical indicators calculation
    print(f"\n4. TECHNICAL INDICATORS CALCULATION:")
    print(f"   Calculating technical indicators (including 20 MA)")
    
    # This mimics what data_fetcher.calculate_technical_indicators does
    if 'ma_20' not in scanner_data.columns:
        scanner_data['ma_20'] = scanner_data['close'].rolling(window=20).mean()
    
    # Check if 20 MA has valid values
    ma_20_values = scanner_data['ma_20'].dropna()
    print(f"   📊 20 MA calculated for {len(ma_20_values)} days")
    
    if len(ma_20_values) == 0:
        print(f"   ❌ No 20 MA values calculated - insufficient data!")
        return
    
    # 5. Check latest data point
    print(f"\n5. LATEST DATA POINT ANALYSIS:")
    latest = scanner_data.iloc[-1]
    
    print(f"   📈 Latest date: {latest.name}")
    print(f"   💰 Close price: {latest['close']:.2f}")
    print(f"   📊 20 MA: {latest['ma_20']:.2f}")
    
    # Check if close is above 20 MA
    if latest['close'] > latest['ma_20']:
        print(f"   ✅ Close is ABOVE 20 MA")
        above_ma = True
    else:
        print(f"   ❌ Close is BELOW 20 MA")
        above_ma = False
    
    # 6. Check 20 MA calculation validity
    print(f"\n6. 20 MA CALCULATION VALIDITY:")
    
    # Get the data used for the latest 20 MA calculation
    latest_index = scanner_data.index[-1]
    latest_position = scanner_data.index.get_loc(latest_index)
    
    # For 20 MA to be valid, we need at least 20 data points before this position
    required_start_position = latest_position - 19
    
    if required_start_position < 0:
        print(f"   ❌ INSUFFICIENT DATA: Need {20} days, only have {latest_position + 1} days")
        print(f"       This explains why the 20 MA might be artificially low!")
    else:
        print(f"   ✅ SUFFICIENT DATA: Have {latest_position + 1} days, need {20} days")
        
        # Show the actual data used for 20 MA calculation
        ma_data = scanner_data.iloc[required_start_position:latest_position + 1]
        print(f"   📊 20 MA calculated using data from {ma_data.index[0].date()} to {ma_data.index[-1].date()}")
        print(f"   📈 Close prices used: {ma_data['close'].tolist()}")
        
        # Calculate manual 20 MA to verify
        manual_ma = ma_data['close'].mean()
        print(f"   🧮 Manual 20 MA calculation: {manual_ma:.2f}")
        print(f"   📊 Scanner 20 MA value: {latest['ma_20']:.2f}")
        
        if abs(manual_ma - latest['ma_20']) < 0.01:
            print(f"   ✅ 20 MA calculation is correct")
        else:
            print(f"   ⚠️  20 MA calculation discrepancy detected")
    
    # 7. Summary
    print(f"\n7. SUMMARY FOR {symbol}:")
    print(f"   📊 Total data days: {len(scanner_data)}")
    print(f"   📈 Above 20 MA: {above_ma}")
    print(f"   📊 20 MA value: {latest['ma_20']:.2f}")
    print(f"   💰 Close price: {latest['close']:.2f}")
    
    if above_ma:
        print(f"   🎯 This stock would PASS the 20 MA check in scanner")
    else:
        print(f"   🚫 This stock would FAIL the 20 MA check in scanner")
    
    return scanner_data

def main():
    """Main test function"""
    print("🔍 20 MA DATA CHECK TEST")
    print("=" * 60)
    
    # Test for 1st Feb 2026 (as mentioned in the issue)
    scan_date = date(2026, 2, 1)
    print(f"Testing for scan date: {scan_date}")
    
    # Test stocks mentioned in the issue
    test_stocks = ['MMFL', 'TENNIND']
    
    all_results = {}
    
    for symbol in test_stocks:
        try:
            result = check_stock_data(symbol, scan_date)
            all_results[symbol] = result
        except Exception as e:
            print(f"\n❌ Error checking {symbol}: {e}")
            all_results[symbol] = None
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    for symbol in test_stocks:
        result = all_results[symbol]
        if result is not None:
            latest = result.iloc[-1]
            above_ma = latest['close'] > latest['ma_20']
            print(f"{symbol}: {'✅ PASS' if above_ma else '❌ FAIL'} - Close: {latest['close']:.2f}, 20 MA: {latest['ma_20']:.2f}")
        else:
            print(f"{symbol}: ❌ ERROR - Could not analyze")

if __name__ == "__main__":
    main()