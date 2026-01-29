#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Volume System Test
Tests volume accumulation vs mean volume baseline for 30 seconds
"""

import sys
import time
import logging

# Add src to path
sys.path.insert(0, 'src')

# Configure logging to show detailed messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

def test_volume_system_simple():
    """Test volume system with real cache data for 30 seconds"""
    print("SIMPLE VOLUME SYSTEM TEST")
    print("=" * 40)
    print(f"Starting at: {time.strftime('%H:%M:%S')}")
    print()
    
    # Import required modules
    from src.utils.upstox_fetcher import upstox_fetcher
    from src.trading.live_trading.stock_scorer import stock_scorer
    
    # Test stock from user's logs
    test_stock = "BLISSGVS"
    print(f"Testing stock: {test_stock}")
    print("-" * 30)
    
    # Try to get mean volume baseline from cache data first
    try:
        metadata = stock_scorer.stock_metadata.get(test_stock, {})
        mean_volume = metadata.get('volume_baseline', 0)
        
        if mean_volume > 0:
            print(f"✅ Mean volume baseline found from cache: {mean_volume:,} shares")
        else:
            print(f"❌ No cache data found for {test_stock}")
            print("Will use fallback volume baseline for testing")
            mean_volume = 800000  # Fallback baseline (800K)
            print(f"Using fallback baseline: {mean_volume:,} shares")
            
    except Exception as e:
        print(f"❌ Error getting mean volume: {e}")
        print("Using fallback baseline for testing")
        mean_volume = 800000  # Fallback baseline
    
    # Test volume accumulation for 30 seconds
    print(f"\nTesting volume accumulation for 30 seconds...")
    print("Time | Cumulative Volume | % of Mean | Status")
    print("-" * 50)
    
    start_time = time.time()
    end_time = start_time + 30  # 30 seconds test
    
    while time.time() < end_time:
        current_time = time.time()
        elapsed = int(current_time - start_time)
        
        try:
            # Get current cumulative volume using the volume-only method
            current_volume = upstox_fetcher.get_current_volume(test_stock)
            
            if current_volume > 0:
                # Calculate percentage of mean volume
                volume_pct = (current_volume / mean_volume) * 100
                
                # Format volume for display
                if current_volume >= 1000000:
                    vol_str = f"{current_volume/1000000:.1f}M"
                elif current_volume >= 1000:
                    vol_str = f"{current_volume/1000:.1f}K"
                else:
                    vol_str = f"{current_volume:.0f}"
                
                # Check if meets SVRO threshold (7.5%)
                threshold_met = volume_pct >= 7.5
                status = "✅ PASS" if threshold_met else "❌ FAIL"
                
                print(f"{elapsed:2d}s  | {vol_str:>12} | {volume_pct:5.1f}% | {status}")
                
            else:
                print(f"{elapsed:2d}s  | {'No data':>12} | {'N/A':>5} | ❌ FAIL")
                
        except Exception as e:
            print(f"{elapsed:2d}s  | {'Error':>12} | {'N/A':>5} | ❌ FAIL ({e})")
        
        # Wait 3 seconds between checks
        time.sleep(3)
    
    print("\n" + "=" * 50)
    print("TEST COMPLETED")
    print("=" * 50)
    
    # Final summary
    try:
        final_volume = upstox_fetcher.get_current_volume(test_stock)
        if final_volume > 0:
            final_pct = (final_volume / mean_volume) * 100
            print(f"Final cumulative volume: {final_volume:,} shares ({final_pct:.1f}%)")
            print(f"Mean volume baseline: {mean_volume:,} shares")
            print(f"Threshold met: {'YES' if final_pct >= 7.5 else 'NO'}")
        else:
            print("❌ Could not get final volume reading")
    except Exception as e:
        print(f"❌ Error in final reading: {e}")
    
    return True

def main():
    """Main test function"""
    print("Starting Simple Volume System Test")
    print("This test verifies volume accumulation vs mean volume baseline")
    print("Testing with BLISSGVS (from your live logs)")
    print()
    
    # Run test
    success = test_volume_system_simple()
    
    if success:
        print("\n✅ Volume system test completed")
        print("Check the output above to see if volume accumulation is working correctly")
    else:
        print("\n❌ Volume system test failed")
        print("Check if cache data is available and Upstox API is working")
    
    return success

if __name__ == "__main__":
    main()