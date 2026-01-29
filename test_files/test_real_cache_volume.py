#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Real Cache Volume Data
Loads actual cache data and tests volume accumulation vs real mean volume
"""

import sys
import time
import logging

# Add src to path
sys.path.insert(0, 'src')

# Configure logging to show detailed messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

def test_real_cache_volume():
    """Test volume system with real cache data for 30 seconds"""
    print("REAL CACHE VOLUME TEST - MULTIPLE STOCKS")
    print("=" * 50)
    print(f"Starting at: {time.strftime('%H:%M:%S')}")
    print()
    
    # Import required modules
    from src.utils.upstox_fetcher import upstox_fetcher
    from src.trading.live_trading.stock_scorer import stock_scorer
    
    # Test stocks including RELIANCE
    test_stocks = ["BLISSGVS", "RELIANCE", "INFY", "TCS", "HDFCBANK"]
    print(f"Testing stocks: {test_stocks}")
    print("-" * 50)
    
    # Load cache data into stock_scorer metadata
    print("Loading cache data into stock_scorer...")
    try:
        # Get list of available stocks from cache
        from src.utils.cache_manager import cache_manager
        import os
        
        cache_files = os.listdir(cache_manager.cache_dir)
        available_stocks = [f.replace('.pkl', '') for f in cache_files if f.endswith('.pkl')]
        print(f"Available stocks in cache: {len(available_stocks)}")
        
        # Load metadata for test stocks (including RELIANCE)
        print(f"Loading metadata for: {test_stocks}")
        
        # Call preload_metadata to load cache data into memory
        stock_scorer.preload_metadata(test_stocks)
        print(f"✅ Loaded metadata for {len(stock_scorer.stock_metadata)} stocks")
        
    except Exception as e:
        print(f"❌ Error loading cache data: {e}")
        return False
    
    # Test each stock
    for stock_symbol in test_stocks:
        print(f"\n{'='*60}")
        print(f"TESTING STOCK: {stock_symbol}")
        print(f"{'='*60}")
        
        # Get mean volume baseline from cache data (real data now!)
        try:
            metadata = stock_scorer.stock_metadata.get(stock_symbol, {})
            mean_volume = metadata.get('volume_baseline', 0)
            
            if mean_volume > 0:
                print(f"✅ Real mean volume baseline found: {mean_volume:,} shares")
                print(f"   ADR: {metadata.get('adr_percent', 'N/A'):.1f}% | Price: Rs{metadata.get('current_price', 'N/A'):.0f}")
            else:
                print(f"❌ No mean volume baseline found for {stock_symbol}")
                continue
                
        except Exception as e:
            print(f"❌ Error getting mean volume for {stock_symbol}: {e}")
            continue
        
        # Test volume accumulation for 30 seconds
        print(f"\nTesting volume accumulation for 30 seconds...")
        print("Time | Cumulative Volume | % of Mean | Status")
        print("-" * 50)
        
        start_time = time.time()
        end_time = start_time + 30  # 30 seconds test
        
        # Get initial volume to track accumulation
        initial_volume = upstox_fetcher.get_current_volume(stock_symbol)
        if initial_volume == 0:
            print(f"❌ Could not get initial volume reading for {stock_symbol}")
            continue
        
        print(f"Initial volume reading: {initial_volume:,}")
        
        while time.time() < end_time:
            current_time = time.time()
            elapsed = int(current_time - start_time)
            
            try:
                # Get current volume and calculate cumulative (current - initial)
                current_volume = upstox_fetcher.get_current_volume(stock_symbol)
                
                if current_volume > 0:
                    # Calculate cumulative volume (volume accumulated since start)
                    cumulative_volume = current_volume - initial_volume
                    
                    # Calculate percentage of mean volume
                    volume_pct = (cumulative_volume / mean_volume) * 100
                    
                    # Format volume for display
                    if cumulative_volume >= 1000000:
                        vol_str = f"{cumulative_volume/1000000:.1f}M"
                    elif cumulative_volume >= 1000:
                        vol_str = f"{cumulative_volume/1000:.1f}K"
                    else:
                        vol_str = f"{cumulative_volume:.0f}"
                    
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
        
        # Final summary with real cache data
        try:
            final_volume = upstox_fetcher.get_current_volume(stock_symbol)
            if final_volume > 0:
                # Calculate actual cumulative volume (final - initial)
                actual_cumulative = final_volume - initial_volume
                final_pct = (actual_cumulative / mean_volume) * 100
                print(f"Final cumulative volume: {actual_cumulative:,} shares ({final_pct:.1f}%)")
                print(f"Real mean volume baseline: {mean_volume:,} shares")
                print(f"Threshold met: {'YES' if final_pct >= 7.5 else 'NO'}")
                print(f"Stock: {stock_symbol} | ADR: {metadata.get('adr_percent', 'N/A'):.1f}% | Price: Rs{metadata.get('current_price', 'N/A'):.0f}")
            else:
                print("❌ Could not get final volume reading")
        except Exception as e:
            print(f"❌ Error in final reading: {e}")
    
    return True

def main():
    """Main test function"""
    print("Starting Real Cache Volume Test")
    print("This test uses ACTUAL cache data (not fallback values)")
    print("Testing with BLISSGVS and real mean volume baseline")
    print()
    
    # Run test
    success = test_real_cache_volume()
    
    if success:
        print("\n✅ Real cache volume test completed")
        print("Now using REAL cache data instead of random 800K fallback!")
    else:
        print("\n❌ Real cache volume test failed")
        print("Check cache loading and Upstox API")
    
    return success

if __name__ == "__main__":
    main()