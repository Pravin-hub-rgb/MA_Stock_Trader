#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Volume Timing Test
Tests volume validation with actual ENTRY_TIME
"""

import sys
import os
import time as time_module
from datetime import datetime, time, timedelta
import pytz

# Add src to path
sys.path.insert(0, 'src')

def test_volume_timing():
    """Test volume validation with actual ENTRY_TIME"""
    print("VOLUME TIMING TEST")
    print("=" * 30)
    print(f"Current time: {time_module.strftime('%H:%M:%S')}")
    print()
    
    try:
        # Import required modules
        from src.trading.live_trading.continuation_stock_monitor import StockMonitor, StockState
        from src.utils.upstox_fetcher import UpstoxFetcher
        from src.trading.live_trading.config import ENTRY_TIME
        
        # Create fetcher
        fetcher = UpstoxFetcher()
        
        # Create monitor
        monitor = StockMonitor()
        
        # Test with a real stock
        test_symbol = "ANGELONE"
        
        print(f"Testing volume timing for {test_symbol}")
        print("-" * 40)
        
        # Add test stock
        monitor.add_stock(test_symbol, "NSE_EQ|ANGELONE", 2642.0, 'continuation')
        stock = monitor.stocks["NSE_EQ|ANGELONE"]
        
        # Set up stock state (simulating post-market open state)
        stock.open_price = 2703.0
        stock.gap_validated = True
        stock.low_violation_checked = True
        stock.volume_validated = False
        
        # Set volume baseline (from cache data)
        stock.volume_baseline = 1310359.6  # ANGELONE baseline from logs
        
        print(f"Stock setup:")
        print(f"  Symbol: {stock.symbol}")
        print(f"  Open price: Rs{stock.open_price:.2f}")
        print(f"  Volume baseline: {stock.volume_baseline:,} shares")
        print()
        
        # Check current time vs ENTRY_TIME
        IST = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(IST).time()
        
        print(f"Timing check:")
        print(f"  Current time: {current_time}")
        print(f"  ENTRY_TIME: {ENTRY_TIME}")
        
        # Calculate time difference
        current_dt = datetime.combine(datetime.today(), current_time)
        entry_dt = datetime.combine(datetime.today(), ENTRY_TIME)
        time_diff = (current_dt - entry_dt).total_seconds()
        
        print(f"  Time difference: {time_diff:.0f} seconds from ENTRY_TIME")
        print()
        
        if time_diff >= 0 and time_diff <= 1800:  # Within 30 minutes after ENTRY_TIME
            print("✅ Within volume validation window - should validate now")
            
            # Test volume validation
            print("Testing volume validation...")
            
            # Get current volume
            current_volume = fetcher.get_current_volume(test_symbol)
            print(f"Current volume from API: {current_volume:,} shares")
            
            if current_volume > 0:
                # Use simplified approach: current_volume IS cumulative volume
                cumulative_volume = current_volume
                volume_ratio = (cumulative_volume / stock.volume_baseline) * 100
                
                print(f"Cumulative volume: {cumulative_volume:,} shares")
                print(f"Volume ratio: {volume_ratio:.1f}%")
                print(f"Threshold: 7.5%")
                
                if volume_ratio >= 7.5:
                    print("✅ Volume validation PASSED!")
                    stock.volume_validated = True
                    stock.early_volume = cumulative_volume
                else:
                    print("❌ Volume validation FAILED!")
                    stock.reject(f"Insufficient relative volume: {volume_ratio:.1f}% < 7.5%")
            else:
                print("❌ No volume data available")
                stock.reject("No volume data available")
            
            # Check qualification status
            print()
            print("Checking qualification status...")
            qualified_stocks = monitor.get_qualified_stocks()
            
            if qualified_stocks:
                print(f"✅ {test_symbol} is QUALIFIED!")
                for stock in qualified_stocks:
                    print(f"   Gap validated: {stock.gap_validated}")
                    print(f"   Low violation checked: {stock.low_violation_checked}")
                    print(f"   Volume validated: {stock.volume_validated}")
                    print(f"   Volume: {stock.early_volume:,} shares ({(stock.early_volume/stock.volume_baseline*100):.1f}%)")
            else:
                print(f"❌ {test_symbol} is REJECTED")
                if stock.rejection_reason:
                    print(f"   Reason: {stock.rejection_reason}")
            
            return len(qualified_stocks) > 0
            
        else:
            print("❌ Outside volume validation window")
            print("   Volume validation should only run at ENTRY_TIME + 2 minutes")
            return False
        
    except Exception as e:
        print(f"❌ Error in volume timing test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Testing Volume Timing with Actual ENTRY_TIME")
    print("This test verifies volume validation runs at the correct time")
    print()
    
    success = test_volume_timing()
    
    if success:
        print("\n✅ Volume timing test PASSED!")
        print("Volume validation is working at the correct time with actual ENTRY_TIME")
    else:
        print("\n❌ Volume timing test FAILED!")
    
    return success

if __name__ == "__main__":
    main()