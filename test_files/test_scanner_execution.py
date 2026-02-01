#!/usr/bin/env python3
"""
Test script to run the actual continuation scanner on MMFL and TENNIND
This will help us see exactly what the scanner is doing and why these stocks
are appearing in results when they should be filtered out by the 20 MA check.
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

def test_scanner_execution(symbol: str, scan_date: date):
    """Test the actual scanner execution for a specific stock"""
    print(f"\n{'='*60}")
    print(f"TESTING SCANNER EXECUTION FOR: {symbol}")
    print(f"{'='*60}")
    
    try:
        # 1. Get cached data (same as scanner)
        print(f"\n1. GETTING CACHED DATA:")
        cached_data = cache_manager.load_cached_data(symbol)
        
        if cached_data is None or cached_data.empty:
            print(f"   ❌ No cached data found for {symbol}")
            return None
        
        print(f"   ✅ Found cached data: {len(cached_data)} days")
        
        # 2. Get data for date range (same as scanner)
        print(f"\n2. FETCHING DATA FOR DATE RANGE:")
        scanner_data = data_fetcher.get_data_for_date_range(
            symbol,
            None,  # From earliest available
            scan_date
        )
        
        if scanner_data.empty:
            print(f"   ❌ Scanner data fetch returned empty")
            return None
        
        print(f"   ✅ Scanner data fetched: {len(scanner_data)} days")
        
        # 3. Calculate technical indicators (same as scanner)
        print(f"\n3. CALCULATING TECHNICAL INDICATORS:")
        scanner_data = data_fetcher.calculate_technical_indicators(scanner_data)
        print(f"   ✅ Technical indicators calculated")
        
        # 4. Get latest data point
        latest = scanner_data.iloc[-1]
        print(f"   📈 Latest date: {latest.name}")
        print(f"   💰 Close: {latest['close']:.2f}")
        print(f"   📊 20 MA: {latest['ma_20']:.2f}")
        
        # 5. Apply base filters (same as scanner)
        print(f"\n4. APPLYING BASE FILTERS:")
        
        # Check price filter (₹100 - ₹2000)
        price_min = 100
        price_max = 2000
        close_price = float(latest['close'])
        price_pass = price_min <= close_price <= price_max
        print(f"   💰 Price filter (₹{price_min}-{price_max}): {'✅ PASS' if price_pass else '❌ FAIL'} - {close_price:.2f}")
        
        if not price_pass:
            print(f"   🚫 Would be filtered out by price filter")
            return None
        
        # Check ADR filter (3% minimum)
        adr_percent = float(latest['adr_percent'])
        adr_pass = adr_percent >= 3.0
        print(f"   📊 ADR filter (≥3%): {'✅ PASS' if adr_pass else '❌ FAIL'} - {adr_percent:.2f}%")
        
        if not adr_pass:
            print(f"   🚫 Would be filtered out by ADR filter")
            return None
        
        # 6. Check liquidity confirmation (same as scanner)
        print(f"\n5. CHECKING LIQUIDITY CONFIRMATION:")
        
        # This mimics the filter_engine.check_liquidity_confirmation logic
        lookback_days = 30
        recent_data = scanner_data.tail(lookback_days)
        volume_threshold = 1000000  # 1M shares
        movement_threshold_pct = 0.05  # 5% price movement
        min_liquid_days = 2
        
        # Calculate absolute price movement (either direction)
        price_movements = abs(recent_data['close'] - recent_data['open']) / recent_data['open']
        
        # Find days with BOTH high volume AND significant price movement
        liquid_days = (recent_data['volume'] >= volume_threshold) & \
                     (price_movements >= movement_threshold_pct)
        
        liquid_days_count = liquid_days.sum()
        liquidity_pass = liquid_days_count >= min_liquid_days
        
        print(f"   💧 Liquidity check (≥{min_liquid_days} days): {'✅ PASS' if liquidity_pass else '❌ FAIL'} - {liquid_days_count} days")
        
        if not liquidity_pass:
            print(f"   🚫 Would be filtered out by liquidity filter")
            return None
        
        # 7. Run continuation pattern analysis (same as scanner)
        print(f"\n6. RUNNING CONTINUATION PATTERN ANALYSIS:")
        
        # This mimics the continuation_analyzer.analyze_continuation_setup logic
        params = {
            'near_ma_threshold': 0.06,  # 6% as you mentioned
            'max_body_percentage': 0.05,  # 5% max body size
        }
        
        # Prepare data with proper column names (same as continuation_analyzer)
        df = scanner_data.copy()
        
        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            df = df.rename(columns={'index': 'date'})
        
        df = df.rename(columns={
            'open': 'Open', 'high': 'High', 'low': 'Low',
            'close': 'Close', 'volume': 'Volume', 'ma_20': 'SMA20'
        })
        df = df.set_index('date')
        
        # Calculate indicators (same as continuation_analyzer)
        if 'SMA20' not in df.columns:
            df['SMA20'] = df['Close'].rolling(window=20).mean()
        
        df['SMA20_prev_max'] = df['SMA20'].shift(1).rolling(5).max()
        df['Rising_MA'] = df['SMA20'] > df['SMA20_prev_max']
        df['Above_MA'] = df['Close'] > df['SMA20']
        df['Dist_to_MA_pct'] = abs(df['Close'] - df['SMA20']) / df['Close']
        df['Near_or_Above_MA'] = (df['Close'] > df['SMA20']) & (df['Dist_to_MA_pct'] <= params['near_ma_threshold'])
        
        latest_df = df.iloc[-1]
        
        # Check Phase 3 (20 MA check) - this is the FIRST check in continuation_analyzer
        print(f"   📊 20 MA check (Phase 3):")
        print(f"      - Near_or_Above_MA: {latest_df['Near_or_Above_MA']}")
        print(f"      - Rising_MA: {latest_df['Rising_MA']}")
        print(f"      - Dist_to_MA_pct: {latest_df['Dist_to_MA_pct']*100:.2f}% (threshold: {params['near_ma_threshold']*100}%)")
        
        phase3_pass = latest_df['Near_or_Above_MA'] and latest_df['Rising_MA']
        print(f"      - Result: {'✅ PASS' if phase3_pass else '❌ FAIL'}")
        
        if not phase3_pass:
            print(f"   🚫 Would be filtered out by 20 MA check (Phase 3)")
            return None
        
        # Check body size
        body_size_pct = abs(latest_df['Open'] - latest_df['Close']) / latest_df['Close']
        body_pass = body_size_pct < params['max_body_percentage']
        print(f"   📐 Body size check: {'✅ PASS' if body_pass else '❌ FAIL'} - {body_size_pct*100:.2f}% (threshold: {params['max_body_percentage']*100}%)")
        
        if not body_pass:
            print(f"   🚫 Would be filtered out by body size check")
            return None
        
        # If we get here, the stock would pass all checks
        print(f"\n7. FINAL RESULT:")
        print(f"   🎯 {symbol} WOULD PASS ALL SCANNER CHECKS!")
        print(f"   💰 Close: {latest['close']:.2f}")
        print(f"   📊 20 MA: {latest['ma_20']:.2f}")
        print(f"   📈 Above 20 MA: {latest['close'] > latest['ma_20']}")
        print(f"   📊 Distance from MA: {latest_df['Dist_to_MA_pct']*100:.2f}%")
        
        return {
            'symbol': symbol,
            'close': latest['close'],
            'sma20': latest['ma_20'],
            'dist_to_ma_pct': latest_df['Dist_to_MA_pct'] * 100,
            'above_ma': latest['close'] > latest['ma_20'],
            'near_ma': latest_df['Near_or_Above_MA'],
            'rising_ma': latest_df['Rising_MA']
        }
        
    except Exception as e:
        print(f"\n❌ Error testing {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main test function"""
    print("🔍 SCANNER EXECUTION TEST")
    print("=" * 60)
    
    # Test for 1st Feb 2026 (as mentioned in the issue)
    scan_date = date(2026, 2, 1)
    print(f"Testing scanner execution for scan date: {scan_date}")
    
    # Test stocks mentioned in the issue
    test_stocks = ['MMFL', 'TENNIND']
    
    all_results = {}
    
    for symbol in test_stocks:
        result = test_scanner_execution(symbol, scan_date)
        all_results[symbol] = result
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    for symbol in test_stocks:
        result = all_results[symbol]
        if result is not None:
            print(f"{symbol}: 🎯 WOULD PASS SCANNER")
            print(f"   Close: {result['close']:.2f}, 20 MA: {result['sma20']:.2f}")
            print(f"   Above 20 MA: {result['above_ma']}, Near MA: {result['near_ma']}")
            print(f"   Distance from MA: {result['dist_to_ma_pct']:.2f}%")
        else:
            print(f"{symbol}: ❌ WOULD FAIL SCANNER")

if __name__ == "__main__":
    main()