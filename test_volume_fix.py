#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Volume Fix
Tests the simplified volume validation approach
"""

import sys
import os
import time as time_module
from datetime import datetime, time
import pytz

# Add src to path
sys.path.insert(0, 'src')

def test_volume_fix():
    """Test the volume fix with simplified approach"""
    print("VOLUME FIX TEST")
    print("=" * 30)
    print(f"Starting at: {time_module.strftime('%H:%M:%S')}")
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
        test_symbol = "RELIANCE"
        
        print(f"Testing volume fix for {test_symbol}")
        print("-" * 40)
        
        # Add test stock
        monitor.add_stock(test_symbol, "NSE_EQ|RELIANCE", 2950.0, 'continuation')
        stock = monitor.stocks["NSE_EQ|RELIANCE"]
        
        # Set up stock state
        stock.open_price = 2960.0
        stock.gap_validated = True
        stock.low_violation_checked = True
        stock.volume_validated = False
        
        # Set volume baseline (from cache data)
        stock.volume_baseline = 8000000  # 8M shares
        
        print(f"Stock setup:")
        print(f"  Symbol: {stock.symbol}")
        print(f"  Open price: Rs{stock.open_price:.2f}")
        print(f"  Volume baseline: {stock.volume_baseline:,} shares")
        print()
        
        # Test volume validation (simulating 9:20 timing)
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
        else:
            print(f"❌ {test_symbol} is REJECTED")
            if stock.rejection_reason:
                print(f"   Reason: {stock.rejection_reason}")
        
        return len(qualified_stocks) > 0
        
    except Exception as e:
        print(f"❌ Error in volume fix test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Testing Volume Fix for Continuation Bot")
    print("This test verifies the simplified volume validation approach")
    print()
    
    success = test_volume_fix()
    
    if success:
        print("\n✅ Volume fix test PASSED!")
        print("The continuation bot should now show proper volume validation")
        print("instead of '0.0% (0)' errors.")
    else:
        print("\n❌ Volume fix test FAILED!")
    
    return success

if __name__ == "__main__":
    main()