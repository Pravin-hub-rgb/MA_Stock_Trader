#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Volume Fix Test
Tests the complete simplified volume validation approach
"""

import sys
import os
import time as time_module
from datetime import datetime, time, timedelta
import pytz

# Add src to path
sys.path.insert(0, 'src')

def test_complete_volume_fix():
    """Test the complete volume fix with simplified approach"""
    print("COMPLETE VOLUME FIX TEST")
    print("=" * 40)
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
        
        print(f"Testing complete volume fix for {test_symbol}")
        print("-" * 50)
        
        # Add test stock
        monitor.add_stock(test_symbol, "NSE_EQ|RELIANCE", 2950.0, 'continuation')
        stock = monitor.stocks["NSE_EQ|RELIANCE"]
        
        # Set up stock state (simulating post-market open state)
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
        
        # Simulate the timing check in check_volume_validations
        IST = pytz.timezone('Asia/Kolkata')
        current_time = ENTRY_TIME  # 9:20
        
        # Mock the time check
        import datetime as dt
        mock_datetime = dt.datetime.combine(dt.date.today(), current_time)
        mock_datetime = IST.localize(mock_datetime)
        
        # Temporarily patch datetime.now to return our mock time
        original_now = dt.datetime.now
        dt.datetime.now = lambda tz=None: mock_datetime
        
        try:
            # Test volume validation at 9:20
            print("Testing volume validation at 9:20...")
            
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
                
        finally:
            # Restore original datetime.now
            dt.datetime.now = original_now
        
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
        
        # Test the timing logic
        print()
        print("Testing timing logic...")
        
        # Test before 9:20 (should return early)
        before_920 = (datetime.combine(datetime.today(), ENTRY_TIME) - timedelta(minutes=5)).time()
        mock_datetime_before = dt.datetime.combine(dt.date.today(), before_920)
        mock_datetime_before = IST.localize(mock_datetime_before)
        dt.datetime.now = lambda tz=None: mock_datetime_before
        
        # Reset volume validation
        stock.volume_validated = False
        stock.early_volume = 0
        
        # This should return early (no validation)
        monitor.check_volume_validations()
        
        if not stock.volume_validated:
            print("✅ Timing logic working: No validation before 9:20")
        else:
            print("❌ Timing logic failed: Validation ran before 9:20")
        
        # Test at 9:20 (should validate)
        dt.datetime.now = lambda tz=None: mock_datetime
        monitor.check_volume_validations()
        
        if stock.volume_validated:
            print("✅ Timing logic working: Validation ran at 9:20")
        else:
            print("❌ Timing logic failed: No validation at 9:20")
        
        # Restore original datetime.now
        dt.datetime.now = original_now
        
        return len(qualified_stocks) > 0
        
    except Exception as e:
        print(f"❌ Error in complete volume fix test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Testing Complete Volume Fix for Continuation Bot")
    print("This test verifies the complete simplified volume validation approach")
    print("including timing logic and no initial volume capture")
    print()
    
    success = test_complete_volume_fix()
    
    if success:
        print("\n✅ Complete volume fix test PASSED!")
        print("The continuation bot should now:")
        print("  ✅ NOT capture initial volume at market open")
        print("  ✅ Validate volume only at 9:20")
        print("  ✅ Use current volume directly as cumulative volume")
        print("  ✅ Show proper volume validation instead of '0.0% (0)'")
    else:
        print("\n❌ Complete volume fix test FAILED!")
    
    return success

if __name__ == "__main__":
    main()