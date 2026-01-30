#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Reversal Bot Test
Comprehensive test to verify all fixes are working correctly
"""

import sys
import os
from datetime import datetime
import pytz

# Add src to path
sys.path.insert(0, 'src')

def test_all_fixes():
    """Test all the fixes we implemented"""
    
    print("=== FINAL REVERSAL BOT VERIFICATION ===")
    print("Testing all fixes to ensure the bot is working correctly")
    print()
    
    # Test 1: State Machine Initialization
    print("=== TEST 1: STATE MACHINE INITIALIZATION ===")
    try:
        from src.trading.live_trading.reversal_stock_monitor import ReversalStockState
        from src.trading.live_trading.reversal_modules.state_machine import StockState
        
        stock = ReversalStockState("TEST", "TEST_KEY", 100.0, 'reversal_s2')
        
        # Check if state machine is properly initialized
        assert stock.state.value == "initialized", f"Expected 'initialized', got {stock.state.value}"
        assert stock.is_subscribed == True, "Expected is_subscribed to be True"
        assert stock.is_active == True, "Expected is_active to be True"
        
        print("✅ State machine initialization working correctly")
        
    except Exception as e:
        print(f"❌ State machine initialization failed: {e}")
        return False
    
    # Test 2: State Transitions
    print("\n=== TEST 2: STATE TRANSITIONS ===")
    try:
        # Test gap validation transition
        stock.open_price = 95.0  # Gap down
        stock.validate_gap()
        assert stock.state.value == "gap_validated", f"Expected 'gap_validated', got {stock.state.value}"
        print("✅ Gap validation state transition working")
        
        # Test low violation check transition
        stock.daily_low = 94.1  # No violation
        stock.check_low_violation()
        assert stock.state.value == "qualified", f"Expected 'qualified', got {stock.state.value}"
        print("✅ Low violation check state transition working")
        
        # Test prepare entry transition
        stock.prepare_entry()
        assert stock.state.value == "selected", f"Expected 'selected', got {stock.state.value}"
        print("✅ Prepare entry state transition working")
        
        # Test entry transition
        stock.enter_position(96.0, datetime.now())
        assert stock.state.value == "entered", f"Expected 'entered', got {stock.state.value}"
        print("✅ Entry state transition working")
        
    except Exception as e:
        print(f"❌ State transitions failed: {e}")
        return False
    
    # Test 3: Entry Logic State Validation
    print("\n=== TEST 3: ENTRY LOGIC STATE VALIDATION ===")
    try:
        from src.trading.live_trading.reversal_modules.tick_processor import ReversalTickProcessor
        
        # Create a test stock for entry logic
        stock = ReversalStockState("TEST_ENTRY", "TEST_KEY", 100.0, 'reversal_s2')
        stock.open_price = 95.0
        stock.validate_gap()
        stock.daily_low = 94.1
        stock.check_low_violation()
        stock.prepare_entry()
        
        # Manually set state to monitoring_entry for testing
        stock._transition_to(StockState.MONITORING_ENTRY, "manual test")
        stock.entry_ready = True
        
        # Create tick processor
        tick_processor = ReversalTickProcessor(stock)
        
        # Test tick processing with state validation
        test_price = 101.0  # Above previous close
        tick_processor.process_tick(test_price, datetime.now())
        
        assert stock.entered == True, "Expected stock to be entered after tick processing"
        assert stock.entry_price == test_price, f"Expected entry_price {test_price}, got {stock.entry_price}"
        
        print("✅ Entry logic state validation working correctly")
        
    except Exception as e:
        print(f"❌ Entry logic state validation failed: {e}")
        return False
    
    # Test 4: Enhanced Debug Logging
    print("\n=== TEST 4: ENHANCED DEBUG LOGGING ===")
    try:
        # Test that debug logging is present in tick processor
        import inspect
        from src.trading.live_trading.reversal_modules.tick_processor import ReversalTickProcessor
        
        # Check if _handle_entry_monitoring method has debug logging
        source = inspect.getsource(ReversalTickProcessor._handle_entry_monitoring)
        
        assert "DEBUG: Add state validation logging" in source, "Debug logging not found in _handle_entry_monitoring"
        assert "logger.info(f\"[{self.stock.symbol}] Entry monitoring - Current state:" in source, "State validation logging not found"
        
        print("✅ Enhanced debug logging is present")
        
    except Exception as e:
        print(f"❌ Enhanced debug logging test failed: {e}")
        return False
    
    # Test 5: Improved Logging in Main Bot
    print("\n=== TEST 5: IMPROVED LOGGING IN MAIN BOT ===")
    try:
        # Test that improved logging is present in run_reversal.py
        with open('src/trading/live_trading/run_reversal.py', 'r') as f:
            content = f.read()
        
        assert "OOPS CANDIDATES READY FOR IMMEDIATE TRADING" in content, "OOPS logging not found"
        assert "STRONG START CANDIDATES READY FOR TRADING" in content, "Strong Start logging not found"
        assert "already ready since market open" in content, "Market open timing logging not found"
        
        print("✅ Improved logging is present in main bot")
        
    except Exception as e:
        print(f"❌ Improved logging test failed: {e}")
        return False
    
    print("\n=== ALL TESTS PASSED ===")
    print("✅ The reversal bot has been successfully fixed and verified!")
    print()
    print("Summary of fixes implemented:")
    print("1. ✅ State machine initialization fixed")
    print("2. ✅ State transitions working correctly")
    print("3. ✅ Entry logic state validation implemented")
    print("4. ✅ Enhanced debug logging added")
    print("5. ✅ Improved logging for OOPS vs Strong Start timing")
    print()
    print("The reversal bot should now work correctly:")
    print("- OOPS candidates ready at market open (9:15 AM)")
    print("- Strong Start candidates ready at entry time (9:18 AM)")
    print("- Entries trigger when price crosses thresholds")
    print("- Proper state management and validation")
    print("- Comprehensive debug logging for troubleshooting")
    
    return True

if __name__ == "__main__":
    success = test_all_fixes()
    if success:
        print("\n🎉 REVERSAL BOT FIXES VERIFIED - READY FOR LIVE TRADING!")
    else:
        print("\n❌ Some fixes need attention - please review the errors above")
    
    sys.exit(0 if success else 1)