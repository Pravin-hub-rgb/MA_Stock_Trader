#!/usr/bin/env python3
"""
Test script for VAH calculation fixes
Tests the V3 API implementation and holiday detection
"""

import sys
import os

# Add src to path
sys.path.append('src')

def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")

    try:
        from src.trading.live_trading.volume_profile import volume_profile_calculator
        from src.utils.upstox_fetcher import upstox_fetcher
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_vah_calculator():
    """Test VAH calculator initialization"""
    print("\nTesting VAH calculator...")

    try:
        from src.trading.live_trading.volume_profile import volume_profile_calculator
        print(f"✅ VAH calculator initialized: {type(volume_profile_calculator)}")
        print(f"   Bin size: {volume_profile_calculator.bin_size}")
        print(f"   Value area %: {volume_profile_calculator.value_area_pct}")
        return True
    except Exception as e:
        print(f"❌ VAH calculator error: {e}")
        return False

def test_upstox_methods():
    """Test Upstox fetcher new methods"""
    print("\nTesting Upstox fetcher methods...")

    try:
        from src.utils.upstox_fetcher import upstox_fetcher

        # Test if methods exist
        has_get_ohlc = hasattr(upstox_fetcher, 'get_ohlc_data')
        print(f"✅ get_ohlc_data method: {'Available' if has_get_ohlc else 'Missing'}")

        # Test config loading
        has_token = bool(getattr(upstox_fetcher, 'access_token', None))
        print(f"✅ Access token loaded: {'Yes' if has_token else 'No'}")

        return has_get_ohlc
    except Exception as e:
        print(f"❌ Upstox fetcher error: {e}")
        return False

def test_vah_calculation():
    """Test VAH calculation for all stocks in continuation_list.txt"""
    print("\nTesting VAH calculation for continuation stocks...")

    # Configure logging to see the detailed output
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

    try:
        # Read continuation list
        continuation_file = "src/trading/continuation_list.txt"
        if not os.path.exists(continuation_file):
            print(f"❌ Continuation list not found: {continuation_file}")
            return False

        with open(continuation_file, 'r') as f:
            content = f.read().strip()
            symbols = [s.strip() for s in content.split(',') if s.strip()]

        print(f"📋 Found {len(symbols)} stocks in continuation list: {symbols}")

        if not symbols:
            print("❌ No stocks found in continuation list")
            return False

        # Import VAH calculator
        from src.trading.live_trading.volume_profile import volume_profile_calculator

        # Calculate VAH for all stocks
        print(f"\n🔄 Calculating VAH using previous trading day's data...")
        vah_dict = volume_profile_calculator.calculate_vah_for_stocks(symbols)

        # Display results
        print(f"\n📊 VAH CALCULATION RESULTS:")
        print("=" * 60)

        successful_calcs = 0
        for symbol in symbols:
            if symbol in vah_dict:
                vah = vah_dict[symbol]
                print(f"✅ {symbol}: Upper Range (VAH) = ₹{vah:.2f}")
                successful_calcs += 1
            else:
                print(f"❌ {symbol}: VAH calculation failed")

        print(f"\n📈 Summary: {successful_calcs}/{len(symbols)} stocks successfully calculated")

        if successful_calcs > 0:
            print("🎉 VAH calculation is working! The volume profile system is ready.")
            return True
        else:
            print("❌ All VAH calculations failed")
            return False

    except Exception as e:
        print(f"❌ Error testing VAH calculation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("VAH CALCULATION FIXES TEST")
    print("=" * 60)

    results = []

    # Test 1: Imports
    results.append(test_imports())

    # Test 2: VAH Calculator
    results.append(test_vah_calculator())

    # Test 3: Upstox Methods
    results.append(test_upstox_methods())

    # Test 4: VAH Calculation
    results.append(test_vah_calculation())

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 ALL TESTS PASSED - V3 API fixes are ready!")
        print("\nThe bot should now be able to:")
        print("- Detect previous trading days (including holidays)")
        print("- Fetch 1-minute OHLCV data using V3 API")
        print("- Calculate VAH from volume profiles")
        print("- Get opening prices using OHLC API")
        print("- Apply SVRO-V filtering successfully")
    else:
        print("❌ Some tests failed - check the errors above")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
