#!/usr/bin/env python3
"""
Test Previous Close Fetching for BSE
Verify that Jan 7, 2026 close is correctly fetched as ₹2744.90
"""

import sys
import os

# Add src to path
sys.path.append('src')

def test_bse_previous_close():
    """Test BSE previous close fetching"""
    print("🧪 TESTING BSE PREVIOUS CLOSE FETCHING")
    print("=" * 50)

    from utils.upstox_fetcher import UpstoxFetcher

    fetcher = UpstoxFetcher()

    print("Testing BSE previous close (should be ₹2744.90 for Jan 7, 2026)...")

    # Test LTP method first
    print("\n1. Testing LTP method ('cp' field):")
    try:
        ltp_data = fetcher.get_ltp_data('BSE')
        if ltp_data and 'cp' in ltp_data:
            cp = ltp_data['cp']
            print(f"   LTP 'cp' field: ₹{cp:.2f}")
            if abs(cp - 2744.90) < 0.01:  # Allow small floating point differences
                print("   ✅ CORRECT! Matches expected ₹2744.90")
            else:
                print(f"   ❌ INCORRECT! Expected ₹2744.90, got ₹{cp:.2f}")
        else:
            print("   ❌ No 'cp' field in LTP data")
    except Exception as e:
        print(f"   ❌ LTP method failed: {e}")

    # Test cache fallback
    print("\n2. Testing cache fallback:")
    try:
        cache_close = fetcher.get_previous_close_from_cache('BSE')
        if cache_close is not None:
            print(f"   Cache close: ₹{cache_close:.2f}")
            if abs(cache_close - 2744.90) < 0.01:
                print("   ✅ CORRECT! Matches expected ₹2744.90")
            else:
                print(f"   ❌ INCORRECT! Expected ₹2744.90, got ₹{cache_close:.2f}")
        else:
            print("   ❌ No cache data available")
    except Exception as e:
        print(f"   ❌ Cache method failed: {e}")

    # Test historical method (old way)
    print("\n3. Testing historical method (for comparison):")
    try:
        hist_data = fetcher.get_latest_data('BSE')
        if hist_data and 'close' in hist_data:
            close = hist_data['close']
            print(f"   Historical close: ₹{close:.2f}")
            if abs(close - 2744.90) < 0.01:
                print("   ✅ CORRECT! Matches expected ₹2744.90")
            else:
                print(f"   ⚠️  DIFFERENT! Expected ₹2744.90, got ₹{close:.2f} (this may be today's data)")
        else:
            print("   ❌ No historical data")
    except Exception as e:
        print(f"   ❌ Historical method failed: {e}")

    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    print("- LTP 'cp' field should give previous working day close")
    print("- Cache fallback ensures reliability")
    print("- Historical method may return inconsistent data")
    print("=" * 50)

if __name__ == "__main__":
    test_bse_previous_close()