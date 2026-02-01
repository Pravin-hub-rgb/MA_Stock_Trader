#!/usr/bin/env python3
"""
Test to see which stocks are actually passing the scanner and why.
"""

import sys
import os
from datetime import date

# Add src to path
sys.path.append('src')

from src.scanner.scanner import scanner

def test_who_is_passing(scan_date: date):
    """Test which stocks are passing the scanner and why"""
    print("🔍 WHO IS PASSING THE SCANNER?")
    print("=" * 60)
    
    try:
        # Run the actual continuation scan
        print(f"\n1. RUNNING CONTINUATION SCAN:")
        result = scanner.run_continuation_scan(scan_date)
        
        print(f"   📊 Total candidates found: {len(result)}")
        
        if len(result) > 0:
            print(f"\n2. CANDIDATE DETAILS:")
            for i, candidate in enumerate(result, 1):
                print(f"\n   {i}. {candidate['symbol']}:")
                print(f"      Close: {candidate['close']:.2f}")
                print(f"      20 MA: {candidate['sma20']:.2f}")
                print(f"      Distance from MA: {candidate['dist_to_ma_pct']:.2f}%")
                print(f"      Above 20 MA: {candidate['close'] > candidate['sma20']}")
                print(f"      Phase1 High: {candidate['phase1_high']:.2f}")
                print(f"      Phase2 Low: {candidate['phase2_low']:.2f}")
                print(f"      Phase3 High: {candidate['phase3_high']:.2f}")
                print(f"      Depth: {candidate['depth_rs']:.2f} ({candidate['depth_pct']:.1f}%)")
                print(f"      ADR: {candidate['adr_pct']:.1f}%")
        else:
            print(f"   ❌ No candidates found")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error running scanner: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Main test function"""
    scan_date = date(2026, 2, 1)
    candidates = test_who_is_passing(scan_date)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if len(candidates) > 0:
        print(f"Found {len(candidates)} candidates:")
        for candidate in candidates:
            print(f"   - {candidate['symbol']}")
    else:
        print("No candidates found in scanner")

if __name__ == "__main__":
    main()