#!/usr/bin/env python3
"""
Simple Test: BSE Previous Close from Cache
"""

import sys
sys.path.append('src')

def test_simple_bse():
    """Simple test of BSE previous close from cache"""
    print("🧪 SIMPLE TEST: BSE Previous Close from Cache")
    print("=" * 50)

    from utils.upstox_fetcher import UpstoxFetcher

    fetcher = UpstoxFetcher()
    close = fetcher.get_previous_close_from_cache('BSE')

    if close is not None:
        print(f"🎯 BSE Previous Close: ₹{close:.2f}")
        expected = 2744.90
        if abs(close - expected) < 0.01:
            print("✅ SUCCESS! Cache data is correct!")
            return True
        else:
            print(f"❌ FAILED! Expected ₹{expected:.2f}, got ₹{close:.2f}")
            return False
    else:
        print("❌ No cache data found for BSE")
        return False

if __name__ == "__main__":
    success = test_simple_bse()
    print("\n" + "=" * 50)
    if success:
        print("🎉 CACHE DATA VERIFIED!")
        print("✅ Previous close: ACCURATE")
        print("✅ Live trading: READY")
    else:
        print("⚠️  CHECK CACHE DATA")
    print("=" * 50)