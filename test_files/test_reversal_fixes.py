#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify reversal bot fixes
Tests state machine initialization, entry logic, and state transitions
"""

import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def test_state_machine_initialization():
    """Test that state machine is properly initialized"""
    print("\n=== TESTING STATE MACHINE INITIALIZATION ===")
    
    try:
        from src.trading.live_trading.reversal_stock_monitor import ReversalStockState
        from src.trading.live_trading.reversal_modules.state_machine import StockState
        
        # Create a test stock
        stock = ReversalStockState("TEST", "TEST_KEY", 100.0, 'reversal_s2')
        
        # Check if state machine is properly initialized
        print(f"Stock symbol: {stock.symbol}")
        print(f"Stock state: {stock.state.value}")
        print(f"Stock is_subscribed: {stock.is_subscribed}")
        print(f"Stock is_active: {stock.is_active}")
        
        # Verify initial state
        assert stock.state.value == "initialized", f"Expected 'initialized', got {stock.state.value}"
        assert stock.is_subscribed == True, "Expected is_subscribed to be True"
        assert stock.is_active == True, "Expected is_active to be True"
        
        print("✅ State machine initialization test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ State machine initialization test FAILED: {e}")
        return False

def test_state_transitions():
    """Test state transitions"""
    print("\n=== TESTING STATE TRANSITIONS ===")
    
    try:
        from src.trading.live_trading.reversal_stock_monitor import ReversalStockState
        from src.trading.live_trading.reversal_modules.state_machine import StockState
        
        # Create a test stock
        stock = ReversalStockState("TEST", "TEST_KEY", 100.0, 'reversal_s2')
        
        # Test gap validation transition
        stock.open_price = 95.0  # Gap down
        stock.validate_gap()
        
        print(f"After gap validation: {stock.state.value}")
        assert stock.state.value == "gap_validated", f"Expected 'gap_validated', got {stock.state.value}"
        
        # Test low violation check transition
        stock.daily_low = 94.1  # No violation (1% of 95 = 0.95, so threshold is 94.05)
        stock.check_low_violation()
        
        print(f"After low violation check: {stock.state.value}")
        assert stock.state.value == "qualified", f"Expected 'qualified', got {stock.state.value}"
        
        # Test prepare entry transition
        stock.prepare_entry()
        
        print(f"After prepare entry: {stock.state.value}")
        assert stock.state.value == "selected", f"Expected 'selected', got {stock.state.value}"
        
        # Test entry transition
        stock.enter_position(96.0, datetime.now())
        
        print(f"After enter position: {stock.state.value}")
        assert stock.state.value == "entered", f"Expected 'entered', got {stock.state.value}"
        
        print("✅ State transitions test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ State transitions test FAILED: {e}")
        return False

def test_entry_logic():
    """Test entry logic for OOPS stocks"""
    print("\n=== TESTING ENTRY LOGIC ===")
    
    try:
        from src.trading.live_trading.reversal_stock_monitor import ReversalStockState
        from src.trading.live_trading.reversal_modules.state_machine import StockState
        
        # Create a test OOPS stock
        stock = ReversalStockState("TEST", "TEST_KEY", 100.0, 'reversal_s2')
        
        # Set up the stock for entry
        stock.open_price = 95.0  # Gap down
        stock.validate_gap()
        stock.daily_low = 94.0
        stock.check_low_violation()
        stock.prepare_entry()
        
        # Manually set state to monitoring_entry for testing
        stock._transition_to(StockState.MONITORING_ENTRY, "manual test")
        stock.entry_ready = True
        
        print(f"Stock state before entry: {stock.state.value}")
        print(f"Entry ready: {stock.entry_ready}")
        print(f"Previous close: {stock.previous_close}")
        
        # Test OOPS entry trigger
        test_price = 101.0  # Above previous close
        stock.enter_position(test_price, datetime.now())
        
        print(f"After entry: {stock.state.value}")
        print(f"Entered: {stock.entered}")
        print(f"Entry price: {stock.entry_price}")
        
        assert stock.state.value == "entered", f"Expected 'entered', got {stock.state.value}"
        assert stock.entered == True, "Expected entered to be True"
        assert stock.entry_price == test_price, f"Expected entry_price {test_price}, got {stock.entry_price}"
        
        print("✅ Entry logic test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Entry logic test FAILED: {e}")
        return False

def test_tick_processor():
    """Test tick processor state validation"""
    print("\n=== TESTING TICK PROCESSOR ===")
    
    try:
        from src.trading.live_trading.reversal_modules.tick_processor import ReversalTickProcessor
        from src.trading.live_trading.reversal_stock_monitor import ReversalStockState
        from src.trading.live_trading.reversal_modules.state_machine import StockState
        
        # Create a test stock
        stock = ReversalStockState("TEST", "TEST_KEY", 100.0, 'reversal_s2')
        stock.open_price = 95.0
        stock.validate_gap()
        stock.daily_low = 94.0
        stock.check_low_violation()
        stock.prepare_entry()
        stock._transition_to(StockState.MONITORING_ENTRY, "manual test")
        stock.entry_ready = True
        
        # Create tick processor
        tick_processor = ReversalTickProcessor(stock)
        
        # Test tick processing
        test_price = 101.0
        test_timestamp = datetime.now()
        
        print(f"Before tick processing:")
        print(f"  Stock state: {stock.state.value}")
        print(f"  Entry ready: {stock.entry_ready}")
        print(f"  Entered: {stock.entered}")
        
        # Process tick
        tick_processor.process_tick(test_price, test_timestamp)
        
        print(f"After tick processing:")
        print(f"  Stock state: {stock.state.value}")
        print(f"  Entered: {stock.entered}")
        print(f"  Entry price: {stock.entry_price}")
        
        assert stock.entered == True, "Expected stock to be entered after tick processing"
        assert stock.entry_price == test_price, f"Expected entry_price {test_price}, got {stock.entry_price}"
        
        print("✅ Tick processor test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Tick processor test FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("REVERSAL BOT FIX VERIFICATION TESTS")
    print("=" * 50)
    
    tests = [
        test_state_machine_initialization,
        test_state_transitions,
        test_entry_logic,
        test_tick_processor
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} FAILED with exception: {e}")
    
    print(f"\n{'=' * 50}")
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The reversal bot fixes are working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the fixes.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)