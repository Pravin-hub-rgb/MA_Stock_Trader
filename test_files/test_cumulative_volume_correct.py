#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Correct Cumulative Volume Test
Tests proper volume accumulation from market open using the correct method
"""

import sys
import time
import logging

# Add src to path
sys.path.insert(0, 'src')

# Configure logging to show detailed messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

def test_cumulative_volume_correct():
    """Test proper cumulative volume accumulation from market open"""
    print("CORRECT CUMULATIVE VOLUME TEST")
    print("=" * 40)
    print(f"Starting at: {time.strftime('%H:%M:%S')}")
    print()
    
    # Import required modules
    from src.utils.upstox_fetcher import upstox_fetcher
    
    # Test stock from user's logs
    test_stock = "BLISSGVS"
    print(f"Testing stock: {test_stock}")
    print("-" * 30)
    
    # Get initial volume at start (this represents volume at market open)
    print("Getting initial volume (market open baseline)...")
    try:
        initial_volume = upstox_fetcher.get_current_volume(test_stock)
        if initial_volume <= 0:
            print("❌ Failed to get initial volume")
            return False
        print(f"Initial volume (baseline): {initial_volume:,} shares")
    except Exception as e:
        print(f"❌ Error getting initial volume: {e}")
        return False
    
    # Test volume accumulation for 30 seconds
    print(f"\nTesting volume accumulation for 30 seconds...")
    print("Time | Current Volume | Change | Cumulative | % of Mean | Status")
    print("-" * 70)
    
    start_time = time.time()
    end_time = start_time + 30  # 30 seconds test
    cumulative_volume = 0
    sample_count = 0
    
    # Get mean volume baseline from cache data (real data now!)
    try:
        from src.trading.live_trading.stock_scorer import stock_scorer
        from src.utils.cache_manager import cache_manager
        import os
        
        # Load cache data into stock_scorer metadata
        cache_files = os.listdir(cache_manager.cache_dir)
        available_stocks = [f.replace('.pkl', '') for f in cache_files if f.endswith('.pkl')]
        test_stocks = [test_stock] + available_stocks[:5]
        stock_scorer.preload_metadata(test_stocks)
        
        metadata = stock_scorer.stock_metadata.get(test_stock, {})
        mean_volume = metadata.get('volume_baseline', 0)
        
        if mean_volume > 0:
            print(f"Real mean volume baseline: {mean_volume:,} shares")
        else:
            print(f"❌ No mean volume baseline found for {test_stock}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting mean volume: {e}")
        return False
    
    while time.time() < end_time:
        current_time = time.time()
        elapsed = int(current_time - start_time)
        sample_count += 1
        
        try:
            # Get current volume (total daily volume)
            current_volume = upstox_fetcher.get_current_volume(test_stock)
            
            if current_volume > 0:
                # Calculate volume change from initial (this is the NEW volume since market open)
                volume_change = current_volume - initial_volume
                if volume_change < 0:  # Handle volume reset/rollover
                    volume_change = 0
                
                # Update cumulative volume (volume accumulated since market open)
                cumulative_volume += volume_change
                
                # Calculate percentage of mean volume
                volume_pct = (cumulative_volume / mean_volume) * 100
                
                # Format volumes for display
                if current_volume >= 1000000:
                    curr_vol_str = f"{current_volume/1000000:.1f}M"
                elif current_volume >= 1000:
                    curr_vol_str = f"{current_volume/1000:.1f}K"
                else:
                    curr_vol_str = f"{current_volume:.0f}"
                
                if cumulative_volume >= 1000000:
                    cum_vol_str = f"{cumulative_volume/1000000:.1f}M"
                elif cumulative_volume >= 1000:
                    cum_vol_str = f"{cumulative_volume/1000:.1f}K"
                else:
                    cum_vol_str = f"{cumulative_volume:.0f}"
                
                # Check if meets SVRO threshold (7.5%)
                threshold_met = volume_pct >= 7.5
                status = "✅ PASS" if threshold_met else "❌ FAIL"
                
                print(f"{elapsed:2d}s  | {curr_vol_str:>12} | {volume_change:>6} | {cum_vol_str:>10} | {volume_pct:5.1f}% | {status}")
                
                # Update initial volume for next iteration (this simulates real-time accumulation)
                initial_volume = current_volume
                
            else:
