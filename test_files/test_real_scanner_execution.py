#!/usr/bin/env python3
"""
Test the actual scanner execution to see what's happening
with MMFL and TENNIND in the real scanner.
"""

import sys
import os
from datetime import date
import pandas as pd

# Add src to path
sys.path.append('src')

from src.scanner.scanner import scanner

def test_real_scanner_execution(symbol: str, scan_date: date):
    """Test the actual scanner execution"""
    print(f"\n{'='*60}")
    print(f"TESTING REAL SCANNER EXECUTION FOR: {symbol}")
    print(f"{'='*60}")
    
    try:
        # Run the actual continuation scan for this symbol
        print(f"\n1. RUNNING ACTUAL CONTINUATION SCAN:")
        
        # Get the scanner's continuation scan method
        result = scanner.run_continuation_scan(scan_date)
        
        # Check if our symbol is in the results
        symbol_found = any(r['symbol'] == symbol for r in result)
        
        print(f"   📊 Total candidates found: {len(result)}")
        print(f"   🎯 {symbol} in results: {symbol_found}")
        
        if symbol_found:
            symbol_result = next(r for r in result if r['symbol'] == symbol)
            print(f"   💰 {symbol} details:")
            print(f"      Close: {symbol_result['close']:.2f}")
            print(f"      20 MA: {symbol_result['sma20']:.2f}")
            print(f"      Distance from MA: {symbol_result['dist_to_ma_pct']:.2f}%")
            print(f"      Phase1 High: {symbol_result['phase1_high']:.2f}")
            print(f"      Phase2 Low: {symbol_result['phase2_low']:.2f}")
            print(f"      Phase3 High: {symbol_result['phase3_high']:.2f}")
            print(f"      Depth: {symbol_result['depth_rs']:.2f} ({symbol_result['depth_pct']:.1f}%)")
            print(f"      ADR: {symbol_result['adr_pct']:.1f}%")
        else:
            print(f"   ❌ {symbol} NOT found in scanner results")
        
        return symbol_found
        
    except Exception as e:
        print(f"\n❌ Error testing {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🔍 REAL SCANNER EXECUTION TEST")
    print("=" * 60)
    
    # Test for 1st Feb 2026
    scan_date = date(2026, 2, 1)
    print(f"Testing real scanner execution for scan date: {scan_date}")
    
    # Test stocks
    test_stocks = ['MMFL', 'TENNIND']
    
    all_results = {}
    
    for symbol in test_stocks:
        result = test_real_scanner_execution(symbol, scan_date)
        all_results[symbol] = result
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    for symbol in test_stocks:
        found = all_results[symbol]
        print(f"{symbol}: {'✅ FOUND in scanner results' if found else '❌ NOT found in scanner results'}")

if __name__ == "__main__":
    main()