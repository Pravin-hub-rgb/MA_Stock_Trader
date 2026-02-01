#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test OOPS Entry Fix
Simple test to verify OOPS stocks now get entry price and entry_ready set correctly
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

def test_oops_entry_fix():
    """Test that OOPS stocks now get entry price and entry_ready set correctly"""
    
    print("=== TESTING OOPS ENTRY FIX ===")
    print("Verifying that OOPS stocks get entry price and entry_ready set when qualified")
    print()
    
    # Test 1: OOPS Stock Entry Price and Ready Fix
    print("=== TEST 1: OOPS STOCK ENTRY FIX ===")
    try:
        from src.trading.live_trading.reversal_stock_monitor import ReversalStockState
        from src.trading.live_trading.reversal_modules.state_machine import StockState
        
        # Create an OOPS stock
        stock = ReversalStockState("TEST_OOPS", "TEST_KEY", 100.0, 'reversal_s2')
        stock.open_price = 95.0  # Gap down setup
        
        print(f"Stock created: {stock.symbol} (OOPS)")
        print(f"Previous close: {stock.previous_close}")
        print(f"Open price: {stock.open_price}")
        print(f"Entry ready before: {stock.entry_ready}")
        print(f"Entry price before: {stock.entry_price}")
        
        # Validate gap (should set situation to reversal_s2)
        stock.validate_gap()
        print(f"Gap validated: {stock.gap_validated}")
        print(f"Situation after gap validation: {stock.situation}")
        
        # Check low violation (this should now set entry price and entry_ready for OOPS)
        stock.daily_low = 94.1  # No violation
        stock.check_low_violation()
        
        print(f"Low violation checked: {stock.low_violation_checked}")
        print(f"Entry ready after check_low_violation: {stock.entry_ready}")
        print(f"Entry price after check_low_violation: {stock.entry_price}")
        
        # Verify the fix worked
        assert stock.entry_ready == True, f"Expected entry_ready=True, got {stock.entry_ready}"
        assert stock.entry_price == stock.previous_close, f"Expected entry_price={stock.previous_close}, got {stock.entry_price}"
        
        print("✅ OOPS entry fix working correctly!")
        print(f"   Entry price set to: {stock.entry_price}")
        print(f"   Entry ready set to: {stock.entry_ready}")
        
    except Exception as e:
        print(f"❌ OOPS entry fix failed: {e}")
        return False
    
    # Test 2: Entry Signal Check
    print("\n=== TEST 2: ENTRY SIGNAL CHECK ===")
    try:
        # Test that entry signal works now
        test_price = 101.0  # Above previous close
        entry_signal = stock.check_entry_signal(test_price)
        
        print(f"Test price: {test_price}")
        print(f"Previous close: {stock.previous_close}")
        print(f"Entry signal triggered: {entry_signal}")
        
        assert entry_signal == True, f"Expected entry signal=True, got {entry_signal}"
        print("✅ Entry signal working correctly!")
        
    except Exception as e:
        print(f"❌ Entry signal test failed: {e}")
        return False
    
    # Test 3: Tick Processing
    print("\n=== TEST 3: TICK PROCESSING ===")
    try:
        from src.trading.live_trading.reversal_modules.tick_processor import ReversalTickProcessor
        from src.trading.live_trading.reversal_modules.state_machine import StockState
        
        # Create tick processor
        tick_processor = ReversalTickProcessor(stock)
        
        # Set stock to monitoring_entry state for entry testing
        stock._transition_to(StockState.MONITORING_ENTRY, "test setup")
        
        # Process a tick that should trigger entry
        test_price = 101.0
        tick_processor.process_tick(test_price, datetime.now())
        
        print(f"Tick processed: {test_price}")
        print(f"Stock entered: {stock.entered}")
        print(f"Entry price: {stock.entry_price}")
        
        assert stock.entered == True, f"Expected stock.entered=True, got {stock.entered}"
        assert stock.entry_price == test_price, f"Expected entry_price={test_price}, got {stock.entry_price}"
        
        print("✅ Tick processing working correctly!")
        
    except Exception as e:
        print(f"❌ Tick processing test failed: {e}")
        return False
    
    print("\n=== ALL OOPS ENTRY TESTS PASSED ===")
    print("✅ OOPS stocks now properly set entry price and entry_ready!")
    print("✅ OOPS stocks can now trigger entries when price crosses previous close!")
    print()
    print("The simple entry system is now working correctly:")
    print("- OOPS stocks get entry_price = previous_close when qualified")
    print("- OOPS stocks get entry_ready = True when qualified")
    print("- Entries trigger when price crosses entry_price")
    
    return True

if __name__ == "__main__":
    success = test_oops_entry_fix()
    if success:
        print("\n🎉 OOPS ENTRY FIX VERIFIED - SIMPLE ENTRY SYSTEM WORKING!")
    else:
        print("\n❌ OOPS entry fix needs attention")
    
    sys.exit(0 if success else 1)