#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test for timing fix verification
"""

import sys
import os
from datetime import datetime, time, timedelta
import pytz

# Add src to path
sys.path.insert(0, 'src')

def test_entry_time_gate():
    """Test that entry time gates work correctly"""
    print("=== TESTING ENTRY TIME GATES ===")
    
    try:
        from src.trading.live_trading.config import ENTRY_TIME
        from src.trading.live_trading.continuation_stock_monitor import StockState
        from src.trading.live_trading.continuation_modules.tick_processor import ContinuationTickProcessor
        IST = pytz.timezone('Asia/Kolkata')
        
        print(f"ENTRY_TIME: {ENTRY_TIME}")
        
        # Create a test stock
        stock = StockState("TEST", "TEST_KEY", 100.0, 'continuation')
        processor = ContinuationTickProcessor(stock)
        
        # Test 1: Before entry time - should not set entry_ready
        print(f"\nTest 1: Before entry time")
        
        # Create a timestamp before entry time
        current_date = datetime.now(IST).date()
        before_time = time(11, 10, 0)  # Before 11:16:00
        test_timestamp = datetime.combine(current_date, before_time)
        
        print(f"Testing with timestamp: {test_timestamp.time()}")
        print(f"Entry time: {ENTRY_TIME}")
        print(f"Before entry time: {test_timestamp.time() < ENTRY_TIME}")
        
        # Simulate tick processing before entry time
        processor._track_entry_levels(105.0, test_timestamp)
        
        print(f"Entry ready after processing: {stock.entry_ready}")
        print(f"Entry time reached after processing: {stock.entry_time_reached}")
        
        if not stock.entry_ready and not stock.entry_time_reached:
            print("✓ Entry ready correctly NOT set before entry time")
        else:
            print("✗ Entry ready incorrectly set before entry time")
            return False
        
        # Test 2: After entry time - should set entry_ready
        print(f"\nTest 2: After entry time")
        
        # Reset stock state
        stock.entry_ready = False
        stock.entry_time_reached = False
        
        # Create a timestamp after entry time
        after_time = time(11, 20, 0)  # After 11:16:00
        test_timestamp = datetime.combine(current_date, after_time)
        
        print(f"Testing with timestamp: {test_timestamp.time()}")
        print(f"After entry time: {test_timestamp.time() >= ENTRY_TIME}")
        
        # Simulate tick processing after entry time
        processor._track_entry_levels(105.0, test_timestamp)
        
        print(f"Entry ready after processing: {stock.entry_ready}")
        print(f"Entry time reached after processing: {stock.entry_time_reached}")
        
        if stock.entry_ready and stock.entry_time_reached:
            print("✓ Entry ready correctly set after entry time")
        else:
            print("✗ Entry ready not set after entry time")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing entry time gates: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prepare_entry_timing():
    """Test prepare_entry method timing gate"""
    print("\n=== TESTING PREPARE_ENTRY TIMING ===")
    
    try:
        from src.trading.live_trading.continuation_stock_monitor import StockState
        from src.trading.live_trading.config import ENTRY_TIME
        IST = pytz.timezone('Asia/Kolkata')
        
        # Create test stock
        stock = StockState("TEST", "TEST_KEY", 100.0, 'continuation')
        
        # Test before entry time
        print(f"\nTest: Before entry time")
        current_date = datetime.now(IST).date()
        before_time = time(11, 10, 0)  # Before 11:16:00
        
        # Mock datetime.now to return before entry time
        import datetime as dt_module
        original_datetime = dt_module.datetime
        
        class MockDateTime:
            @staticmethod
            def now():
                return datetime.combine(current_date, before_time)
        
        dt_module.datetime = MockDateTime
        
        try:
            stock.prepare_entry()
            
            print(f"Entry ready after prepare_entry (before entry time): {stock.entry_ready}")
            print(f"Entry time reached after prepare_entry (before entry time): {stock.entry_time_reached}")
            
            if not stock.entry_ready and not stock.entry_time_reached:
                print("✓ prepare_entry correctly does not set entry_ready before entry time")
            else:
                print("✗ prepare_entry incorrectly sets entry_ready before entry time")
                return False
            
            # Test after entry time
            print(f"\nTest: After entry time")
            
            after_time = time(11, 20, 0)  # After 11:16:00
            
            class MockDateTimeAfter:
                @staticmethod
                def now():
                    return datetime.combine(current_date, after_time)
            
            dt_module.datetime = MockDateTimeAfter
            
            stock.entry_ready = False
            stock.entry_time_reached = False
            stock.prepare_entry()
            
            print(f"Entry ready after prepare_entry (after entry time): {stock.entry_ready}")
            print(f"Entry time reached after prepare_entry (after entry time): {stock.entry_time_reached}")
            
            if stock.entry_ready and stock.entry_time_reached:
                print("✓ prepare_entry correctly sets entry_ready after entry time")
            else:
                print("✗ prepare_entry does not set entry_ready after entry time")
                return False
                
        finally:
            # Restore original datetime
            dt_module.datetime = original_datetime
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing prepare_entry timing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run timing fix tests"""
    print("SIMPLE TIMING FIX VERIFICATION")
    print("=" * 40)
    
    success = True
    
    success &= test_entry_time_gate()
    success &= test_prepare_entry_timing()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ ALL TIMING FIX TESTS PASSED")
        print("The critical timing bypass issue has been fixed!")
    else:
        print("✗ SOME TIMING FIX TESTS FAILED")
        print("Please review the timing implementation.")
    
    return success

if __name__ == "__main__":
    main()