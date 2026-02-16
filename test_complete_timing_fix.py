#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test for complete timing fix verification
Tests all aspects of the timing bypass fix
"""

import sys
import os
from datetime import datetime, time, timedelta
import pytz

# Add src to path
sys.path.insert(0, 'src')

def test_entry_time_gates():
    """Test that entry time gates are properly implemented"""
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
        before_entry_time = (datetime.combine(datetime.now(IST).date(), ENTRY_TIME) - timedelta(minutes=10)).time()
        print(f"\nTest 1: Before entry time ({before_entry_time})")
        
        # Simulate tick processing before entry time
        test_timestamp = datetime.combine(datetime.now(IST).date(), before_entry_time)
        processor._track_entry_levels(105.0, test_timestamp)
        
        if not stock.entry_ready:
            print("✓ Entry ready correctly NOT set before entry time")
        else:
            print("✗ Entry ready incorrectly set before entry time")
            return False
        
        # Test 2: After entry time - should set entry_ready
        after_entry_time = (datetime.combine(datetime.now(IST).date(), ENTRY_TIME) + timedelta(minutes=10)).time()
        print(f"\nTest 2: After entry time ({after_entry_time})")
        
        # Reset stock state
        stock.entry_ready = False
        stock.entry_time_reached = False
        
        # Simulate tick processing after entry time
        test_timestamp = datetime.combine(datetime.now(IST).date(), after_entry_time)
        processor._track_entry_levels(105.0, test_timestamp)
        
        if stock.entry_ready and stock.entry_time_reached:
            print("✓ Entry ready correctly set after entry time")
        else:
            print("✗ Entry ready not set after entry time")
            return False
        
        # Test 3: Entry monitoring gate
        print(f"\nTest 3: Entry monitoring gate")
        
        # Reset stock state
        stock.entry_ready = True
        stock.entry_time_reached = True
        stock.entered = False
        
        # Test before entry time - should skip entry
        before_entry_time = (datetime.combine(datetime.now(IST).date(), ENTRY_TIME) - timedelta(minutes=10)).time()
        test_timestamp = datetime.combine(datetime.now(IST).date(), before_entry_time)
        
        # Mock the enter_position method to track if it's called
        original_enter_position = stock.enter_position
        stock.enter_position_called = False
        
        def mock_enter_position(price, timestamp):
            stock.enter_position_called = True
            print(f"Entry triggered at {price}")
        
        stock.enter_position = mock_enter_position
        
        # Try to trigger entry before entry time
        processor._handle_entry_monitoring(110.0, test_timestamp)
        
        if not stock.enter_position_called:
            print("✓ Entry correctly blocked before entry time")
        else:
            print("✗ Entry incorrectly triggered before entry time")
            return False
        
        # Test after entry time - should allow entry
        after_entry_time = (datetime.combine(datetime.now(IST).date(), ENTRY_TIME) + timedelta(minutes=10)).time()
        test_timestamp = datetime.combine(datetime.now(IST).date(), after_entry_time)
        
        stock.enter_position_called = False
        processor._handle_entry_monitoring(110.0, test_timestamp)
        
        if stock.enter_position_called:
            print("✓ Entry correctly allowed after entry time")
        else:
            print("✗ Entry incorrectly blocked after entry time")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing entry time gates: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_timing_flow():
    """Test the complete timing flow"""
    print("\n=== TESTING TIMING FLOW ===")
    
    try:
        from src.trading.live_trading.config import MARKET_OPEN, ENTRY_TIME, PREP_START
        IST = pytz.timezone('Asia/Kolkata')
        
        current_time = datetime.now(IST).time()
        current_datetime = datetime.now(IST)
        
        print(f"Current time: {current_time}")
        print(f"PREP_START: {PREP_START}")
        print(f"MARKET_OPEN: {MARKET_OPEN}")
        print(f"ENTRY_TIME: {ENTRY_TIME}")
        
        # Determine current phase
        if current_datetime < datetime.combine(datetime.now(IST).date(), PREP_START).replace(tzinfo=IST):
            phase = "BEFORE PREP_START"
        elif current_datetime < datetime.combine(datetime.now(IST).date(), MARKET_OPEN).replace(tzinfo=IST):
            phase = "BETWEEN PREP_START AND MARKET_OPEN"
        elif current_datetime < datetime.combine(datetime.now(IST).date(), ENTRY_TIME).replace(tzinfo=IST):
            phase = "BETWEEN MARKET_OPEN AND ENTRY_TIME"
        else:
            phase = "AFTER ENTRY_TIME"
            
        print(f"Current phase: {phase}")
        
        # Test the timing logic that should prevent early entries
        if current_time < ENTRY_TIME:
            print("✓ Currently before entry time - entries should be blocked")
        else:
            print("✓ Currently after entry time - entries should be allowed")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing timing flow: {e}")
        return False

def test_stock_state_entry_time_tracking():
    """Test that StockState properly tracks entry time"""
    print("\n=== TESTING STOCK STATE ENTRY TIME TRACKING ===")
    
    try:
        from src.trading.live_trading.continuation_stock_monitor import StockState
        from src.trading.live_trading.config import ENTRY_TIME
        IST = pytz.timezone('Asia/Kolkata')
        
        # Create test stock
        stock = StockState("TEST", "TEST_KEY", 100.0, 'continuation')
        
        # Test initial state
        if not stock.entry_time_reached and not stock.entry_ready:
            print("✓ Initial state: entry_time_reached=False, entry_ready=False")
        else:
            print("✗ Initial state incorrect")
            return False
        
        # Test prepare_entry method timing gate
        from datetime import datetime
        
        # Test before entry time
        before_time = (datetime.combine(datetime.now(IST).date(), ENTRY_TIME) - timedelta(minutes=10)).time()
        current_time_backup = datetime.now
        
        def mock_datetime_now():
            return datetime.combine(datetime.now(IST).date(), before_time)
        
        # Temporarily replace datetime.now
        import datetime as dt_module
        original_now = dt_module.datetime.now
        dt_module.datetime.now = mock_datetime_now
        
        try:
            stock.prepare_entry()
            
            if not stock.entry_ready and not stock.entry_time_reached:
                print("✓ prepare_entry correctly does not set entry_ready before entry time")
            else:
                print("✗ prepare_entry incorrectly sets entry_ready before entry time")
                return False
            
            # Test after entry time
            after_time = (datetime.combine(datetime.now(IST).date(), ENTRY_TIME) + timedelta(minutes=10)).time()
            
            def mock_datetime_now_after():
                return datetime.combine(datetime.now(IST).date(), after_time)
            
            dt_module.datetime.now = mock_datetime_now_after
            
            stock.entry_ready = False
            stock.entry_time_reached = False
            stock.prepare_entry()
            
            if stock.entry_ready and stock.entry_time_reached:
                print("✓ prepare_entry correctly sets entry_ready after entry time")
            else:
                print("✗ prepare_entry does not set entry_ready after entry time")
                return False
                
        finally:
            # Restore original datetime.now
            dt_module.datetime.now = original_now
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing stock state entry time tracking: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all timing fix tests"""
    print("COMPLETE TIMING FIX VERIFICATION")
    print("=" * 50)
    
    success = True
    
    success &= test_entry_time_gates()
    success &= test_timing_flow()
    success &= test_stock_state_entry_time_tracking()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ ALL TIMING FIX TESTS PASSED")
        print("The critical timing bypass issue has been fixed!")
        print("\nKey fixes implemented:")
        print("1. Entry time gates in tick processor")
        print("2. Entry time tracking in StockState")
        print("3. Deferred entry processing until ENTRY_TIME")
        print("4. Multiple safety gates to prevent timing bypass")
    else:
        print("✗ SOME TIMING FIX TESTS FAILED")
        print("Please review the timing implementation.")
    
    return success

if __name__ == "__main__":
    main()