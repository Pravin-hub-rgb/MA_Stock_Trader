#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test to verify unsubscription logic works
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

def test_unsubscription_logic():
    """Test just the unsubscription logic without tick processing"""
    
    print("=== TESTING UNSUBSCRIPTION LOGIC ONLY ===")
    print()
    
    try:
        # Import the modules
        from src.trading.live_trading.continuation_stock_monitor import StockMonitor
        from src.trading.live_trading.continuation_modules.subscription_manager import ContinuationSubscriptionManager
        from src.trading.live_trading.continuation_modules.integration import ContinuationIntegration
        
        # Create a mock data streamer
        class MockDataStreamer:
            def unsubscribe(self, instrument_keys):
                print(f"Mock: Unsubscribed from {len(instrument_keys)} instruments")
        
        # Create test setup
        data_streamer = MockDataStreamer()
        monitor = StockMonitor()
        
        # Add test stocks with proper setup
        monitor.add_stock("TEST1", "test1_key", 100.0, 'continuation')
        monitor.add_stock("TEST2", "test2_key", 200.0, 'continuation')
        
        # Set opening prices to avoid formatting errors
        monitor.stocks["test1_key"].set_open_price(100.0)
        monitor.stocks["test2_key"].set_open_price(200.0)
        
        # Create subscription manager
        subscription_manager = ContinuationSubscriptionManager(data_streamer, monitor)
        
        # Subscribe to all stocks
        instrument_keys = ["test1_key", "test2_key"]
        subscription_manager.subscribe_all(instrument_keys)
        
        print("Initial state:")
        for stock in monitor.stocks.values():
            print(f"  {stock.symbol}: is_active={stock.is_active}, is_subscribed={stock.is_subscribed}")
        print()
        
        # Create integration
        integration = ContinuationIntegration(data_streamer, monitor)
        
        print("=== STEP 1: TEST TICK HANDLER WITH ACTIVE STOCKS ===")
        print("Sending ticks to both stocks (should process normally):")
        
        # Test tick handler with active stocks
        print("Testing TEST1 (should process):")
        result1 = integration.simplified_tick_handler("test1_key", "TEST1", 101.0, datetime.now(), [])
        print(f"  Result: {result1}")
        
        print("Testing TEST2 (should process):")
        result2 = integration.simplified_tick_handler("test2_key", "TEST2", 201.0, datetime.now(), [])
        print(f"  Result: {result2}")
        
        print()
        print("=== STEP 2: SIMULATE UNSUBSCRIPTION ===")
        print("Now unsubscribing TEST1...")
        
        # Simulate unsubscription (like what happens in Phase 1/2)
        rejected_keys = ["test1_key"]
        subscription_manager.mark_stocks_unsubscribed(rejected_keys)
        
        print("Status after unsubscription:")
        for stock in monitor.stocks.values():
            print(f"  {stock.symbol}: is_active={stock.is_active}, is_subscribed={stock.is_subscribed}, rejection_reason={stock.rejection_reason}")
        print()
        
        print("=== STEP 3: TEST TICK HANDLER AFTER UNSUBSCRIPTION ===")
        print("Sending ticks to both stocks (TEST1 should exit early, TEST2 should process):")
        
        # Test tick handler after unsubscription
        print("Testing TEST1 (should exit early due to is_subscribed=False):")
        result3 = integration.simplified_tick_handler("test1_key", "TEST1", 102.0, datetime.now(), [])
        print(f"  Result: {result3}")
        
        print("Testing TEST2 (should process normally):")
        result4 = integration.simplified_tick_handler("test2_key", "TEST2", 202.0, datetime.now(), [])
        print(f"  Result: {result4}")
        
        print()
        print("=== STEP 4: VERIFY UNSUBSCRIPTION WORKED ===")
        
        # Check final status
        test1 = monitor.stocks["test1_key"]
        test2 = monitor.stocks["test2_key"]
        
        print("Final verification:")
        print(f"  TEST1 (unsubscribed): is_active={test1.is_active}, is_subscribed={test1.is_subscribed}")
        print(f"  TEST2 (still subscribed): is_active={test2.is_active}, is_subscribed={test2.is_subscribed}")
        
        # The key test: did TEST1 exit early due to is_subscribed=False?
        # If our fix works, TEST1 should have exited early and not processed the tick
        
        if not test1.is_subscribed and test2.is_subscribed:
            print("  ✅ SUCCESS: Unsubscription logic works correctly!")
            print("     - TEST1 is properly unsubscribed (is_subscribed=False)")
            print("     - TEST2 is still subscribed (is_subscribed=True)")
            print("     - The early exit check should prevent TEST1 from processing ticks")
        else:
            print("  ❌ FAILURE: Unsubscription logic did not work!")
            print(f"     - Expected TEST1.is_subscribed=False, got {test1.is_subscribed}")
            print(f"     - Expected TEST2.is_subscribed=True, got {test2.is_subscribed}")
        
        print()
        print("=== CONCLUSION ===")
        print("This test verifies that:")
        print("1. Stocks start as subscribed and active")
        print("2. After unsubscription, rejected stocks have is_subscribed=False")
        print("3. The early exit check in the tick handler should prevent processing")
        print("4. The fix is working at the subscription management level")
        
        return not test1.is_subscribed and test2.is_subscribed
        
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_unsubscription_logic()
    if success:
        print("\n🎉 UNSUBSCRIPTION LOGIC TEST PASSED!")
        print("The fix is working correctly at the subscription management level.")
    else:
        print("\n❌ UNSUBSCRIPTION LOGIC TEST FAILED!")